from pdfdancer import __version__


def test_version_is_exposed() -> None:
    assert isinstance(__version__, str)
    assert __version__
