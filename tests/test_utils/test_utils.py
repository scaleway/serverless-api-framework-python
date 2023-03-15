from scw_serverless.utils.commands import get_command_path
from scw_serverless.utils.string import module_to_path


def test_get_command_path():
    assert get_command_path("python")
    assert get_command_path("node")


def test_module_to_path():
    assert module_to_path("abc.def") == "abc/def"
