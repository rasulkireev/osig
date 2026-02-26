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


class OnboardingWizardIn(Schema):
    page_url: str = "https://osig.app"
    style: str = "base"
    site: str = "x"
    font: str = "helvetica"
    title: str = ""
    subtitle: str = ""
    eyebrow: str = ""
    image_url: str = ""
    format: str = "png"
    quality: str | int | None = None
    max_kb: str | int | None = None
    version: str = ""
    expires_in_seconds: int = 3600


class OnboardingWizardOut(Schema):
    signed_url: str
    expires_at: str
    meta_tags: str
    validation_links: dict[str, str]
