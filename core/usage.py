from collections.abc import Iterable
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.models import ProfileUsage


def _is_enabled(limit: int | None) -> bool:
    return limit is not None and limit > 0


def _month_start_for(date):
    return date.replace(day=1)


def _warn_threshold(limit: int) -> int:
    return int(limit * float(settings.OSIG_USAGE_WARNING_PERCENT))


def _should_warn(count: int, limit: int | None) -> bool:
    if not _is_enabled(limit):
        return False

    return count >= _warn_threshold(limit)


def _limits_for_profile():
    return {
        "daily": settings.OSIG_DAILY_USAGE_LIMIT,
        "monthly": settings.OSIG_MONTHLY_USAGE_LIMIT,
    }


@dataclass(frozen=True)
class UsageState:
    blocked: bool
    blocked_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    daily_count: int
    monthly_count: int
    daily_limit: int | None
    monthly_limit: int | None


def _as_tuple(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(values)


def track_profile_usage(profile) -> UsageState:
    now = timezone.now()
    today = now.date()
    month_start = _month_start_for(today)
    limits = _limits_for_profile()

    with transaction.atomic():
        usage, _ = ProfileUsage.objects.select_for_update().get_or_create(
            profile=profile,
            defaults={
                "daily_date": today,
                "monthly_date": month_start,
            },
        )

        if usage.daily_date != today:
            usage.daily_date = today
            usage.daily_count = 0
            usage.daily_warning_sent = False

        if usage.monthly_date != month_start:
            usage.monthly_date = month_start
            usage.monthly_count = 0
            usage.monthly_warning_sent = False

        next_daily_count = usage.daily_count + 1
        next_monthly_count = usage.monthly_count + 1

        blocked_reasons: list[str] = []

        if _is_enabled(limits["daily"]) and next_daily_count >= limits["daily"]:
            blocked_reasons.append("daily")

        if _is_enabled(limits["monthly"]) and next_monthly_count >= limits["monthly"]:
            blocked_reasons.append("monthly")

        if blocked_reasons:
            return UsageState(
                blocked=True,
                blocked_reasons=_as_tuple(blocked_reasons),
                warnings=(),
                daily_count=usage.daily_count,
                monthly_count=usage.monthly_count,
                daily_limit=limits["daily"],
                monthly_limit=limits["monthly"],
            )

        usage.daily_count = next_daily_count
        usage.monthly_count = next_monthly_count

        warnings: list[str] = []

        if not usage.daily_warning_sent and _should_warn(usage.daily_count, limits["daily"]):
            usage.daily_warning_sent = True
            warnings.append("daily")

        if not usage.monthly_warning_sent and _should_warn(usage.monthly_count, limits["monthly"]):
            usage.monthly_warning_sent = True
            warnings.append("monthly")

        usage.save()

        return UsageState(
            blocked=False,
            blocked_reasons=(),
            warnings=_as_tuple(warnings),
            daily_count=usage.daily_count,
            monthly_count=usage.monthly_count,
            daily_limit=limits["daily"],
            monthly_limit=limits["monthly"],
        )
