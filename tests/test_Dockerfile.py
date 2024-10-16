import docker
import pytest


@pytest.fixture(scope="module")
def docker_client():
    return docker.from_env()

@pytest.fixture(scope="module")
def image(docker_client):
    image, logs = docker_client.images.build(path=".", dockerfile="Dockerfile")
    return image

def test_image_build(image):
    assert image is not None

@pytest.fixture(scope="module")
def container(docker_client, image):
    container = docker_client.containers.run(
        image.id,
        detach=True,
        environment={"PORT": "8000"},
        ports={"8000/tcp": 8000}
    )
    yield container
    container.stop()
    container.remove()

def test_container_running(container):
    assert container.status == "running"

def test_container_logs(container):
    logs = container.logs().decode("utf-8")
    assert "Running on http://0.0.0.0:8000/" in logs or "Booting worker with pid" in logs