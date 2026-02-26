# Usage Metering + Quota Enforcement

Wave 1 task [6/8] adds per-key metering and configurable quota enforcement for `/g` requests.

## What is tracked

For requests that include a valid `key`:

- daily usage count
- monthly usage count
- warning sent flags (daily/monthly)

Storage model: `ProfileUsage` (one row per API key/profile).

## Enforcement rules

- warning threshold: `OSIG_USAGE_WARNING_PERCENT` (default `0.8`)
- hard block: at 100% of configured limit
- blocked requests return `429`

Configurable limits:

- `OSIG_DAILY_USAGE_LIMIT` (default `1000`)
- `OSIG_MONTHLY_USAGE_LIMIT` (default `10000`)

## Response headers

When a keyed request is accepted:

- `X-OSIG-Daily-Usage: <count>/<limit>`
- `X-OSIG-Monthly-Usage: <count>/<limit>`
- `X-OSIG-Quota-Warning: daily|monthly` (only when crossing warning threshold for the first time in the period)

## Backward compatibility

Existing no-key `/g` flows are unchanged and not quota-enforced.

## Admin visibility

`ProfileUsage` is registered in Django admin and sorted by `monthly_count` descending for quick top-key visibility.
