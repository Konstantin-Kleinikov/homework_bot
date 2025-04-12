"""Модуль логики бот-ассистента по проверке домашних заданий в Я.Практикум."""
import logging
import sys
import time
from datetime import datetime, timedelta
from http import HTTPStatus

import requests
from telebot import TeleBot

from constants import (ENDPOINT, HEADERS, HOMEWORK_NAME_KEY, HOMEWORK_VERDICTS,
                       HOMEWORKS_KEY, NUM_DAYS_AGO, PRACTICUM_TOKEN,
                       RETRY_PERIOD, STATUS_KEY, TELEGRAM_CHAT_ID,
                       TELEGRAM_TOKEN)
from exeptions import (EndpointNotAvailable, HomeworkNameNotFound,
                       HomeworkNotFound, HomeworkResponseEmpty,
                       HomeworkStatusNotFound, UnexpectedHomeworkStatus)


def check_tokens() -> bool:
    """Проверка присутствия и заполнения переменных окружения."""
    env_variables = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for name, value in env_variables.items():
        if not value:
            logging.critical(f'Переменная окружения {name} не установлена.')
            raise ValueError(f'Переменная окружения {name} не установлена.')
    return True


def send_message(bot, message):
    """Отправляет сообщение телеграм боту."""
    result = bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.debug('Успешно отправлено сообщение: '
                  f'{message} на id чата {TELEGRAM_CHAT_ID}.')
    return result


def get_api_answer(timestamp: int):
    """Обращается с запросом к API сервиса Практикум.Домашка."""
    payload = {'from_date': timestamp}
    try:
        api_response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
        if api_response.status_code != HTTPStatus.OK:
            raise EndpointNotAvailable(
                f'Ошибка при запросе к API: {api_response.status_code} '
                f'{api_response.reason}. '
                f'Проверьте корректность ENDPOINT ({ENDPOINT}) '
                'и параметры запроса.'
            )
        return api_response.json()
    except requests.exceptions.RequestException as error:
        raise EndpointNotAvailable(
            f'Ошибка при запросе к API: {error}'
        ) from error


def check_response(response):
    """Проверяет содержимое ответа от API сервиса Практикум.Домашка."""
    if not isinstance(response, dict):
        raise TypeError(
            f'Ожидался словарь в ответе от {ENDPOINT}, '
            f'но получен объект типа {type(response).__name__}.'
        )
    homeworks = response.get(HOMEWORKS_KEY)
    if not homeworks:
        raise HomeworkNotFound(
            f'Не найден ключ {HOMEWORKS_KEY} в ответе от ({ENDPOINT})!'
        )
    if not isinstance(homeworks, list):
        raise TypeError(
            f'Ожидался список в ключе {HOMEWORKS_KEY}, '
            f'но получен объект типа {type(homeworks).__name__}.'
        )
    if not homeworks[0]:
        raise HomeworkResponseEmpty(
            f'В ответе от ({ENDPOINT}) содержимое ключа'
            f'{HOMEWORKS_KEY} не найдено!'
        )
    return homeworks[0]


def parse_status(homework):
    """Анализирует статус проверки домашнего задания."""
    status = homework.get(STATUS_KEY)
    if not status:
        raise HomeworkStatusNotFound('Статус проверки задания не изменился.')
    if status not in HOMEWORK_VERDICTS:
        raise UnexpectedHomeworkStatus(
            f'В ответе от ({ENDPOINT}) получен статус '
            f'{status},'
            'который не может быть обработан!'
        )
    homework_name = homework.get(HOMEWORK_NAME_KEY)
    if not homework_name:
        raise HomeworkNameNotFound(
            f'Не найдено содержимое ключа {HOMEWORK_NAME_KEY}!'
        )
    homework_name = homework.get(HOMEWORK_NAME_KEY)
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def get_timestamp(days_ago: int) -> int:
    """Вычисляет значение Unix-время в прошлом."""
    date_in_past = datetime.now() - timedelta(days=days_ago)
    starting_from = int(time.mktime(date_in_past.timetuple()))
    return starting_from


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    if check_tokens():
        starting_from = get_timestamp(NUM_DAYS_AGO)
        bot = TeleBot(token=TELEGRAM_TOKEN)
        sent_errors = set()
        while True:
            try:
                cleaned_response = get_api_answer(starting_from)
                homework = check_response(cleaned_response)
                status_message = parse_status(homework)
                send_message(bot, status_message)
                sent_errors.clear()
            except (EndpointNotAvailable, HomeworkNotFound,
                    HomeworkResponseEmpty, UnexpectedHomeworkStatus,
                    HomeworkNameNotFound) as error:
                if str(error) not in sent_errors:
                    send_message(bot, error)
                    sent_errors.add(str(error))
                logging.error(error)
            except Exception as error:
                logging.error(f'Сбой в работе программы: {error}')
            finally:
                time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
