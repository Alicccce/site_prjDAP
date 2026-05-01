# Система анализа вакансий с AI

**Курсовая работа по анализу данных**
*Автор: студентка 2 курса*

Моя система анализирует вакансии с hh.ru, извлекает навыки и сравнивает их с навыками пользователя. Полный цикл: запрос → hh.ru → анализ → результат.

## � Что умеет система

### Основные функции:

1. **Анализ вакансий**
   - Получает вакансии с hh.ru по поисковому запросу
   - Находит навыки в описаниях вакансий
   - Определяет важность навыков (обязательные/рекомендуемые/желательные)

2. **Сравнение навыков**
   - Считает процент совпадения навыков пользователя с требованиями
   - Учитывает важность разных навыков
   - Показывает каких навыков не хватает

3. **Кэширование**
   - Сохраняет результаты на 1 час
   - Ускоряет повторные запросы

4. **Статистика**
   - Время обработки запросов
   - Количество найденных навыков
   - Производительность системы

## 🏗️ Архитектура проекта

```
Пользователь → VacancyAnalysisService → hh.ru API
                ↓
         AIAssistant (анализ и сравнение)
                ↓
         Models (хранение данных)
```

## � Структура проекта

```
site-project/
├── models.py                    # Модели данных
├── vacancy_analysis_service.py  # Основной сервис анализа
├── ai_assistant.py             # AI-ассистент
├── main.py                     # CLI приложение
├── test_integration.py         # Тесты
├── demo.py                     # Демонстрация
├── simple_test.py              # Простой тест
├── hh_parser/                  # Парсер hh.ru
│   ├── parse_vacancies.py      # Получение вакансий
│   └── analyze_skills.py       # Базовый анализ
└── README.md                   # Документация
```

## 🚀 Как использовать

### Установка
```bash
pip install requests
```

### Запуск
```bash
# Анализ должности
python main.py --position "Data Scientist"

# Сравнение навыков
python main.py --skills "Python,SQL" --positions "Data Scientist,Python Developer"

# Тесты
python main.py --test

# Демонстрация
python demo.py
```

## 🎯 Как работает алгоритм

### Формула расчета совпадения:
```
Общий процент = (обязательные * 0.7) + (рекомендуемые * 0.2) + (желательные * 0.1)
```

### Уровни важности навыков:
- **Обязательные**: встречаются в 70%+ вакансий
- **Рекомендуемые**: 40-70% вакансий  
- **Желательные**: меньше 40% вакансий

## 📊 Пример работы

```
Пользовательские навыки: Python, SQL, Docker

Data Scientist: 50% совпадения
✅ Совпали: Python, SQL, Docker
❌ Не хватает: Machine Learning (обязательный)

Python Developer: 75% совпадения  
✅ Совпали: Python, Docker
⚠️ Не хватает: Django, PostgreSQL
```

## 🧪 Тестирование

Запуск всех тестов:
```bash
python main.py --test
```

Тесты проверяют:
- AI-анализ вакансий
- Сравнение навыков
- Кэширование
- Метрики
- Обработку ошибок

## 📈 Что я узнала при разработке

### Технические навыки:
- Работа с API hh.ru
- Обработка и анализ текстовых данных
- Разработка архитектуры с кэшированием
- Написание тестов и метрик

### Аналитические навыки:
- Алгоритмы сравнения навыков
- Статистический анализ рынка труда
- Оптимизация производительности

## 🔧 Ограничения и планы

### Что можно улучшить:
1. **База данных** - сейчас все хранится в памяти
2. **Больше навыков** - расширить словарь технологий
3. **Web интерфейс** - сделать веб-версию
4. **Другие регионы** - добавить анализ по городам

### Текущие ограничения:
- Максимум 50 вакансий за раз
- Только hh.ru (можно добавить другие сайты)
- Простой словарь навыков

---

**Курсовая работа выполнена!** 🎓  
*Готова к демонстрации и дальнейшему развитию*

## 📁 Структура проекта

