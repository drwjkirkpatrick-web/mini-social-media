import os


def test_dockerfile_exists():
    root = os.path.dirname(os.path.dirname(__file__))
    assert os.path.exists(os.path.join(root, "Dockerfile"))


def test_docker_compose_exists():
    root = os.path.dirname(os.path.dirname(__file__))
    assert os.path.exists(os.path.join(root, "docker-compose.yml"))


def test_gunicorn_config_exists():
    root = os.path.dirname(os.path.dirname(__file__))
    assert os.path.exists(os.path.join(root, "gunicorn.conf.py"))
