from typing import Optional


class Cron:
    def __init__(
        self,
        seconds: str,
        minutes: str,
        hours: str,
        day_of_month: str,
        month: str,
        day_of_week: str,
        year: Optional[str] = None,
    ) -> None:
        self.seconds = seconds
        self.minutes = minutes
        self.hours = hours
        self.day_of_month = day_of_month
        self.month = month
        self.day_of_week = day_of_week
        self.year = year

    def as_expression(self) -> str:
        fields = [
            self.seconds,
            self.minutes,
            self.hours,
            self.day_of_month,
            self.day_of_week,
        ]
        if self.year is not None:
            fields.append(self.year)
        return " ".join(fields)
