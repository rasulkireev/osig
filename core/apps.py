import posthog
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        import core.signals  # noqa

        posthog.api_key = "phc_wa2RfooG5BAVE9zHHGkeEyF52nJTbwmcjdjrH32ZKl6"
        posthog.host = "https://us.i.posthog.com"
