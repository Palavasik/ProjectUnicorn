"""
Вспомогательные функции и утилиты.
"""

from typing import Any, Dict


def format_message(text: str, **kwargs: Any) -> str:
    """
    Форматирование сообщения с подстановкой переменных.
    
    Args:
        text: Текст шаблона
        **kwargs: Переменные для подстановки
        
    Returns:
        Отформатированное сообщение
    """
    return text.format(**kwargs)


def validate_input(data: Dict[str, Any], required_fields: list) -> bool:
    """
    Валидация входных данных.
    
    Args:
        data: Словарь с данными
        required_fields: Список обязательных полей
        
    Returns:
        True если все поля присутствуют, False иначе
    """
    return all(field in data for field in required_fields)
