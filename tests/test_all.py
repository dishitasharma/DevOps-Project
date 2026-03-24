"""Test suite for Jenkins Pipeline Template Library."""

import pytest
import tempfile
import os
from pathlib import Path


# ─── Registry tests ────────────────────────────────────────────────────────────

def test_registry_not_empty():
    from jenkins_pipeline_lib.core.registry import get_all_templates
    templates = get_all_templates()
    assert len(templates) >= 15


def test_get_template_by_id_valid():
    from jenkins_pipeline_lib.core.registry import get_template_by_id
    t = get_template_by_id("python-ci")
    assert t is not None
    assert t.name == "Python CI Pipeline"


def test_get_template_by_id_invalid():
    from jenkins_pipeline_lib.core.registry import get_template_by_id
    assert get_template_by_id("non-existent-xyz") is None


def test_get_all_categories():
    from jenkins_pipeline_lib.core.registry import get_all_categories
    cats = get_all_categories()
    assert "ci" in cats
    assert "deployment" in cats
    assert len(cats) >= 5


def test_templates_have_required_fields():
    from jenkins_pipeline_lib.core.registry import get_all_templates
    for t in get_all_templates():
        assert t.id, f"Template missing id"
        assert t.name, f"Template {t.id} missing name"
        assert t.description, f"Template {t.id} missing description"
        assert t.category, f"Template {t.id} missing category"
        assert t.complexity in ("simple", "moderate", "advanced")
        assert isinstance(t.parameters, dict)
        assert isinstance(t.tags, list)


# ─── Scorer tests ──────────────────────────────────────────────────────────────

def test_recommend_python_project():
    from jenkins_pipeline_lib.core.scorer import recommend_templates
    results = recommend_templates("Python Flask API", ["python", "flask"])
    assert len(results) > 0
    assert results[0]["id"] == "python-ci"


def test_recommend_docker_project():
    from jenkins_pipeline_lib.core.scorer import recommend_templates
    results = recommend_templates("containerized app", ["docker", "registry"])
    assert any(r["id"] == "docker-build-push" for r in results)


def test_recommend_returns_ranked():
    from jenkins_pipeline_lib.core.scorer import recommend_templates
    results = recommend_templates("kubernetes microservices deployment", ["k8s"])
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_recommend_top_n():
    from jenkins_pipeline_lib.core.scorer import recommend_templates
    results = recommend_templates("anything", [], top_n=5)
    assert len(results) <= 5


def test_recommend_empty_input():
    from jenkins_pipeline_lib.core.scorer import recommend_templates
    results = recommend_templates("", [], top_n=3)
    assert isinstance(results, list)


# ─── Generator tests ───────────────────────────────────────────────────────────

def test_generate_creates_jenkinsfile():
    from jenkins_pipeline_lib.core.generator import generate_files
    with tempfile.TemporaryDirectory() as tmpdir:
        written = generate_files("python-ci", tmpdir)
        assert "Jenkinsfile" in written
        jf = Path(tmpdir) / "Jenkinsfile"
        assert jf.exists()
        content = jf.read_text()
        assert "pipeline" in content
        assert "stage" in content


def test_generate_with_param_override():
    from jenkins_pipeline_lib.core.generator import generate_files
    with tempfile.TemporaryDirectory() as tmpdir:
        written = generate_files("python-ci", tmpdir, {"PYTHON_VERSION": "3.12"})
        jf = Path(tmpdir) / "Jenkinsfile"
        content = jf.read_text()
        assert "3.12" in content


def test_generate_extra_files():
    from jenkins_pipeline_lib.core.generator import generate_files
    with tempfile.TemporaryDirectory() as tmpdir:
        written = generate_files("python-ci", tmpdir)
        assert "requirements.txt" in written
        assert "setup.py" in written


def test_generate_invalid_template():
    from jenkins_pipeline_lib.core.generator import generate_files
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="not found"):
            generate_files("fake-template", tmpdir)


def test_generate_docker_dockerfile():
    from jenkins_pipeline_lib.core.generator import generate_files
    with tempfile.TemporaryDirectory() as tmpdir:
        written = generate_files("docker-build-push", tmpdir)
        assert "Dockerfile" in written


# ─── API tests ────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from jenkins_pipeline_lib.api.app import app
    return TestClient(app)


def test_api_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Jenkins" in r.json()["service"]


def test_api_list_templates(client):
    r = client.get("/templates")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 15


def test_api_list_templates_filter_category(client):
    r = client.get("/templates?category=ci")
    assert r.status_code == 200
    for t in r.json():
        assert t["category"] == "ci"


def test_api_get_template(client):
    r = client.get("/templates/python-ci")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "python-ci"
    assert "parameters" in data


def test_api_get_template_not_found(client):
    r = client.get("/templates/does-not-exist")
    assert r.status_code == 404


def test_api_get_jenkinsfile(client):
    r = client.get("/templates/python-ci/jenkinsfile")
    assert r.status_code == 200
    assert "pipeline" in r.text


def test_api_categories(client):
    r = client.get("/categories")
    assert r.status_code == 200
    cats = [c["name"] for c in r.json()]
    assert "ci" in cats


def test_api_recommend(client):
    r = client.post("/recommend", json={
        "description": "Python Django web app with Docker",
        "tags": ["python", "docker"],
        "top_n": 3
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) > 0
    assert data["results"][0]["rank"] == 1


def test_api_search(client):
    r = client.get("/search?q=docker")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert "docker-build-push" in ids


def test_api_templates_by_category(client):
    r = client.get("/categories/ci/templates")
    assert r.status_code == 200
    assert len(r.json()) > 0
