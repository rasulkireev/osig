from ninja import Schema

from core.choices import BlogPostStatus


class BlogPostIn(Schema):
    title: str
    description: str = ""
    slug: str
    tags: str = ""
    content: str
    icon: str | None = None  # URL or base64 string
    image: str | None = None  # URL or base64 string
    status: BlogPostStatus = BlogPostStatus.DRAFT


class BlogPostOut(Schema):
    status: str
    message: str


class SignOgUrlIn(Schema):
    params: dict[str, str | int | float | bool]
    expires_in_seconds: int = 3600


class SignOgUrlOut(Schema):
    signed_url: str
    expires_at: str
