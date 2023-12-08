import json
from dataclasses import dataclass
from json.decoder import JSONDecodeError
from typing import Optional

from aws_lambda_powertools.utilities.data_classes import (CloudWatchLogsEvent,
                                                          event_source)
from aws_lambda_powertools.utilities.typing import LambdaContext
from common.load_environments import load_environments
from common.logger import (create_logger, logging_function,
                           logging_handler_exception)


@dataclass
class EnvironmentVariables:
    sns_topic_error: str


logger = create_logger(__name__)


@event_source(data_class=CloudWatchLogsEvent)
@logging_handler_exception(logger)
def handler(
    event: CloudWatchLogsEvent,
    context: LambdaContext,
):
    env = load_environments(dataclass_type=EnvironmentVariables)
    logger.debug("env", extra={"data": {"env": env}})
    logger.debug("event", extra={"data": {"event": event}})

    decompressed_log = event.parse_logs_data()
    logger.debug("decompressed", extra={"data": {"decompressed": decompressed_log}})


@logging_function(logger)
def get_lambda_request_id(message: str) -> Optional[str]:
    try:
        data = json.loads(message)
        return data["function_request_id"]
    except KeyError:
        return None
    except JSONDecodeError:
        pass

    if message.find("Runtime.ImportModuleError") == -1:
        return None
    elif message.find("Task timed out") != -1:
        part = message.split(" ")
        return part[1]
    elif message.find("Runtime exited with error") != -1:
        pass
    else:
        return None
