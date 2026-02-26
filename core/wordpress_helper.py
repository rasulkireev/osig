from dataclasses import dataclass


def _to_int_if_valid(value: str | int | None) -> int | None:
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class WordPressRenderResult:
    params: dict
    mapped_fields: dict[str, str]
    fallbacks: list[str]


def _first_non_empty(*values: str) -> str:
    for value in values:
        normalized = (value or "").strip()
        if normalized:
            return normalized
    return ""


def _slug_to_title(slug: str) -> str:
    normalized = (slug or "").strip()
    if not normalized:
        return ""

    return normalized.replace("-", " ").replace("_", " ").title()


def build_wordpress_render_params(
    *,
    page_url: str,
    post_title: str = "",
    post_name: str = "",
    seo_title: str = "",
    title: str = "",
    subtitle: str = "",
    excerpt: str = "",
    description: str = "",
    featured_image: str = "",
    featured_image_url: str = "",
    logo_url: str = "",
    fallback_image_url: str = "",
    eyebrow: str = "",
    style: str = "job_logo",
    site: str = "x",
    font: str = "helvetica",
    key: str = "",
    format: str = "png",
    quality: str | int | None = None,
    max_kb: str | int | None = None,
    version: str = "",
) -> WordPressRenderResult:
    if not page_url:
        raise ValueError("page_url is required")

    mapped_title = _first_non_empty(title, post_title, seo_title, _slug_to_title(post_name))
    mapped_subtitle = _first_non_empty(subtitle, excerpt, description)

    image_url = _first_non_empty(featured_image_url, featured_image, logo_url)
    fallbacks: list[str] = []

    if not image_url:
        if fallback_image_url:
            image_url = fallback_image_url.strip()
            fallbacks.append("image_fallback")
        else:
            fallbacks.append("image_missing")

    params = {
        "style": style or "job_logo",
        "site": site or "x",
        "font": font or "helvetica",
        "title": mapped_title,
        "subtitle": mapped_subtitle,
        "eyebrow": eyebrow,
        "format": format or "png",
        "key": key,
    }

    if key:
        params["key"] = key
    if image_url:
        params["image_url"] = image_url

    normalized_quality = _to_int_if_valid(quality)
    if normalized_quality is not None:
        params["quality"] = normalized_quality

    normalized_max_kb = _to_int_if_valid(max_kb)
    if normalized_max_kb is not None:
        params["max_kb"] = normalized_max_kb

    if version:
        params["v"] = version.strip()

    mapped_fields = {
        "page_url": page_url,
        "title": mapped_title,
        "subtitle": mapped_subtitle,
        "image_url": image_url,
        "style": params["style"],
        "site": params["site"],
        "font": params["font"],
        "eyebrow": params["eyebrow"],
        "format": params["format"],
    }

    return WordPressRenderResult(params=params, mapped_fields=mapped_fields, fallbacks=fallbacks)


def wordpress_helper_snippet(base_url: str, signed_url: str = "https://osig.app/g") -> str:
    return f"""<?php
/**
 * Lightweight WordPress helper for OSIG job posts
 */
function build_osig_meta_tags($post = null, $key = '') {{
    $post = $post ?: get_post();
    $title = get_the_title($post) ?: get_the_archive_title();
    $subtitle = get_the_excerpt($post) ?: wp_trim_words((string) get_the_content($post), 20);
    $image = get_the_post_thumbnail_url($post, 'full')
        ?: get_field('company_logo')
        ?: get_custom_logo_url($key)
        ?: '';

    if (empty($title)) {{
        $title = get_queried_object_id();
    }}

    $query = [
        'key' => $key,
        'title' => $title,
        'subtitle' => $subtitle,
        'image_url' => $image,
        'style' => 'job_logo',
        'site' => 'x',
        'font' => 'helvetica',
        'v' => gmdate('Y-m'),
    ];

    $query = array_filter($query, 'strlen');
    return add_query_arg($query, '{base_url}');
}}

// Usage in your template:
// <meta property="og:image" content="<?php echo esc_url(build_osig_meta_tags(null, '{{key}}')); ?>" />
?>
"""
