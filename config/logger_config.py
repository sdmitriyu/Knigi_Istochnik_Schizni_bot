import logging
import traceback
import os
from datetime import datetime

# Создаем директорию для логов, если её нет
if not os.path.exists('logs'):
    os.makedirs('logs')

# Настройка логирования
def setup_logger(name: str) -> logging.Logger:
    """Настройка логгера для модуля"""
    logger = logging.getLogger(name)
    
    # Если логгер уже настроен, возвращаем его
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
        'File: %(pathname)s:%(lineno)d\n'
        'Function: %(funcName)s\n'
        'Traceback: %(exc_info)s'
    )
    
    # Хендлер для файла
    current_date = datetime.now().strftime('%Y-%m-%d')
    file_handler = logging.FileHandler(
        f'logs/{name}_{current_date}.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Хендлер для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    # Добавляем хендлеры к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_error(logger: logging.Logger, error: Exception, context: str = None):
    """Логирование ошибки с контекстом"""
    error_msg = f"Ошибка: {str(error)}"
    if context:
        error_msg = f"{context} - {error_msg}"
    
    logger.error(error_msg)
    logger.error(f"Traceback:\n{traceback.format_exc()}")

def log_debug(logger: logging.Logger, message: str, data: dict = None):
    """Логирование отладочной информации"""
    if data:
        logger.debug(f"{message} - Данные: {data}")
    else:
        logger.debug(message)

def log_info(logger: logging.Logger, message: str, data: dict = None):
    """Логирование информационных сообщений"""
    if data:
        logger.info(f"{message} - Данные: {data}")
    else:
        logger.info(message)

def log_warning(logger: logging.Logger, message: str, data: dict = None):
    """Логирование предупреждений"""
    if data:
        logger.warning(f"{message} - Данные: {data}")
    else:
        logger.warning(message) 