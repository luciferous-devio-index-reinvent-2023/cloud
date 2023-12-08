import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from json.decoder import JSONDecodeError
from typing import Optional
from urllib.parse import quote_plus

from aws_lambda_powertools.utilities.data_classes import (
    CloudWatchLogsEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from common.aws import create_client
from common.load_environments import load_environments
from common.logger import create_logger, logging_function, logging_handler_exception


@dataclass
class EnvironmentVariables:
    sns_topic_error: str
    aws_default_region: str


@dataclass
class Message:
    message: str
    title: str


logger = create_logger(__name__)
jst = timezone(offset=timedelta(hours=+9), name="jst")


@event_source(data_class=CloudWatchLogsEvent)
@logging_handler_exception(logger)
def handler(
    event: CloudWatchLogsEvent, context: LambdaContext, sns_client=create_client("sns")
):
    env = load_environments(dataclass_type=EnvironmentVariables)
    message = create_message(event=event, region=env.aws_default_region)
    sns_client.publish(
        TopicArn=env.sns_topic_error, Message=message.message, Subject=message.title
    )


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
    elif (
        message.find("Task timed out") != -1
        or message.find("Runtime exited with error") != -1
    ):
        part = message.split(" ")
        return part[1]
    else:
        return None


@logging_function(logger)
def create_url_cw_logs(
    *,
    name_log_group: str,
    name_log_stream: str,
    timestamp: int,
    lambda_request_id: Optional[str],
    region: str,
) -> str:
    args_convert = ["%", "$"]
    part = [
        "https://",
        region,
        ".console.aws.amazon.com/cloudwatch/home?region=",
        region,
        "#logsV2:log-groups/log-group/",
        quote_plus(quote_plus(name_log_group)).replace("%", "$"),
        "/log-events/",
        quote_plus(quote_plus(name_log_stream)).replace("%", "$"),
        quote_plus("?").replace("%", "$"),
    ]
    if lambda_request_id is None:
        start = timestamp - 900000  # 1000 ms/s * 60 s/m * 15 m = 900000 ms
        part += [quote_plus(f"start={start}").replace("%", "$")]
    else:
        part += [
            quote_plus("filterPattern=").replace("%", "$"),
            quote_plus(quote_plus(f'"{lambda_request_id}"')).replace("%", "$"),
        ]
    return "".join(part)


@logging_function(logger)
def create_url_lambda(*, function_name: str, region: str) -> str:
    return "".join(
        [
            "https://",
            region,
            ".console.aws.amazon.com/lambda/home?region=",
            region,
            "#/functions/",
            function_name,
        ]
    )


@logging_function(logger)
def create_message(*, event: CloudWatchLogsEvent, region: str) -> Message:
    decompressed = event.parse_logs_data()
    function_name = decompressed.log_group.replace("/aws/lambda/", "")
    url_lambda = create_url_lambda(function_name=function_name, region=region)
    dt_now = datetime.now(jst)
    lines = [
        f'Function : "{function_name}"',
        f'LogGroup : "{decompressed.log_group}"',
        f'LogStream: "{decompressed.log_stream}"',
        f'Date(Now): "{dt_now}"',
        f"Lambda   :\n",
        f"　{url_lambda}",
    ]
    for log_event in decompressed.log_events:
        url_cw = create_url_cw_logs(
            name_log_group=decompressed.log_group,
            name_log_stream=decompressed.log_stream,
            timestamp=log_event.timestamp,
            lambda_request_id=get_lambda_request_id(message=log_event.message),
            region=region,
        )
        lines += [
            "",
            "=" * 30,
            "",
            f'Timestamp: "{log_event.timestamp}"',
            f'Date     : "{datetime.fromtimestamp(timestamp=(log_event.timestamp / 1000), tz=jst)}"',
            f"CW URL   :\n",
            f"　{url_cw}",
            f"\nMessage  :\n",
        ]
        try:
            lines.append(json.dumps(json.loads(log_event.message), indent=2, ensure_ascii=False))
        except JSONDecodeError:
            lines.append(log_event.message)

    return Message(
        message="\n".join(lines), title=f"Raise Error ({dt_now}) {function_name}"
    )
