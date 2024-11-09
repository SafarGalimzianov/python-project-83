import docker
import pytest
import subprocess
import time
import requests


@pytest.fixture(scope="module")
def docker_client():
    return docker.from_env()


@pytest.fixture(scope="module")
def image(docker_client):
    image, logs = docker_client.images.build(path=".", dockerfile="Dockerfile")
    return image


@pytest.fixture(scope="module")
def container(docker_client, image):
    container = docker_client.containers.run(
        image.id,
        detach=True,
        environment={"PORT": "8000"},
        ports={"8000/tcp": 8000}
    )
    time.sleep(2)  # Wait for container to fully start
    yield container
    container.stop()
    container.remove()


def test_image_build(image):
    """Test if the image builds successfully"""
    assert image is not None


def test_python_version(container):
    """Test if correct Python version is installed"""
    result = container.exec_run("python --version")
    assert result.exit_code == 0
    assert b"Python 3.12" in result.output


def test_non_root_user(container):
    """Test if container runs as non-root user"""
    result = container.exec_run("whoami")
    assert result.exit_code == 0
    assert b"appuser" in result.output


def test_working_directory(container):
    """Test if working directory is set correctly"""
    result = container.exec_run("pwd")
    assert result.exit_code == 0
    assert b"/app" in result.output


def test_environment_variables(container):
    """Test if environment variables are set correctly"""
    result = container.exec_run('env')
    assert b"FLASK_APP=page_analyzer.app:app" in result.output
    assert b"FLASK_RUN_HOST=0.0.0.0" in result.output


def test_poetry_installation(container):
    """Test if Poetry is installed"""
    result = container.exec_run("poetry --version")
    assert result.exit_code == 0
    assert b"Poetry" in result.output


def test_required_packages(container):
    """Test if required system packages are installed"""
    packages = ["gcc", "make", "libpq-dev"]
    for package in packages:
        result = container.exec_run(f"dpkg -l | grep {package}")
        assert result.exit_code == 0


def test_container_running(container):
    """Test if container is running"""
    container.reload()
    assert container.status == "running"


def test_port_binding(container):
    """Test if port is correctly bound"""
    try:
        response = requests.get("http://localhost:8000", timeout=1)
        assert response.status_code in [200, 301, 302, 308]
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to the application")


def test_gunicorn_process(container):
    """Test if Gunicorn is running"""
    result = container.exec_run("ps aux")
    assert result.exit_code == 0
    assert b"gunicorn" in result.output


def test_file_permissions(container):
    """Test if file permissions are set correctly"""
    result = container.exec_run("ls -l /app")
    assert result.exit_code == 0
    assert b"appuser appuser" in result.output