# -*- coding: utf-8 -*-
"""
Поиск реальных курсов на Stepik через публичный API каталога (search-results),
ранжирование по выборке отзывов (course-reviews, оценки 1–5) и числу студентов (courses).
Ссылки: https://stepik.org/course/<id>/promo
"""

from __future__ import annotations

import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

import requests

STEPIK_SEARCH_URL = "https://stepik.org/api/search-results"
STEPIK_COURSES_URL = "https://stepik.org/api/courses"
STEPIK_REVIEWS_URL = "https://stepik.org/api/course-reviews"
HEADERS = {
    "User-Agent": "site-project-learning-plan/1.0 (educational catalog; contact: local)",
    "Accept": "application/json",
}


def _truncate(q: str, max_len: int) -> str:
    q = " ".join(q.split())
    if len(q) <= max_len:
        return q
    cut = q[:max_len]
    if " " in cut:
        return cut.rsplit(" ", 1)[0]
    return cut


def week_primary_query(week: Dict[str, Any], max_len: int = 160) -> str:
    """Запрос для поиска курсов: навыки недели + тема (как в цели плана)."""
    chunks: List[str] = []
    seen: set = set()
    for s in week.get("skills") or []:
        t = str(s).strip()
        if not t:
            continue
        low = t.lower()
        if low in seen:
            continue
        seen.add(low)
        chunks.append(t)
    theme = (week.get("theme") or "").strip()
    if theme:
        tl = theme.lower()
        blob = " ".join(chunks).lower()
        if tl not in blob:
            chunks.append(theme)
    q = " ".join(chunks).strip()
    if not q:
        g = (week.get("goal") or "").strip()
        q = g if g else ""
    return _truncate(q, max_len)


def week_fallback_query(week: Dict[str, Any], max_len: int = 100) -> str:
    """Короткий запрос по формулировке цели — если по основному запросу мало курсов."""
    g = (week.get("goal") or "").strip()
    if not g:
        return ""
    g = re.sub(r"\s+", " ", g)
    return _truncate(g, max_len)


def _week_text_blob(week: Dict[str, Any]) -> str:
    parts = [
        " ".join(str(s) for s in (week.get("skills") or [])),
        str(week.get("theme") or ""),
        str(week.get("goal") or ""),
    ]
    return " ".join(parts).lower().replace("ё", "е")


def _text_has_cpp(t: str) -> bool:
    x = t.lower().replace("ё", "е")
    return (
        "c++" in x
        or re.search(r"\bcpp\b", x)
        or "с++" in x
        or "си ++" in x
        or "си плюс" in x
    )


def _text_has_python(t: str) -> bool:
    x = t.lower().replace("ё", "е")
    return "python" in x or "питон" in x or "django" in x or "flask" in x or "fastapi" in x


def _week_lang_signals(week: Dict[str, Any]) -> Dict[str, bool]:
    blob = _week_text_blob(week)
    return {
        "cpp": _text_has_cpp(blob),
        "python": _text_has_python(blob),
    }


def _title_mentions_cpp(title: str) -> bool:
    return _text_has_cpp(title.lower())


def _should_skip_course_title(title: str, signals: Dict[str, bool]) -> bool:
    """Отсекаем явно чужие курсы (напр. Python в неделе про C++)."""
    if not title:
        return False
    t = title.lower().replace("ё", "е")
    if signals.get("cpp") and not signals.get("python"):
        if ("python" in t or "питон" in t) and not _title_mentions_cpp(title):
            return True
    if signals.get("python") and not signals.get("cpp"):
        if _title_mentions_cpp(title) and "python" not in t and "питон" not in t:
            return True
    return False


