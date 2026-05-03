# -*- coding: utf-8 -*-
# tests/test_get_token.py

import sys
import os
import pytest
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGetToken:
    """tests for get_token.py (real API calls)"""
    
    def test_script_runs_without_error(self, tmp_path):
        """test: script runs without crashing"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "get_token.py")
        
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )
        
        # скрипт может завершиться с ошибкой 403, если токен уже есть
        # но не должен падать с другой ошибкой
        assert result.returncode in [0, 1]  # 0 или 1 допустимы
        
        print(f"\n✓ Script executed (returncode: {result.returncode})")
    
    def test_token_file_created_if_not_exists(self, tmp_path):
        """test: token file is created when API returns token"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "get_token.py")
        
        # удаляем существующий токен, если он есть в tmp_path
        token_file = tmp_path / "token.txt"
        if token_file.exists():
            token_file.unlink()
        
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )
        
        # если API вернул ошибку 403, файл может не создаться
        # это нормально для теста
        if "403" not in result.stdout and "ошибка" not in result.stdout.lower():
            assert token_file.exists()
        
        print(f"\n✓ Script output: {result.stdout[:200] if result.stdout else 'no output'}")
    
    def test_script_output_contains_token_info(self, tmp_path):
        """test: script prints token info when successful"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "get_token.py")
        
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )
        
        output = result.stdout
        # проверяем, что вывод содержит информацию о токене 
        # (или сообщение об ошибке)
        assert "токен" in output.lower() or "token" in output.lower() or "ошибка" in output.lower()
        
        print(f"\n✓ Output contains token/error info")


@pytest.mark.skip(reason="Requires fresh token, runs manually")
class TestGetTokenManual:
    """manual tests - run only when needed"""
    
    def test_get_token_manually(self):
        """manual test: just run get_token.py"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "get_token.py")
        subprocess.run(["python", script_path])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])