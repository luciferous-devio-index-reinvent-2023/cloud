from datetime import datetime
from http.client import HTTPResponse
from time import sleep
from typing import Callable, Union
from urllib.request import Request, urlopen

from common.logger import create_logger, logging_function

logger = create_logger(__name__)


def create_http_client(
    sec: Union[int, float]
) -> Callable[[Union[str, Request]], HTTPResponse]:
    dt_prev = datetime.now()

    @logging_function(logger)
    def process(req: Union[str, Request]) -> HTTPResponse:
        nonlocal dt_prev
        delta = datetime.now() - dt_prev
        interval = sec - delta.total_seconds()
        if interval > 0:
            sleep(interval)
        try:
            return urlopen(req)
        finally:
            dt_prev = datetime.now()

    return process
