import os
import pytest
import requests

DEFAULT_SERVER_URL = "http://roguewar.org"


def pytest_addoption(parser):
    parser.addoption(
        "--server-url",
        default=os.environ.get("ROGUEWAR_SERVER_URL", DEFAULT_SERVER_URL),
        help="PersistentMap server base URL (default: http://roguewar.org)",
    )


@pytest.fixture(scope="session")
def server_url(request):
    url = request.config.getoption("--server-url").rstrip("/")
    return url


@pytest.fixture(scope="session")
def war_services_url(server_url):
    return f"{server_url}/warServices"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s
