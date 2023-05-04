from scw_serverless.utils.string import module_to_path


def test_module_to_path():
    assert module_to_path("abc.def") == "abc/def"