```
site-project/
├── models.py                    # Модели данных
├── vacancy_analysis_service.py  # Основной сервис анализа
├── ai_assistant.py             # AI-ассистент
├── main.py                     # CLI приложение
├── test_integration.py         # Интеграционные тесты
├── hh_parser/                  # Парсер hh.ru
│   ├── parse_vacancies.py      # Получение вакансий
│   └── analyze_skills.py       # Базовый анализ навыков
└── README.md                   # Документация
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install requests
```

### 2. Получение токена hh.ru (опционально)

Создайте файл `token.txt` в корне проекта с токеном от hh.ru API для увеличения лимитов запросов.

### 3. Запуск анализа

```bash
# Анализ конкретной должности
python main.py --position "Data Scientist"

# Сравнение навыков пользователя с должностями
python main.py --skills "Python,SQL,Machine Learning" --positions "Data Scientist,Python Developer"

# Запуск с рекомендациями
python main.py --skills "Python" --positions "Data Scientist" --recommendations

# Просмотр метрик производительности
python main.py --metrics

# Запуск тестов
python main.py --test
```

## 📊 Пример использования

### Анализ должности

```python
from vacancy_analysis_service import VacancyAnalysisService

service = VacancyAnalysisService()
result = service.analyze_position("Data Scientist")

print(f"Найдено навыков: {len(result.skills)}")
for skill in result.skills[:5]:
    print(f"- {skill.name}: {skill.frequency}% ({skill.importance.value})")
```

### Сравнение навыков

```python
from ai_assistant import AIAssistant
from models import SkillsPosition, Skill, SkillImportance

ai = AIAssistant()

# Создаем анализируемые должности
job_analyses = [
    SkillsPosition(
        position_name="Data Scientist",
        skills=[
            Skill("Python", SkillImportance.MANDATORY, 80),
            Skill("Machine Learning", SkillImportance.MANDATORY, 60),
            Skill("SQL", SkillImportance.RECOMMENDED, 70)
        ]
    )
]

# Сравниваем с навыками пользователя
user_skills = ["Python", "SQL", "Machine Learning"]
matches = ai.matchUserSkillsWithJobs(user_skills, job_analyses)

for match in matches:
    print(f"{match.job_title}: {match.match_percentage}% совпадения")
```

## 🎯 Алгоритм расчета совпадения навыков

### Формула расчета

```
Общий процент = (процент_обязательных * 0.7) + (процент_рекомендуемых * 0.2) + (процент_желательных * 0.1)
```

### Классификация навыков по частоте

- **🔥 Обязательные (mandatory)**: ≥ 70% вакансий
- **⭐ Рекомендуемые (recommended)**: 40-70% вакансий  
- **💡 Желательные (optional)**: < 40% вакансий

### Пример расчета

Пользовательские навыки: `["Python", "SQL"]`

Требования Data Scientist:
- Обязательные: Python, Machine Learning (2 навыка)
- Рекомендуемые: SQL, Statistics (2 навыка)
- Желательные: Docker, Git (2 навыка)

Расчет:
- Обязательные: 1/2 = 50% → 50% × 0.7 = 35%
- Рекомендуемые: 1/2 = 50% → 50% × 0.2 = 10%
- Желательные: 0/2 = 0% → 0% × 0.1 = 0%

**Итоговый процент: 35% + 10% + 0% = 45%**

## 📈 Метрики и производительность

Система автоматически собирает следующие метрики:

- **hh_parsing_time_ms**: время запроса к hh.ru API
- **ai_analysis_time_ms**: время AI-анализа вакансий
- **total_time_ms**: общее время обработки
- **vacancies_found**: количество найденных вакансий
- **vacancies_analyzed**: количество обработанных вакансий (ограничено max_vacancies)
- **skills_extracted**: количество извлеченных навыков

### Ограничения

- **max_vacancies**: 50 (можно изменить в конструкторе)
- **cache_duration**: 1 час (можно изменить)
- **hh.ru API лимиты**: 100 вакансий на запрос

## 🧪 Тестирование

### Запуск всех тестов

```bash
python main.py --test
```

### Структура тестов

1. **AI-анализ вакансий** - проверка извлечения навыков
2. **Сервис анализа** - интеграция с hh.ru
3. **Сравнение навыков** - расчет процентов совпадения
4. **Кэширование** - работа механизма кэша
5. **Метрики** - сбор статистики
6. **Рекомендации** - генерация советов по развитию
7. **Edge cases** - обработка ошибок

