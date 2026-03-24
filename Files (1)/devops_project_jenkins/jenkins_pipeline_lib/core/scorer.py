"""Scoring engine to recommend the best Jenkins template for a given project."""

from typing import List, Dict, Tuple
from jenkins_pipeline_lib.core.registry import TemplateMetadata, get_all_templates


def score_template(template: TemplateMetadata, project_description: str, project_tags: List[str]) -> float:
    """
    Score a template against a project description and tags.
    Returns a float between 0.0 and 1.0.
    """
    desc_lower = project_description.lower()
    combined_input = desc_lower + " " + " ".join(t.lower() for t in project_tags)

    score = 0.0
    matched_keywords = []

    for kw in template.score_keywords:
        if kw.lower() in combined_input:
            score += 1.0
            matched_keywords.append(kw)

    # Bonus: if category keyword appears
    if template.category in combined_input:
        score += 0.5

    # Normalize against total keywords
    max_possible = len(template.score_keywords) + 0.5
    normalized = score / max_possible if max_possible > 0 else 0.0
    return round(min(normalized, 1.0), 4), matched_keywords


def recommend_templates(
    project_description: str,
    project_tags: List[str],
    top_n: int = 3
) -> List[Dict]:
    """
    Recommend top N templates for a project.
    Returns list of dicts sorted by score descending.
    """
    results = []
    for template in get_all_templates():
        score, matched = score_template(template, project_description, project_tags)
        results.append({
            "template": template,
            "score": score,
            "matched_keywords": matched,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    top = [r for r in results if r["score"] > 0][:top_n]

    if not top:
        # Return top_n by default if nothing matched
        top = results[:top_n]

    return [
        {
            "rank": i + 1,
            "id": r["template"].id,
            "name": r["template"].name,
            "score": r["score"],
            "matched_keywords": r["matched_keywords"],
            "description": r["template"].description,
            "category": r["template"].category,
            "complexity": r["template"].complexity,
        }
        for i, r in enumerate(top)
    ]
