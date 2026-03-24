"""
Jenkins Pipeline Template Library - REST API
Run: uvicorn jenkins_pipeline_lib.api.app:app --reload
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import dataclasses

from jenkins_pipeline_lib.core.registry import (
    get_all_templates,
    get_template_by_id,
    get_all_categories,
    get_templates_by_category,
)
from jenkins_pipeline_lib.core.scorer import recommend_templates
from jenkins_pipeline_lib.core.generator import JENKINSFILES

app = FastAPI(
    title="Jenkins Pipeline Template Library API",
    description="REST API for browsing and recommending reusable Jenkins pipeline templates.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ─── Pydantic response models ──────────────────────────────────────────────────

class TemplateSummary(BaseModel):
    id: str
    name: str
    description: str
    category: str
    complexity: str
    tags: List[str]

class TemplateDetail(TemplateSummary):
    parameters: Dict[str, str]
    use_cases: List[str]
    requirements: List[str]

class RecommendRequest(BaseModel):
    description: str = Field(..., example="Node.js REST API with Docker deployment to Kubernetes")
    tags: List[str] = Field(default=[], example=["nodejs", "docker", "k8s"])
    top_n: int = Field(default=3, ge=1, le=10)

class RecommendResult(BaseModel):
    rank: int
    id: str
    name: str
    score: float
    matched_keywords: List[str]
    description: str
    category: str
    complexity: str

class RecommendResponse(BaseModel):
    query_description: str
    query_tags: List[str]
    results: List[RecommendResult]

class CategoryInfo(BaseModel):
    name: str
    count: int
    templates: List[str]


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", summary="API health check")
def root():
    return {
        "service": "Jenkins Pipeline Template Library",
        "version": "1.0.0",
        "endpoints": [
            "GET  /templates",
            "GET  /templates/{id}",
            "GET  /templates/{id}/jenkinsfile",
            "GET  /categories",
            "GET  /categories/{name}/templates",
            "POST /recommend",
            "GET  /search?q=...",
        ],
    }


@app.get("/templates", response_model=List[TemplateSummary], summary="List all templates")
def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    complexity: Optional[str] = Query(None, description="Filter by complexity: simple|moderate|advanced"),
):
    """Return all available Jenkins pipeline templates, with optional filters."""
    templates = get_all_templates()
    if category:
        templates = [t for t in templates if t.category == category]
    if complexity:
        templates = [t for t in templates if t.complexity == complexity]
    return [
        TemplateSummary(
            id=t.id, name=t.name, description=t.description,
            category=t.category, complexity=t.complexity, tags=t.tags
        )
        for t in templates
    ]


@app.get("/templates/{template_id}", response_model=TemplateDetail, summary="Get template details")
def get_template(template_id: str):
    """Return full details of a specific template by ID."""
    t = get_template_by_id(template_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")
    return TemplateDetail(
        id=t.id, name=t.name, description=t.description, category=t.category,
        complexity=t.complexity, tags=t.tags, parameters=t.parameters,
        use_cases=t.use_cases, requirements=t.requirements,
    )


@app.get(
    "/templates/{template_id}/jenkinsfile",
    response_class=PlainTextResponse,
    summary="Get raw Jenkinsfile content",
)
def get_jenkinsfile(template_id: str):
    """Return the raw Jenkinsfile template content for a given template ID."""
    t = get_template_by_id(template_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")
    raw = JENKINSFILES.get(template_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Jenkinsfile content not available for this template.")
    # Return with default params substituted
    try:
        return raw.format(**{k: v for k, v in t.parameters.items()})
    except KeyError:
        return raw


@app.get("/categories", response_model=List[CategoryInfo], summary="List all categories")
def list_categories():
    """List all template categories with counts."""
    cats = get_all_categories()
    return [
        CategoryInfo(
            name=cat,
            count=len(get_templates_by_category(cat)),
            templates=[t.id for t in get_templates_by_category(cat)],
        )
        for cat in cats
    ]


@app.get("/categories/{category_name}/templates", response_model=List[TemplateSummary], summary="Templates by category")
def templates_by_category(category_name: str):
    """Return all templates in a specific category."""
    templates = get_templates_by_category(category_name)
    if not templates:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found.")
    return [
        TemplateSummary(
            id=t.id, name=t.name, description=t.description,
            category=t.category, complexity=t.complexity, tags=t.tags
        )
        for t in templates
    ]


@app.post("/recommend", response_model=RecommendResponse, summary="Recommend best template for a project")
def recommend(request: RecommendRequest):
    """
    **Best-match endpoint.**

    Given a project description and optional tags, returns the top N most
    suitable Jenkins pipeline templates ranked by relevance score.

    Example request body:
    ```json
    {
      "description": "Python Flask REST API deployed with Docker to AWS ECS",
      "tags": ["python", "docker", "aws"],
      "top_n": 3
    }
    ```
    """
    results = recommend_templates(
        project_description=request.description,
        project_tags=request.tags,
        top_n=request.top_n,
    )
    return RecommendResponse(
        query_description=request.description,
        query_tags=request.tags,
        results=[RecommendResult(**r) for r in results],
    )


@app.get("/search", response_model=List[TemplateSummary], summary="Search templates")
def search_templates(q: str = Query(..., description="Search keyword")):
    """Search templates by keyword across ID, name, description, and tags."""
    q_lower = q.lower()
    results = [
        t for t in get_all_templates()
        if q_lower in t.id.lower()
        or q_lower in t.name.lower()
        or q_lower in t.description.lower()
        or any(q_lower in tag.lower() for tag in t.tags)
    ]
    return [
        TemplateSummary(
            id=t.id, name=t.name, description=t.description,
            category=t.category, complexity=t.complexity, tags=t.tags
        )
        for t in results
    ]
