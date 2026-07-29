import pytest

from backend.app import create_app
from backend.services.container import ServiceContainer


@pytest.fixture
def app():
    ServiceContainer.reset()
    application = create_app(testing=True)
    yield application
    ServiceContainer.reset()


@pytest.fixture
def client(app):
    return app.test_client()
