from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CronTrigger:
    """Cron trigger which will execute a function periodically.

    :param schedule: The Cron expression.
    :param args: Data to be sent in the body.
    :param name: Name to give to your resource.

    .. seealso:: https://developers.scaleway.com/en/products/functions/api/#create-a-cron-trigger-for-your-function
    """

    schedule: str
    args: Optional[dict[str, Any]] = None
    name: Optional[str] = None

    # pylint: disable=too-many-arguments
    @staticmethod
    def from_parts(
        minutes: str,
        hours: str,
        day_of_month: str,
        month: str,
        day_of_week: str,
        seconds: str = "",
        year: Optional[str] = None,
        args: Optional[dict[str, Any]] = None,
        name: Optional[str] = None,
    ):
        """Create a Cron expression from its parts."""
        fields = list(
            filter(
                lambda s: s != "",
                [
                    seconds,
                    minutes,
                    hours,
                    day_of_month,
                    month,
                    day_of_week,
                ],
            )
        )
        if year:
            fields.append(year)
        return CronTrigger(schedule=" ".join(fields), args=args, name=name)
