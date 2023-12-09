import json
from dataclasses import dataclass
from gzip import decompress
from typing import Dict, Type, TypeVar
from urllib.parse import urlparse

from common.aws import create_client
from common.http import sec1_http_client
from common.load_environments import load_environments
from common.logger import create_logger, logging_function, logging_handler_exception


@dataclass(frozen=True)
class EnvironmentVariables:
    notion_database_id: str
    ssm_param_name_notion_token: str
    ssm_param_name_cloudflare_deploy_hook_url: str
    s3_bucket_data: str
    s3_key_authors: str


@dataclass(frozen=True)
class SsmParameters:
    notion_token: str
    cloudflare_deploy_hook_url: str


@dataclass
class Author:
    id: int
    name: str
    link: str
    avatar: str


@dataclass(init=False)
class StoreAuthors:
    map_authors: Dict[str, Author]

    def __init__(self, body: bytes):
        data: dict = json.loads(body)
        self.map_authors = {k: Author(**v) for k, v in data.items()}

    def save_author(self, *, id_author: int) -> Author:
        resp = sec1_http_client(
            f"https://dev.classmethod.jp/wp-json/wp/v2/users/{id_author}"
        )
        data = json.load(resp)
        part_avatar = urlparse(data["avatar_urls"]["24"])
        author = Author(
            id=id_author,
            name=data["name"],
            link=data["link"],
            avatar=f"{part_avatar.scheme}://${part_avatar.hostname}{part_avatar.path}",
        )
        self.map_authors[str(id_author)] = author
        return author

    def get_author(self, *, id_author: int) -> Author:
        author = self.map_authors.get(str(id_author))
        if author is not None:
            return author
        return self.save_author(id_author=id_author)


logger = create_logger(__name__)
T = TypeVar("T")


@logging_handler_exception(logger)
def handler(
    event, context, client_s3=create_client("s3"), client_ssm=create_client("ssm")
):
    env = load_environments(dataclass_type=EnvironmentVariables)
    params = get_ssm_parameters(
        params=SsmParameters(
            notion_token=env.ssm_param_name_notion_token,
            cloudflare_deploy_hook_url=env.ssm_param_name_cloudflare_deploy_hook_url,
        ),
        client=client_ssm,
    )
    store_authors = get_os3_object(
        bucket=env.s3_bucket_data,
        key=env.s3_key_authors,
        type_return=StoreAuthors,
        client=client_s3,
        is_gz=True,
    )


@logging_function(logger)
def get_os3_object(
    *, bucket: str, key: str, type_return: Type[T], client, is_gz: bool = False
) -> T:
    resp = client.get_object(Bucket=bucket, Key=key)
    body = resp["Body"].read()
    if is_gz:
        body = decompress(body)
    return type_return(body)


@logging_function(logger)
def get_ssm_parameters(*, params: SsmParameters, client) -> SsmParameters:
    resp = client.get_parameters(
        WithDecryption=True,
        Names=[params.notion_token, params.cloudflare_deploy_hook_url],
    )
    map_params = {x["Name"]: x["Value"] for x in resp["Parameters"]}
    return SsmParameters(
        notion_token=map_params[params.notion_token],
        cloudflare_deploy_hook_url=map_params[params.cloudflare_deploy_hook_url],
    )
