import os
from dataclasses import fields, is_dataclass
from typing import Type, TypeVar

from common.logger import create_logger, logging_function

T = TypeVar("T")
logger = create_logger(__name__)


@logging_function(logger)
def load_environments(*, dataclass_type: Type[T]) -> T:
    if not is_dataclass(dataclass_type):
        raise TypeError("dataclas_type is not dataclass")
    return dataclass_type(
        **{f.name: os.environ[f.name.upper()] for f in fields(dataclass_type)}
    )
