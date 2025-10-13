from django.http import HttpRequest
from ninja import NinjaAPI

from core.api.auth import superuser_api_auth
from core.api.schemas import BlogPostIn, BlogPostOut
from core.models import BlogPost

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
