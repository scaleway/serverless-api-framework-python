from typing import Optional, Any
from typing_extensions import Self

from .event import Event


class CronSchedule(Event):
    def __init__(
        self,
        minutes: str,
        hours: str,
        day_of_month: str,
        month: str,
        day_of_week: str,
        seconds: str = "",
        year: Optional[str] = None,
        inputs: dict[str, Any] = {},
    ) -> None:
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
        if year is not None:
            fields.append(year)
        self.expression = " ".join(fields)
        self.inputs = inputs

    @property
    def kind(self) -> str:
        return "schedule"

    @classmethod
    def from_expression(cls, expression: str, inputs: dict[str, Any] = {}) -> Self:
        c = cls.__new__(cls)
        c.expression = expression
        c.inputs = inputs
        return c
