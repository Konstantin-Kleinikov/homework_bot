"""Исключения для приложения homework_bot."""


class EndpointNotAvailableError(Exception):
    """API endpoint не вернул ответ при обращении к нему."""


class HomeworkNotFoundError(KeyError):
    """В полученном ответе не найден ключ homeworks."""


class HomeworkStatusNotFoundError(Exception):
    """В полученном ответе не найден ключ status."""


class UnexpectedHomeworkStatusError(Exception):
    """В полученном ответе найдено необрабатываемое значение ключа status."""


class HomeworkNameNotFoundError(Exception):
    """В полученном ответе не найден ключ homework_name."""


class EnvVariableNotFoundError(Exception):
    """Переменная окружения не найдена."""
