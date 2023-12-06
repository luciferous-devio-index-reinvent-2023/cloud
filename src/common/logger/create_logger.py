import json
from dataclasses import asdict, is_dataclass
from logging import DEBUG
from typing import Type, Union

from aws_lambda_powertools import Logger

TypeJsonlable = Union[int, float, str, bool, None, list, dict]


def custom_json_default(value: object) -> TypeJsonlable:
    if is_dataclass(value):
        if isinstance(value, Type):
            return str(value)
        else:
            return asdict(value)
    try:
        return {"type": str(type(value)), "value": str(value)}
    except Exception as e:
        return {
            "type": str(type(value)),
            "error": {"type": str(type(e)), "value": str(e)},
        }


def create_logger(name: str) -> Logger:
    return Logger(
        service=name, level=DEBUG, json_default=custom_json_default, use_rfc3339=True
    )
