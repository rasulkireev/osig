import io

from django.http import HttpResponse
from django.views.generic import TemplateView
from PIL import Image

from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)


class HomeView(TemplateView):
    template_name = "pages/home.html"


def blank_square_image(request):
    size = (200, 200)
    image = Image.new("RGB", size, color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_data = buffer.getvalue()
    response = HttpResponse(image_data, content_type="image/png")
    response["Content-Disposition"] = 'inline; filename="blank_square.png"'

    return response
