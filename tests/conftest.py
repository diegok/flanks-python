import pytest


@pytest.fixture
def client_id() -> str:
    return "test_client_id"


@pytest.fixture
def client_secret() -> str:
    return "test_client_secret"


@pytest.fixture
def base_url() -> str:
    return "https://api.test.flanks.io"
