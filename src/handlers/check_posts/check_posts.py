from common.logger import create_logger, logging_handler_exception

logger = create_logger(__name__)


@logging_handler_exception(logger)
def handler(event, context):
    raise Exception("test error")
