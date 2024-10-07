
## Supported values

### fonts
- helvetica

### site
- x
- meta


## Stripe
- When creating a webhook in the admin, specify the latest version from here https://stripe.com/docs/api/versioning

- Create your products in stripe (monthly, annual and one-time, for example), then sync them via `make stripe-sync` command.

- Current (`user-settings.html` and `pricing.html`) template assumes you have 3 products: monthly, annual and one-time.
  I haven't found a reliable way to programmatcialy set this template. When you have created your products in Stripe and synced them, update the template with the correct plan id.
