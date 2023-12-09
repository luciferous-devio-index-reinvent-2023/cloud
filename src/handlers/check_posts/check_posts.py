import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from gzip import compress, decompress
from hashlib import sha3_256
from typing import Dict, List, Optional, Set, Tuple, Type, TypeVar
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request

from common.aws import create_client
from common.http import sec1_http_client
from common.load_environments import load_environments
from common.logger import create_logger, logging_function, logging_handler_exception

logger = create_logger(__name__)
T = TypeVar("T")
JST = timezone(offset=timedelta(hours=+9), name="JST")


@dataclass(frozen=True)
class EnvironmentVariables:
    notion_database_id: str
    ssm_param_name_notion_token: str
    ssm_param_name_cloudflare_deploy_hook_url: str
    s3_bucket_data: str
    s3_key_authors: str
    s3_key_edited: str
    sns_topic_error: str


@dataclass(frozen=True)
class SsmParameters:
    notion_token: str
    cloudflare_deploy_hook_url: str


@dataclass(init=False)
class StoreEdited:
    array_edited: List[int]

    @logging_function(logger)
    def __init__(self, binary: bytes):
        self.array_edited = json.loads(binary)


@dataclass
class Author:
    id: int
    name: str
    link: str
    avatar: str


@dataclass(init=False)
class StoreAuthors:
    map_authors: Dict[str, Author]
    hash_raw: str

    @logging_function(logger)
    def __init__(self, body: bytes):
        data: dict = json.loads(body)
        self.map_authors = {k: Author(**v) for k, v in data.items()}
        self.hash_raw = sha3_256(body).hexdigest()

    @logging_function(logger)
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

    @logging_function(logger)
    def get_author(self, *, id_author: int) -> Author:
        author = self.map_authors.get(str(id_author))
        if author is not None:
            return author
        return self.save_author(id_author=id_author)

    @logging_function(logger)
    def convert_to_json_gz(self) -> Tuple[bytes, bool]:
        authors = {
            k: self.map_authors[k]
            for k in sorted(self.map_authors.keys(), key=lambda x: int(x))
        }
        binary = json.dumps(authors, ensure_ascii=False, default=asdict).encode()
        hash_current = sha3_256(binary).hexdigest()
        result = compress(binary)
        return result, hash_current != self.hash_raw


@dataclass(init=False)
class DevioPost:
    id: int
    title: str
    url: str
    date: str
    raw_date: str
    author_name: str
    author_url: str
    author_avatar: str

    @logging_function(logger)
    def __init__(self, data: dict, store_authors: StoreAuthors):
        self.id = data["id"]
        self.title = data["title"]["rendered"]
        self.url = data["link"]
        self.raw_date = data["date"]
        self.date = self.raw_date[:10].replace("-", ".")
        id_author: int = data["author"]
        author = store_authors.get_author(id_author=id_author)
        self.author_name = author.name
        self.author_url = author.link
        self.author_avatar = author.avatar


@dataclass
class NotionItem:
    post_id: int
    edited: bool


