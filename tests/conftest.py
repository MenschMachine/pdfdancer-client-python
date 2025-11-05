import datetime
import logging
import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def configure_logging():
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    start = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{start}] START {item.nodeid}")
    outcome = yield
    end = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{end}] END {item.nodeid}")


@pytest.fixture(scope="session", autouse=True)
def set_test_environment():
    """Automatically set PDFDANCER_BASE_URL to localhost for all tests"""
    if os.getenv("PDFDANCER_BASE_URL") is None:
        os.environ["PDFDANCER_BASE_URL"] = "http://localhost:8080"
    yield