### Тестовые данные

Тесты используют сохраненные JSON-данные с hh.ru для стабильности и отсутствия зависимости от внешних API.

## 🔧 Конфигурация

### Параметры VacancyAnalysisService

```python
service = VacancyAnalysisService(
    cache_duration_hours=1,  # Длительность кэша в часах
    max_vacancies=50         # Максимум вакансий для анализа
)
```

### Настройка логирования

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 📝 API Reference

### VacancyAnalysisService

#### `analyze_position(search_query: str, area: int = 1) -> SkillsPosition`

Анализ должности и извлечение навыков.

**Параметры:**
- `search_query`: поисковый запрос (например, "Data Scientist")
- `area`: ID региона (1 - Москва, 2 - Санкт-Петербург)

**Возвращает:** `SkillsPosition` с анализированными навыками

### AIAssistant

#### `analyzeVacancies(vacancies_data: List[Dict]) -> Dict`

Анализ вакансий с использованием AI.

**Параметры:**
- `vacancies_data`: список вакансий от hh.ru API

**Возвращает:** словарь с навыками и статистикой

#### `matchUserSkillsWithJobs(user_skills: List[str], job_analyses: List[SkillsPosition]) -> List[JobMatch]`

Сравнение навыков пользователя с требованиями должностей.

**Параметры:**
- `user_skills`: навыки пользователя
- `job_analyses`: проанализированные должности

**Возвращает:** список совпадений, отсортированный по проценту

## 🚨 Обработка ошибок

### Типы ошибок

1. **hh.ru API ошибки**
   - Network timeouts
   - Rate limiting
   - Invalid tokens

2. **AI ошибки анализа**
   - Empty vacancy data
   - Memory issues с большими JSON
   - Skill extraction failures

3. **Ошибки сравнения**
   - Empty user skills
   - Empty job analyses
   - Invalid skill formats

### Логирование ошибок

Все ошибки логируются с детальной информацией для отладки. AI-ошибки отдельно логируются для улучшения алгоритма.

## 🔄 Workflow

### Полный цикл обработки

1. **Запрос пользователя** → VacancyAnalysisService
2. **Проверка кэша** → Если есть свежий результат, вернуть его
3. **Запрос к hh.ru** → fetch_vacancies()
4. **AI-анализ** → AIAssistant.analyzeVacancies()
5. **Сохранение в кэш** → cache_result()
6. **Сбор метрик** → AnalysisMetrics
7. **Возврат результата** → SkillsPosition

### Пример workflow

```python
# 1. Пользователь запрашивает анализ
service = VacancyAnalysisService()
result = service.analyze_position("Python Developer")

# 2. Система проверяет кэш
cached = service._get_from_cache("Python Developer")

# 3. Если кэша нет, запрос к hh.ru
vacancies = fetch_vacancies("Python Developer")

# 4. AI-анализ полученных данных
ai_result = ai_assistant.analyzeVacancies(vacancies['items'])

# 5. Сохранение в кэш и метрики
service._cache_result("Python Developer", result)
service.metrics.append(metric)
```

## 📋 TODO и улучшения

### Планируемые улучшения

1. **База данных** - интеграция с PostgreSQL/MongoDB
2. **Web интерфейс** - REST API и фронтенд
3. **Расширенный AI** - интеграция с GPT/другими AI моделями
4. **Регионирование** - анализ по разным городам
5. **Исторические данные** - тренды навыков во времени
6. **Экспорт** - CSV/Excel отчеты
7. **Уведомления** - новые вакансии по навыкам пользователя

### Ограничения текущей версии

- Только hh.ru API
- Ограниченный словарь навыков
- Простая кэш-система в памяти
- CLI интерфейс только

## 📞 Поддержка

Для вопросов и предложений:
- Создайте issue в репозитории
- Проверьте тесты: `python main.py --test`
- Изучите метрики: `python main.py --metrics`

---

**Версия:** 1.0.0  
**Автор:** AI Assistant  
**Лицензия:** MIT
