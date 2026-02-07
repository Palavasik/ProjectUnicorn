# Makefile для удобства разработки

.PHONY: help install run test clean format lint

help:
	@echo "Доступные команды:"
	@echo "  make install  - Установить зависимости"
	@echo "  make run      - Запустить бота"
	@echo "  make test     - Запустить тесты"
	@echo "  make format   - Форматировать код (black)"
	@echo "  make lint     - Проверить код (flake8)"
	@echo "  make clean    - Очистить временные файлы"

install:
	pip install -r requirements.txt

run:
	python src/main.py

test:
	pytest

format:
	black src/ tests/

lint:
	flake8 src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
