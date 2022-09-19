import pytest

from serverless.events.cron import Cron


@pytest.mark.parametrize(
    "cron,expected_expression",
    [
        (Cron("*", "*", "*", "*", "*", "*", "*"), "* * * * * *"),
        (Cron("*", "*", "*", "*", "*", "*"), "* * * * *"),
    ],
)
def test_cron_as_expression(cron, expected_expression: str):
    assert cron.as_expression() == expected_expression
