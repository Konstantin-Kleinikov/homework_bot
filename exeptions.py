"""Исключения для приложения homework_bot."""


class EndpointNotAvailable(Exception):
    pass


class HomeworkNotFound(Exception):
    pass


class HomeworkStatusNotFound(Exception):
    pass


class HomeworkResponseEmpty(Exception):
    pass


class UnexpectedHomeworkStatus(Exception):
    pass


class HomeworkNameNotFound(Exception):
    pass
