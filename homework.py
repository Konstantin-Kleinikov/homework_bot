"""Модуль логики бот-ассистента по проверке домашних заданий в Я.Практикум."""
import logging
import sys
import time
from datetime import datetime, timedelta
from http import HTTPStatus

import requests
import telebot
from telebot import TeleBot

from constants import (ENDPOINT, ENDPOINT_NOT_AVAILABLE_ERROR,
                       ENV_VARIABLE_NOT_FOUND_ERROR, HEADERS,
                       HOMEWORK_NAME_KEY, HOMEWORK_STATUS_NOT_CHANGED,
                       HOMEWORK_VERDICT_WAS_CHANGED, HOMEWORK_VERDICTS,
                       HOMEWORKS_KEY, NUM_DAYS_AGO, PRACTICUM_TOKEN,
                       PROGRAM_ERROR, RETRY_PERIOD, STATUS_KEY,
                       TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)
from exeptions import (EndpointNotAvailableError, EnvVariableNotFoundError,
                       HomeworkNameNotFoundError, HomeworkNotFoundError,
                       HomeworkStatusNotFoundError,
                       UnexpectedHomeworkStatusError)


def check_tokens():
    """Проверка присутствия и заполнения переменных окружения."""
    env_variables = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    errors = []
    for name, value in env_variables.items():
        if not value:
            error_message = ENV_VARIABLE_NOT_FOUND_ERROR.format(name=name)
            logging.critical(error_message)
            errors.append(error_message)
    if errors:
        raise EnvVariableNotFoundError('\n'.join(errors))


def send_message(bot, message) -> bool:
    """Отправляет сообщение телеграм боту."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Успешно отправлено сообщение: '
                      f'{message} на id чата {TELEGRAM_CHAT_ID}.')
        return True
    except (
            requests.exceptions.RequestException,
            telebot.apihelper.ApiException,
    ) as error:
        logging.error(f'Ошибка при отправке сообщения телеграмм боту: {error}')
        return False


def get_api_answer(timestamp: int):
    """Обращается с запросом к API сервису Практикум.Домашка."""
    payload = {'from_date': timestamp}
    request_details = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': payload
    }
    try:
        logging.info(
            'Начало запроса к API: {url}, '
            'заголовки: {headers}, параметры: {params}'
            .format(**request_details)
        )
        api_response = requests.get(**request_details)
    except requests.exceptions.RequestException as error:
        logging.error(
            f'Ошибка при обращении к API сервису Практикум.Домашка: {error}'
        )
        raise EndpointNotAvailableError(
            f'Ошибка при обращении к API: {error}'
        ) from error

    if api_response.status_code != HTTPStatus.OK:
        raise EndpointNotAvailableError(
            ENDPOINT_NOT_AVAILABLE_ERROR.format(
                status_code=api_response.status_code,
                reason=api_response.reason,
                endpoint=ENDPOINT,
            )
        )
    logging.info(f'Получен ответ от API: {api_response},'
                 '{url}, {headers}, {params}'.format(**request_details))
    return api_response.json()


def check_response(response):
    """Проверяет содержимое ответа от API сервиса Практикум.Домашка."""
    if not isinstance(response, dict):
        raise TypeError(
            f'Ожидался словарь в ответе от {ENDPOINT}, '
            f'но получен объект типа {type(response).__name__}.'
        )
    homeworks = response.get(HOMEWORKS_KEY)
    if HOMEWORKS_KEY not in response:
        raise HomeworkNotFoundError(
            f'Не найден ключ {HOMEWORKS_KEY} в ответе от ({ENDPOINT})!'
        )
    if not isinstance(homeworks, list):
        raise TypeError(
            f'Ожидался список в ключе {HOMEWORKS_KEY}, '
            f'но получен объект типа {type(homeworks).__name__}.'
        )
    return homeworks


def parse_status(homework):
    """Анализирует статус проверки домашнего задания."""
    status = homework.get(STATUS_KEY)
    if not status:
        raise HomeworkStatusNotFoundError('Статус проверки задания не найден.')
    if status not in HOMEWORK_VERDICTS:
        raise UnexpectedHomeworkStatusError(
            f'В ответе от ({ENDPOINT}) получен статус '
            f'{status}, который не может быть обработан!'
        )
    homework_name = homework.get(HOMEWORK_NAME_KEY)
    if not homework_name:
        raise HomeworkNameNotFoundError(
            f'Не найдено содержимое ключа {HOMEWORK_NAME_KEY}!'
        )
    verdict = HOMEWORK_VERDICTS.get(status)
    logged_message = HOMEWORK_VERDICT_WAS_CHANGED.format(
        homework_name=homework_name,
        verdict=verdict,
    )
    logging.info(logged_message)
    return logged_message


def get_timestamp(days_ago: int) -> int:
    """Вычисляет значение Unix-время в прошлом."""
    date_in_past = datetime.now() - timedelta(days=days_ago)
    starting_from = int(time.mktime(date_in_past.timetuple()))
    return starting_from


def main():
    """Основная логика работы бота."""
    check_tokens()
    starting_from = get_timestamp(NUM_DAYS_AGO)
    bot = TeleBot(token=TELEGRAM_TOKEN)
    last_message = None
    while True:
        try:
            response = get_api_answer(starting_from)
            homeworks = check_response(response)
            if not homeworks:
                logging.debug(HOMEWORK_STATUS_NOT_CHANGED)
                continue
            if send_message(bot, parse_status(homeworks[0])):
                last_message = None
                starting_from = response.get('current_date', starting_from)
        except Exception as error:
            logging.error(PROGRAM_ERROR.format(error=error))
            if (error != last_message and send_message(
                    bot, PROGRAM_ERROR.format(error=error)
            )
            ):
                last_message = error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - '
               '%(filename)s->%(funcName)s:%(lineno)d, - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    main()
