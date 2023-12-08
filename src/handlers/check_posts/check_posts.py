import boto3
from common.logger import create_logger, logging_handler_exception

logger = create_logger(__name__)

s3 = boto3.client("s3")


@logging_handler_exception(logger)
def handler(event, context):
    raise Exception("test")
