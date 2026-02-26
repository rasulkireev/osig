# OSIG Onboarding Wizard

Wave 1 task [5/8] adds a guided onboarding flow for generating OG metadata quickly.

## What it does

- 5-step guided wizard available at `/onboarding`.
- Builds signed OG image URL via `/api/onboarding/meta`.
- Outputs ready-to-copy OG/Twitter meta tags.
- Generates validation checklist links:
  - Twitter/X Card Validator
  - Facebook Sharing Debugger
  - LinkedIn Post Inspector
  - Google Rich Results
- Keeps legacy behavior unchanged:
  - `/g` still accepts legacy style inputs.
  - image URL handling preserves `image_url` and `image_or_logo` compatibility.

## Output shape

`POST /api/onboarding/meta` returns:

- `signed_url`
- `expires_at`
- `meta_tags` (preformatted HTML tags)
- `validation_links` (map of label -> URL)

## Notes

- Quality is optional and only used for JPEG.
- `version` maps to the existing `v` cache-busting query param.
- `expires_in_seconds` defaults to 3600 if omitted.
