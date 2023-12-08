from functools import wraps
from typing import Callable

from aws_lambda_powertools import Logger


def logging_function(logger: Logger) -> Callable:
    def wrapper(func: Callable) -> Callable:
        @wraps(func)
        def process(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                message = f"raise error in {func.__name__}"
                extra = {"additional_data": {"args": args, "kwargs": kwargs}}
                logger.debug(message, extra=extra, exc_info=True)
                raise

        return process

    return wrapper
