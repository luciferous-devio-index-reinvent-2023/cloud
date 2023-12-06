from dataclasses import dataclass

from aws_lambda_powertools.utilities.data_classes import (CloudWatchLogsEvent,
                                                          event_source)
from aws_lambda_powertools.utilities.typing import LambdaContext

from common.load_environments import load_environments
from common.logger import create_logger, logging_handler_exception


@dataclass
class EnvironmentVariables:
    sns_topic_error: str


logger = create_logger(__name__)


@event_source(data_class=CloudWatchLogsEvent)
@logging_handler_exception(logger)
def handler(event: CloudWatchLogsEvent, context: LambdaContext):
    env = load_environments(dataclass_type=EnvironmentVariables)
    logger.debug("env", extra={"data": {"env": env}})
    logger.debug("event", extra={"data": {"event": event}})

    decompressed_log = event.parse_logs_data()
    logger.debug("decompressed", extra={"data": {"decompressed": decompressed_log}})
