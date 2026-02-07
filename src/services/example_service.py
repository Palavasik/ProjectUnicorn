"""
Пример сервиса для бизнес-логики.
Здесь размещается логика, не связанная напрямую с Telegram API.
"""


class ExampleService:
    """Пример сервиса для демонстрации структуры."""
    
    @staticmethod
    def process_data(data: str) -> str:
        """
        Пример обработки данных.
        
        Args:
            data: Входные данные
            
        Returns:
            Обработанные данные
        """
        # Здесь ваша бизнес-логика
        return f"Processed: {data}"