def _queries_for_stepik(week: Dict[str, Any], signals: Dict[str, bool]) -> List[str]:
    """Несколько запросов: короткие токены вроде «C++» на Stepik дают в топе Python — добавляем уточнения."""
    seen: set = set()
    out: List[str] = []

    def add(q: str) -> None:
        q = _truncate(q.strip(), 170)
        if len(q) < 2:
            return
        k = q.casefold()
        if k in seen:
            return
        seen.add(k)
        out.append(q)

    base = week_primary_query(week)
    fb = week_fallback_query(week)

    if signals.get("cpp"):
        add("Программирование на языке C++")
        add("C++ для начинающих курс")
        if base and not _text_has_cpp(base):
            add(f"{base} C++")
        else:
            add(base)
        if fb and not _text_has_cpp(fb):
            add(_truncate(f"{fb} C++", 170))
        elif fb:
            add(fb)
        return out[:6]

    if signals.get("python"):
        add("Python программирование курс для начинающих")
        add(base)
        if fb:
            add(fb)
        return out[:6]

    add(base)
    if fb:
        add(fb)
    return out[:6]


def _fetch_search_rows(query: str, page_size: int, timeout: float) -> List[Dict[str, Any]]:
    q = (query or "").strip()
    if len(q) < 2:
        return []
    try:
        r = requests.get(
            STEPIK_SEARCH_URL,
            params={"query": q, "page_size": page_size},
            headers=HEADERS,
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json().get("search-results") or []
    except (requests.RequestException, ValueError, KeyError):
        return []


def search_courses(query: str, limit: int = 5, timeout: float = 14.0) -> List[Dict[str, Any]]:
    """
    Возвращает до `limit` курсов с реальными URL на stepik.org.
    При ошибке сети или пустом ответе — [].
    """
    rows = _fetch_search_rows(query, page_size=min(30, max(10, limit * 4)), timeout=timeout)
    out: List[Dict[str, Any]] = []
    seen: set = set()

    for row in rows:
        if row.get("target_type") != "course":
            continue
        cid = row.get("course") or row.get("target_id")
        if cid is None:
            continue
        try:
            cid_int = int(cid)
        except (TypeError, ValueError):
            continue
        if cid_int in seen:
            continue
        seen.add(cid_int)
        title = (row.get("course_title") or "").strip() or f"Курс #{cid_int}"
        out.append(
            {
                "title": f"{title} — Stepik",
                "url": f"https://stepik.org/course/{cid_int}/promo",
                "type": "course",
                "is_free": True,
                "source": "stepik_search",
            }
        )
        if len(out) >= limit:
            break

    return out


def _batch_fetch_course_meta(course_ids: List[int], timeout: float) -> Dict[int, Dict[str, Any]]:
    """learners_count и заголовок с /api/courses по списку id (батчами)."""
    out: Dict[int, Dict[str, Any]] = {}
    chunk_size = 20
    for i in range(0, len(course_ids), chunk_size):
        chunk = course_ids[i : i + chunk_size]
        params: List[Tuple[str, int]] = [("ids[]", cid) for cid in chunk]
        try:
            r = requests.get(STEPIK_COURSES_URL, params=params, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            for c in r.json().get("courses") or []:
                cid = int(c["id"])
                out[cid] = {
                    "learners_count": int(c.get("learners_count") or 0),
                    "api_title": (c.get("title") or "").strip(),
                }
        except (requests.RequestException, ValueError, KeyError, TypeError):
            continue
    return out


def _fetch_review_sample_avg(course_id: int, page_size: int, timeout: float) -> Tuple[Optional[float], int]:
    """Средняя оценка по первой странице отзывов Stepik (score 1–5)."""
    try:
        r = requests.get(
            STEPIK_REVIEWS_URL,
            params={"course": course_id, "page_size": page_size},
            headers=HEADERS,
            timeout=timeout,
        )
        r.raise_for_status()
        revs = r.json().get("course-reviews") or []
        if not revs:
            return None, 0
        scores = [int(x["score"]) for x in revs if x.get("score") is not None]
        if not scores:
            return None, 0
        return sum(scores) / len(scores), len(scores)
    except (requests.RequestException, ValueError, KeyError, TypeError, ZeroDivisionError):
        return None, 0


def _enrich_pool_with_reviews_and_learners(
    pool: List[Dict[str, Any]], review_page_size: int = 40, timeout: float = 10.0
) -> List[Dict[str, Any]]:
    ids = [int(x["course_id"]) for x in pool]
    meta = _batch_fetch_course_meta(ids, timeout=timeout)

    def enrich_one(item: Dict[str, Any]) -> Dict[str, Any]:
        cid = int(item["course_id"])
        m = meta.get(cid, {})
        avg, n = _fetch_review_sample_avg(cid, review_page_size, timeout=timeout)
        learners = int(m.get("learners_count") or 0)
        item["learners_count"] = learners
        item["rating_avg"] = round(avg, 2) if avg is not None else None
        item["rating_n"] = n
        # ранжирование: оценка * доверие к объёму отзывов * популярность курса
        if avg is None:
            item["_rank"] = math.log1p(learners) * 0.15
        else:
            item["_rank"] = avg * math.log1p(n + 1) * (1.0 + math.log1p(learners / 40000.0))
        return item

    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(enrich_one, dict(p)): p["course_id"] for p in pool}
        done: List[Dict[str, Any]] = []
        for fut in as_completed(futures):
            try:
                done.append(fut.result())
            except Exception:
                continue
    by_id = {int(x["course_id"]): x for x in done}
    return [by_id[int(p["course_id"])] for p in pool if int(p["course_id"]) in by_id]


def _finalize_course_item(item: Dict[str, Any]) -> Dict[str, Any]:
    title_plain = item.get("title_plain") or f"Курс #{item['course_id']}"
    ra = item.get("rating_avg")
    rn = item.get("rating_n") or 0
    lc = item.get("learners_count") or 0
    prefix = ""
    if ra is not None:
        prefix = f"⭐{ra:.1f}"
        if rn:
            prefix += f" ({rn} отз.)"
        prefix += " · "
    return {
        "title": f"{prefix}{title_plain} — Stepik",
        "url": f"https://stepik.org/course/{item['course_id']}/promo",
        "type": "course",
        "is_free": True,
        "source": "stepik_search",
        "rating_avg": item.get("rating_avg"),
        "rating_n": item.get("rating_n"),
        "learners_count": lc,
    }


def search_courses_for_week(
    week: Dict[str, Any],
    limit: int = 5,
    timeout: float = 12.0,
    pool_size: int = 18,
    preview_limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Подбор курсов с учётом темы недели, отсева «чужих» языков и ранжирования по отзывам Stepik
    (выборка оценок с API course-reviews) и числу студентов.

    preview_limit: если задан (например 10), вернуть столько лучших по рангу — для последующего отбора ИИ.
    Иначе вернуть `limit` записей.
    """
    pool_size = max(pool_size, limit * 2, 12)
    signals = _week_lang_signals(week)
    queries = _queries_for_stepik(week, signals)
    pool: List[Dict[str, Any]] = []
    seen_ids: set = set()

    for q in queries:
        if len(pool) >= pool_size:
            break
        rows = _fetch_search_rows(q, page_size=40, timeout=timeout)
        for row in rows:
            if len(pool) >= pool_size:
                break
            if row.get("target_type") != "course":
                continue
            cid = row.get("course") or row.get("target_id")
            if cid is None:
                continue
            try:
                cid_int = int(cid)
            except (TypeError, ValueError):
                continue
            if cid_int in seen_ids:
                continue
            title_raw = (row.get("course_title") or "").strip()
            if _should_skip_course_title(title_raw, signals):
                continue
            seen_ids.add(cid_int)
            pool.append(
                {
                    "course_id": cid_int,
                    "title_plain": title_raw or f"Курс #{cid_int}",
                }
            )

    if not pool:
        return []

    enriched = _enrich_pool_with_reviews_and_learners(pool, review_page_size=40, timeout=timeout)
    enriched.sort(key=lambda x: float(x.get("_rank") or 0), reverse=True)
    out_n = preview_limit if preview_limit is not None else limit
    out_n = min(max(out_n, 1), len(enriched))
    return [_finalize_course_item(x) for x in enriched[:out_n]]
