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


class RenderMetricsOut(Schema):
    window_hours: int
    total_attempts: int
    failed_attempts: int
    fail_rate_percent: float
    p95_render_ms: int | None
    error_counts: dict[str, int]


class WordPressHelperIn(Schema):
    page_url: str
    post_title: str = ""
    post_name: str = ""
    seo_title: str = ""
    title: str = ""
    subtitle: str = ""
    excerpt: str = ""
    description: str = ""
    featured_image: str = ""
    featured_image_url: str = ""
    logo_url: str = ""
    fallback_image_url: str = ""
    eyebrow: str = ""
    style: str = "job_logo"
    site: str = "x"
    font: str = "helvetica"
    key: str = ""
    format: str = "png"
    quality: str | int | None = None
    max_kb: str | int | None = None
    version: str = ""
    expires_in_seconds: int = 3600


class WordPressHelperOut(Schema):
    signed_url: str
    expires_at: str
    mapped_fields: dict[str, str]
    fallbacks: list[str]
    snippet: str
