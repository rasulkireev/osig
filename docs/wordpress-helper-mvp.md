# WordPress helper integration (MVP)

Wave 1 task [8/8] adds a lightweight WordPress helper for mapping common post/CPT fields to OSIG image params with resilient fallbacks.

## Endpoint

`POST /api/integrations/wordpress`

Input payload example:

```json
{
  "page_url": "https://example.com/jobs/senior-engineer",
  "post_title": "Senior Django Engineer",
  "post_name": "senior-django-engineer",
  "subtitle": "Join a remote product team",
  "excerpt": "We build resilient hiring products",
  "featured_image_url": "https://example.com/og-candidate.jpg",
  "logo_url": "https://example.com/logo.png",
  "fallback_image_url": "https://example.com/fallback.jpg",
  "style": "job_logo",
  "site": "x",
  "font": "helvetica",
  "key": "YOUR_OSIG_KEY",
  "format": "jpeg",
  "quality": 80,
  "version": "v2026-02-26"
}
```

Response shape:

```json
{
  "signed_url": "https://osig.app/g?...&exp=...&sig=...",
  "expires_at": "2026-02-26T12:34:56+00:00",
  "mapped_fields": {
    "title": "Senior Django Engineer",
    "subtitle": "We build resilient hiring products",
    "image_url": "https://example.com/logo.png",
    "style": "job_logo",
    "site": "x",
    "font": "helvetica",
    "format": "jpeg"
  },
  "fallbacks": [],
  "snippet": "<?php ... ?>"
}
```

## Mapping + fallback behavior

Inputs are mapped in this order:

- `title`: `title` -> `post_title` -> `seo_title` -> `post_name`(slugified)
- `subtitle`: `subtitle` -> `excerpt` -> `description`
- `image_url`: `featured_image_url` -> `featured_image` -> `logo_url`

If there is no image, `fallback_image_url` is used (if provided). Otherwise, no image is attached and `image_missing` fallback is returned.

## PHP snippet

The response contains a small PHP helper snippet that can be dropped into themes/plugins.
It:

- reads common post fields,
- resolves image/logo fallback chain,
- generates a URL with OSIG query params,
- can be adapted to call the signed endpoint for production keys.
