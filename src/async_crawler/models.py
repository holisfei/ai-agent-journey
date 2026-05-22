from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Link(BaseModel):
    """超链接解析model"""

    url: str  # 用 str 不用 HttpUrl，因为href相对路径 /about 不是合法 URL
    text: str  # 链接的文案


class PageContent(BaseModel):
    """从一个网页提取出来的结构化内容model"""

    # 网页的标题
    title: str | None = None
    # 网页的描述
    description: str | None = None
    # h1 + h2 的文字内容
    headings: list[str] = Field(default_factory=list)
    # a 文字内容
    links: list[Link] = Field(default_factory=list)
    # body 总字数（粗略指标）
    text_length: int = 0


# default_factory=list 是 Pydantic 推荐的列表默认值写法（避免可变默认值共享的经典 bug）
# url 用 str 不用 HttpUrl —— 因为 HTML 里的链接经常是相对路径，并不是一个正确的url


class FetchStatus(str, Enum):  # 枚举，和 Pydantic 兼容
    """抓取结果状态"""

    OK = "ok"
    HTTP_ERROR = "http_error"  # 4xx / 5xx
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"  # DNS 失败、连接断开等
    PARSE_ERROR = "parse_error"
    NOT_ALLOWED = "not_allowed" # 禁止爬取


class PageResult(BaseModel):  # 所有可能失败的字段都是None
    """单个 URL 的完整抓取结果"""

    url: str
    status: FetchStatus
    http_code: int | None = None
    error: str | None = None  # 失败时的错误信息
    elapsed_ms: float = 0.0  # 耗时（毫秒）
    fetched_at: datetime = Field(default_factory=datetime.now)
    content: PageContent | None = None  # 成功时才有
