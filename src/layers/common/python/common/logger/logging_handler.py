from functools import wraps
from typing import Callable

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext


def logging_handler_exception(logger: Logger) -> Callable:
    def wrapper(func: Callable) -> Callable:
        @logger.inject_lambda_context
        @wraps(func)
        def process(event: dict, context: LambdaContext, *args, **kwargs):
            try:
                return func(event, context, *args, **kwargs)
            except Exception as e:
                logger.exception(e)
                raise

        return process

    return wrapper
