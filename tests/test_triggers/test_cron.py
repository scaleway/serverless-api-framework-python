import pytest

from scw_serverless.triggers import CronTrigger


@pytest.mark.parametrize(
    "cron,expected_expression",
    [
        (CronTrigger.from_parts("*", "*", "*", "*", "*", "*", "*"), "* * * * * * *"),
        (CronTrigger.from_parts("0", "0", "*", "*", "FRI"), "0 0 * * FRI"),
    ],
)
def test_cron_as_expression(cron: CronTrigger, expected_expression: str):
    assert cron.schedule == expected_expression
