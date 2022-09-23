import pytest

from scw_serverless.events.schedule import CronSchedule


@pytest.mark.parametrize(
    "cron,expected_expression",
    [
        (CronSchedule("*", "*", "*", "*", "*", "*", "*"), "* * * * * * *"),
        (CronSchedule("0", "0", "*", "*", "FRI"), "0 0 * * FRI"),
    ],
)
def test_cron_as_expression(cron: CronSchedule, expected_expression: str):
    assert cron.expression == expected_expression
