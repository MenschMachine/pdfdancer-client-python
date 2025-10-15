import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def set_test_environment():
    """Automatically set PDFDANCER_BASE_URL to localhost for all tests"""
    os.environ["PDFDANCER_BASE_URL"] = "http://localhost:8080"
    yield
