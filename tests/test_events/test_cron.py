import pytest

from serverless.events.cron import Cron


@pytest.mark.parametrize(
    "cron,expected_expression",
    [
        (Cron("*", "*", "*", "*", "*", "*", "*"), "* * * * * *"),
        (Cron("0", "0", "0", "*", "*", "TUE"), "0 0 0 * * TUE"),
    ],
)
def test_cron_as_expression(cron, expected_expression: str):
    assert cron.as_expression() == expected_expression