@logging_handler_exception(logger)
def handler(
    event,
    context,
    client_s3=create_client("s3"),
    client_ssm=create_client("ssm"),
    client_sns=create_client("sns"),
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
    store_prev_edited = get_os3_object(
        bucket=env.s3_bucket_data,
        key=env.s3_key_edited,
        type_return=StoreEdited,
        client=client_s3,
        is_gz=False,
    )
    devio_posts = get_reinvent_posts(store_authors=store_authors)
    notion_items = query_notion_database(
        notion_database_id=env.notion_database_id, notion_token=params.notion_token
    )
    logger.info(
        "data count",
        data={
            "authors": len(store_authors.map_authors),
            "store_edited": len(store_prev_edited.array_edited),
            "devio_posts": len(devio_posts),
            "notion_items": len(notion_items),
        },
    )

    compressed_authors, is_flush_authors = store_authors.convert_to_json_gz()
    if is_flush_authors:
        put_s3_object(
            bucket=env.s3_bucket_data,
            key=env.s3_key_authors,
            body=compressed_authors,
            client=client_s3,
        )

    union_notion_edited_post_id = convert_to_current_edited(notion_items=notion_items)
    if is_deploy(
        prev_edited_post_id=store_prev_edited.array_edited,
        union_notion_edited_post_id=union_notion_edited_post_id,
    ):
        logger.info("call deploy")
        call_deploy(cloudflare_deploy_hook_url=params.cloudflare_deploy_hook_url)
        put_s3_object(
            bucket=env.s3_bucket_data,
            key=env.s3_key_edited,
            body=json.dumps(sorted(union_notion_edited_post_id)).encode(),
            client=client_s3,
        )

    union_insert_target_post_id = get_insert_target_post_id(
        devio_posts=devio_posts, notion_items=notion_items
    )
    if len(union_insert_target_post_id) > 0:
        logger.info("exec insert")
        notify_not_edit_post(sns_topic_arn=env.sns_topic_error, client=client_sns)
        for post in devio_posts:
            if post.id not in union_insert_target_post_id:
                continue
            exec_insert(
                devio_post=post,
                notion_database_id=env.notion_database_id,
                notion_token=params.notion_token,
            )


@logging_function(logger)
def get_os3_object(
    *, bucket: str, key: str, type_return: Type[T], client, is_gz: bool
) -> T:
    resp = client.get_object(Bucket=bucket, Key=key)
    body = resp["Body"].read()
    if is_gz:
        body = decompress(body)
    return type_return(body)


@logging_function(logger)
def put_s3_object(*, bucket: str, key: str, body: bytes, client):
    client.put_object(Bucket=bucket, Key=key, Body=body)


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


@logging_function(logger)
def get_reinvent_posts(*, store_authors: StoreAuthors) -> List[DevioPost]:
    result = []
    page = 0
    while True:
        page += 1
        try:
            resp = sec1_http_client(
                f"https://dev.classmethod.jp/wp-json/wp/v2/posts?referencecat=10107&page={page}"
            )
            data = json.load(resp)
            result += [DevioPost(data=x, store_authors=store_authors) for x in data]
        except HTTPError as e:
            if e.status != 400:
                raise
            data = json.load(e.fp)
            if data["code"] != "rest_post_invalid_page_number":
                raise
            return result


@logging_function(logger)
def query_notion_database(
    *, notion_database_id: str, notion_token: str
) -> List[NotionItem]:
    result = []
    token: Optional[str] = None

    while token is not None or len(result) == 0:
        payload = {}
        if token is not None:
            payload["start_cursor"] = token
        req = Request(
            url=f"https://api.notion.com/v1/databases/{notion_database_id}/query",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
                "Authorization": f"Bearer {notion_token}",
            },
            data=json.dumps(payload).encode(),
        )
        resp = sec1_http_client(req)
        data = json.load(resp)
        token = data.get("next_cursor")
        result += [
            NotionItem(
                post_id=x["properties"]["PostId"]["number"],
                edited=x["properties"]["Edited"]["checkbox"],
            )
            for x in data["results"]
        ]

    return result


@logging_function(logger)
def is_deploy(
    *,
    prev_edited_post_id: List[int],
    union_notion_edited_post_id: Set[int],
) -> bool:
    union_edited_post_id = set(prev_edited_post_id)
    return union_edited_post_id != union_notion_edited_post_id


@logging_function(logger)
def call_deploy(*, cloudflare_deploy_hook_url: str):
    req = Request(url=cloudflare_deploy_hook_url, method="POST")
    sec1_http_client(req)


@logging_function(logger)
def convert_to_current_edited(*, notion_items: List[NotionItem]) -> Set[int]:
    return set([x.post_id for x in notion_items if x.edited])


@logging_function(logger)
def get_insert_target_post_id(
    *, devio_posts: List[DevioPost], notion_items: List[NotionItem]
) -> Set[int]:
    union_devio_post_id = set([x.id for x in devio_posts])
    union_notion_post_id = set([x.post_id for x in notion_items])
    return union_devio_post_id - union_notion_post_id


@logging_function(logger)
def exec_insert(*, devio_post: DevioPost, notion_database_id: str, notion_token: str):
    req = Request(
        url="https://api.notion.com/v1/pages",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
            "Authorization": f"Bearer {notion_token}",
        },
        data=json.dumps(
            {
                "parent": {"database_id": notion_database_id},
                "properties": {
                    "Title": {"title": [{"text": {"content": devio_post.title}}]},
                    "URL": {"url": devio_post.url},
                    "Date": {"rich_text": [{"text": {"content": devio_post.date}}]},
                    "RawDate": {
                        "rich_text": [{"text": {"content": devio_post.raw_date}}]
                    },
                    "AuthorName": {
                        "rich_text": [{"text": {"content": devio_post.author_name}}]
                    },
                    "AuthorUrl": {"url": devio_post.author_url},
                    "AuthorAvatar": {"url": devio_post.author_avatar},
                    "PostId": {
                        "number": devio_post.id
                    }
                },
            }
        ).encode(),
    )
    sec1_http_client(req)


@logging_function(logger)
def notify_not_edit_post(*, sns_topic_arn: str, client):
    lines = [str(datetime.now(JST)), "NotionのDBに編集していないデータがあります。", "編集してください。"]
    client.publish(
        TopicArn=sns_topic_arn,
        Message="\n".join(lines),
        Subject=f"編集していない投稿があります！ ({datetime.now(JST)})",
    )
