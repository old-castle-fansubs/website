import pytest
from oc_website.tests.factories import ProjectFactory, ProjectReleaseFactory
from pytest_factoryboy import register

register(ProjectReleaseFactory)
register(ProjectFactory)


@pytest.fixture(scope="session")
def celery_config() -> dict[str, str]:
    return {"broker_url": "amqp://", "result_backend": "redis://"}
