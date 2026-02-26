from urllib.parse import urlencode

from django.http import HttpRequest
from django.urls import reverse
from ninja import NinjaAPI

from core.api.auth import superuser_api_auth
from core.api.schemas import BlogPostIn, BlogPostOut, SignOgUrlIn, SignOgUrlOut
from core.models import BlogPost
from core.signing import build_signed_params

api = NinjaAPI(docs_url=None)


@api.post("/blog-posts/submit", response=BlogPostOut, auth=[superuser_api_auth])
def submit_blog_post(request: HttpRequest, data: BlogPostIn):
    try:
        BlogPost.objects.create(
            title=data.title,
            description=data.description,
            slug=data.slug,
            tags=data.tags,
            content=data.content,
            status=data.status,
            # icon and image are ignored for now (file upload not handled)
        )
        return BlogPostOut(status="success", message="Blog post submitted successfully.")
    except Exception as e:
        return BlogPostOut(status="error", message=f"Failed to submit blog post: {str(e)}")


@api.post("/sign", response=SignOgUrlOut)
def sign_og_url(request: HttpRequest, data: SignOgUrlIn):
    base_url = request.build_absolute_uri(reverse("generate_image"))

    signed_params, expires_at = build_signed_params(
        params=data.params,
        expires_in_seconds=data.expires_in_seconds,
    )

    signed_url = f"{base_url}?{urlencode(signed_params)}"

    return SignOgUrlOut(
        signed_url=signed_url,
        expires_at=expires_at.isoformat(),
    )
