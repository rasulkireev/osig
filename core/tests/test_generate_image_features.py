import io
import json
from datetime import timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from django.utils import timezone
from PIL import Image

from core.image_styles import _safe_truncate, generate_job_clean_image
from core.signing import build_signed_params


@pytest.fixture
def disable_async_tasks(monkeypatch):
    import core.views as core_views

    monkeypatch.setattr(core_views, "async_task", lambda *args, **kwargs: None)


def _tiny_png_buffer():
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16), color="white").save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


@pytest.mark.django_db
class TestSignedUrls:
    def test_sign_endpoint_returns_signed_og_url(self, client):
        payload = {
            "params": {
                "style": "base",
                "site": "x",
                "title": "Signed title",
                "subtitle": "Signed subtitle",
            },
            "expires_in_seconds": 300,
        }

        response = client.post("/api/sign", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 200
        data = response.json()

        signed_url = data["signed_url"]
        parsed = urlparse(signed_url)
        parsed_query = parse_qs(parsed.query)

        assert parsed.path == "/g"
        assert parsed_query["title"] == ["Signed title"]
        assert "sig" in parsed_query
        assert "exp" in parsed_query

    def test_generate_image_accepts_valid_signature(self, client, disable_async_tasks, monkeypatch):
        import core.views as core_views

        monkeypatch.setattr(core_views, "generate_image_router", lambda params: _tiny_png_buffer())

        signed_params, _ = build_signed_params(
            {
                "style": "base",
                "site": "x",
                "title": "Valid Signature",
                "subtitle": "Works",
            },
            expires_in_seconds=300,
        )

        response = client.get("/g", data=signed_params)

        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"
        assert "max-age=" in response["Cache-Control"]
        assert "immutable" not in response["Cache-Control"]

    def test_generate_image_rejects_tampered_signature(self, client, disable_async_tasks, monkeypatch):
        import core.views as core_views

        monkeypatch.setattr(core_views, "generate_image_router", lambda params: _tiny_png_buffer())

        signed_params, _ = build_signed_params(
            {
                "style": "base",
                "site": "x",
                "title": "Original Title",
            },
            expires_in_seconds=300,
        )
        signed_params["title"] = "Tampered Title"

        response = client.get("/g", data=signed_params)

        assert response.status_code == 403

    def test_generate_image_rejects_expired_signature(self, client, disable_async_tasks, monkeypatch):
        import core.views as core_views

        monkeypatch.setattr(core_views, "generate_image_router", lambda params: _tiny_png_buffer())

        signed_params, _ = build_signed_params(
            {
                "style": "base",
                "site": "x",
                "title": "Expired Signature",
            },
            expires_in_seconds=60,
            now=timezone.now() - timedelta(hours=2),
        )

        response = client.get("/g", data=signed_params)

        assert response.status_code == 403


@pytest.mark.django_db
class TestOutputFormatAndCompression:
    def test_generate_image_supports_png_and_jpeg_content_types(self, client, disable_async_tasks):
        common_params = {
            "style": "base",
            "site": "x",
            "title": "Format Test",
            "subtitle": "Content types",
        }

        png_response = client.get("/g", data={**common_params, "format": "png"})
        jpeg_response = client.get("/g", data={**common_params, "format": "jpeg", "quality": "70"})

        assert png_response.status_code == 200
        assert png_response["Content-Type"] == "image/png"

        assert jpeg_response.status_code == 200
        assert jpeg_response["Content-Type"] == "image/jpeg"
        assert jpeg_response.content.startswith(b"\xff\xd8")

    def test_jpeg_quality_output_is_deterministic(self, client, disable_async_tasks):
        params = {
            "style": "base",
            "site": "x",
            "title": "Deterministic",
            "subtitle": "JPEG quality",
            "format": "jpeg",
            "quality": "62",
        }

        first = client.get("/g", data=params)
        second = client.get("/g", data=params)
        lower_quality = client.get("/g", data={**params, "quality": "20"})

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.content == second.content
        assert first.content != lower_quality.content


@pytest.mark.django_db
class TestJobBoardTemplatePack:
    @pytest.mark.parametrize("style", ["job_classic", "job_logo", "job_clean"])
    def test_generate_image_supports_job_board_styles(self, client, disable_async_tasks, style):
        response = client.get(
            "/g",
            data={
                "style": style,
                "site": "x",
                "title": "Senior Django Engineer",
                "subtitle": "Ship production systems for real users",
                "eyebrow": "Remote",
            },
        )

        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"

    def test_image_or_logo_alias_is_used_when_image_url_is_missing(self, client, disable_async_tasks, monkeypatch):
        import core.views as core_views

        captured_params = {}

        def fake_router(params):
            captured_params.update(params)
            return _tiny_png_buffer()

        monkeypatch.setattr(core_views, "generate_image_router", fake_router)

        response = client.get(
            "/g",
            data={
                "style": "job_logo",
                "title": "Founding Designer",
                "subtitle": "Craft our product experience",
                "image_or_logo": "https://example.com/logo.png",
            },
        )

        assert response.status_code == 200
        assert captured_params["image_url"] == "https://example.com/logo.png"

    def test_safe_truncation_limits_copy_length(self):
        long_text = "A" * 500
        truncated = _safe_truncate(long_text, 64)

        assert len(truncated) <= 64
        assert truncated.endswith("...")

    def test_job_clean_template_handles_long_copy_without_errors(self):
        image = generate_job_clean_image(
            profile_id=None,
            site="x",
            font="helvetica",
            title="Senior Python Engineer " * 30,
            subtitle="Build reliable systems and own customer outcomes. " * 40,
            eyebrow="Hiring now " * 20,
            image_url=None,
        )

        assert image.getbuffer().nbytes > 0


@pytest.mark.django_db
class TestCacheAndVersioning:
    def test_v_query_param_changes_cache_key_lookup(self, client, disable_async_tasks, monkeypatch):
        import core.views as core_views

        requested_image_data = []

        def fake_filter(*args, **kwargs):
            image_data = kwargs["image_data"]
            requested_image_data.append(dict(image_data))

            version = image_data.get("v")
            payload = b"image-v1" if version == "1" else b"image-v2"
            cached_object = SimpleNamespace(
                id=1,
                generated_image=payload,
                updated_at=timezone.now(),
            )
            return SimpleNamespace(first=lambda: cached_object)

        monkeypatch.setattr(core_views.ImageModel.objects, "filter", fake_filter)

        response_v1 = client.get("/g", data={"style": "base", "title": "Cache", "v": "1"})
        response_v2 = client.get("/g", data={"style": "base", "title": "Cache", "v": "2"})

        assert response_v1.status_code == 200
        assert response_v2.status_code == 200
        assert response_v1.content == b"image-v1"
        assert response_v2.content == b"image-v2"

        assert requested_image_data[0]["v"] == "1"
        assert requested_image_data[1]["v"] == "2"

    def test_generate_image_sets_explicit_cache_headers(self, client, disable_async_tasks, monkeypatch):
        import core.views as core_views

        monkeypatch.setattr(core_views, "generate_image_router", lambda params: _tiny_png_buffer())

        response = client.get("/g", data={"style": "base", "title": "Cache headers"})

        assert response.status_code == 200
        assert response["Cache-Control"] == "public, max-age=31536000, immutable"
