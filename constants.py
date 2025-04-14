"""Константы приложения homework_bot"""
import os

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600  # в секундах
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

NUM_DAYS_AGO = 2  # в днях

HOMEWORKS_KEY = 'homeworks'
HOMEWORK_NAME_KEY = 'homework_name'
STATUS_KEY = 'status'
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

ENV_VARIABLE_NOT_FOUND_ERROR = (
    'Обязательная переменная окружения {name} не установлена. '
    'Программа принудительно остановлена!'
)

ENDPOINT_NOT_AVAILABLE_ERROR = (
    'Ошибка {status_code} ({reason}) при запросе к API. '
    'Проверьте корректность ENDPOINT ({endpoint}) '
    'и параметры запроса.'
)

PROGRAM_ERROR = 'Сбой в работе программы: {error}'

HOMEWORK_STATUS_NOT_CHANGED = 'Статус проверки задания не изменился.'
