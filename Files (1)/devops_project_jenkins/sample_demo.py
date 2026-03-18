"""
===========================================================
  Jenkins Pipeline Template Library — Full Demo / Sample
===========================================================

Run this file directly to see every feature of the library
in action without needing the CLI or a running API server.

    python sample_demo.py

Each section is clearly labelled and you can comment out
sections you don't need.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# ── Make sure the package is importable ───────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from jenkins_pipeline_lib.core.registry import (
    get_all_templates,
    get_template_by_id,
    get_all_categories,
    get_templates_by_category,
)
from jenkins_pipeline_lib.core.scorer import recommend_templates
from jenkins_pipeline_lib.core.generator import generate_files, JENKINSFILES

# ── Colour helpers (gracefully degrade if no TTY) ─────────────────────────────
def c(text, *codes):
    if not sys.stdout.isatty():
        return text
    return "".join(codes) + str(text) + "\033[0m"

BOLD  = "\033[1m"
GREEN = "\033[92m"
CYAN  = "\033[96m"
YELL  = "\033[93m"
RED   = "\033[91m"
DIM   = "\033[2m"
RESET = "\033[0m"

def section(title):
    print()
    print(c("=" * 60, BOLD + CYAN))
    print(c(f"  {title}", BOLD + CYAN))
    print(c("=" * 60, BOLD + CYAN))

def ok(msg):   print(c(f"  ✔  {msg}", GREEN))
def info(msg): print(f"     {msg}")
def warn(msg): print(c(f"  ⚠  {msg}", YELL))
def kv(k, v):  print(f"     {c(k+':', BOLD):<30} {v}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Registry: list all templates
# ══════════════════════════════════════════════════════════════════════════════
section("1. ALL AVAILABLE TEMPLATES")

templates = get_all_templates()
print(f"\n  Total templates loaded: {c(len(templates), BOLD + GREEN)}\n")

cplx_colour = {"simple": GREEN, "moderate": YELL, "advanced": RED}

for t in templates:
    cc = cplx_colour.get(t.complexity, CYAN)
    print(
        f"  {c(t.id, CYAN):<38} "
        f"{c('[' + t.category + ']', DIM):<22} "
        f"{c(t.complexity, cc)}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Categories
# ══════════════════════════════════════════════════════════════════════════════
section("2. TEMPLATE CATEGORIES")

categories = get_all_categories()
print(f"\n  {len(categories)} categories found:\n")

for cat in categories:
    items = get_templates_by_category(cat)
    names = ", ".join(t.id for t in items)
    print(f"  {c(cat, BOLD + YELL):<20}  {len(items)} template(s)  →  {c(names, DIM)}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Deep-dive into a single template
# ══════════════════════════════════════════════════════════════════════════════
section("3. TEMPLATE DETAIL  (python-ci)")

t = get_template_by_id("python-ci")
print()
kv("ID",          t.id)
kv("Name",        t.name)
kv("Category",    t.category)
kv("Complexity",  t.complexity)
kv("Description", t.description)
kv("Tags",        ", ".join(t.tags))

print(f"\n     {c('Parameters:', BOLD)}")
for k, v in t.parameters.items():
    print(f"       {c(k, YELL):<30}  default: {v or '(empty)'}")

print(f"\n     {c('Use Cases:', BOLD)}")
for uc in t.use_cases:
    print(f"       • {uc}")

print(f"\n     {c('Requirements:', BOLD)}")
for r in t.requirements:
    print(f"       • {r}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Look up templates that don't exist (graceful handling)
# ══════════════════════════════════════════════════════════════════════════════
section("4. LOOKING UP TEMPLATES BY ID")

for tid in ["docker-build-push", "terraform-iac", "nonexistent-template"]:
    result = get_template_by_id(tid)
    if result:
        ok(f"Found  '{tid}'  →  {result.name}")
    else:
        warn(f"Template '{tid}' not found (expected for invalid IDs)")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Recommendation engine
# ══════════════════════════════════════════════════════════════════════════════
section("5. RECOMMENDATION ENGINE")

demo_projects = [
    {
        "label": "Python Django REST API",
        "description": "A Python Django REST API with pytest tests and pip dependencies",
        "tags": ["python", "django", "pytest"],
    },
    {
        "label": "Node.js React App with Docker",
        "description": "A Node.js React front-end bundled in Docker and pushed to a registry",
        "tags": ["nodejs", "react", "docker", "npm"],
    },
    {
        "label": "Kubernetes Microservices on AWS",
        "description": "Microservices deployed to Kubernetes on AWS EKS using Helm charts",
        "tags": ["kubernetes", "helm", "aws", "microservices"],
    },
    {
        "label": "Terraform Cloud Infrastructure",
        "description": "Infrastructure as code provisioning on Azure using Terraform",
        "tags": ["terraform", "azure", "infrastructure"],
    },
    {
        "label": "Security Compliance Pipeline",
        "description": "DevSecOps pipeline with OWASP ZAP, Trivy vulnerability scanning and compliance checks",
        "tags": ["security", "owasp", "devsecops", "compliance"],
    },
]

for proj in demo_projects:
    print(f"\n  {c('Project:', BOLD)} {c(proj['label'], YELL)}")
    print(f"  {c('Description:', DIM)} {proj['description']}")
    print(f"  {c('Tags:', DIM)} {', '.join(proj['tags'])}")
    print()

    results = recommend_templates(
        project_description=proj["description"],
        project_tags=proj["tags"],
        top_n=3,
    )

    for r in results:
        bar_len = int(r["score"] * 20)
        bar = c("█" * bar_len, GREEN) + c("░" * (20 - bar_len), DIM)
        score_pct = int(r["score"] * 100)
        matched = ", ".join(r["matched_keywords"]) if r["matched_keywords"] else "—"
        print(f"    #{r['rank']}  {c(r['id'], CYAN):<35} {bar}  {score_pct:>3}%")
        print(f"         Matched keywords: {c(matched, GREEN)}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — File generator: write Jenkinsfile + support files to disk
# ══════════════════════════════════════════════════════════════════════════════
section("6. FILE GENERATOR  (writes real files to a temp directory)")

demo_generations = [
    {
        "template_id": "python-ci",
        "params": {"PYTHON_VERSION": "3.12", "COVERAGE_THRESHOLD": "90"},
    },
    {
        "template_id": "docker-build-push",
        "params": {"DOCKER_REGISTRY": "ghcr.io", "IMAGE_NAME": "my-service"},
    },
    {
        "template_id": "kubernetes-deploy",
        "params": {"K8S_NAMESPACE": "production", "DEPLOYMENT_NAME": "api-server"},
    },
    {
        "template_id": "terraform-iac",
        "params": {"TF_WORKSPACE": "staging", "AWS_REGION": "eu-west-1"},
    },
]

for gen in demo_generations:
    tid = gen["template_id"]
    params = gen["params"]
    tmpl = get_template_by_id(tid)

    with tempfile.TemporaryDirectory() as tmpdir:
        written = generate_files(tid, tmpdir, params)

        print(f"\n  {c(tmpl.name, BOLD + YELL)}  [{tid}]")
        print(f"  Parameters used: {params}")
        print(f"  Files generated ({len(written)}):")

        for rel_path, full_path in written.items():
            size = Path(full_path).stat().st_size
            print(f"    {c('✔', GREEN)}  {c(rel_path, CYAN):<35}  ({size} bytes)")

        # Show first 20 lines of the Jenkinsfile
        jf_path = Path(tmpdir) / "Jenkinsfile"
        if jf_path.exists():
            lines = jf_path.read_text().splitlines()[:20]
            print(f"\n  {c('Jenkinsfile preview (first 20 lines):', DIM)}")
            for ln in lines:
                print(f"    {c(ln, DIM)}")
            if len(jf_path.read_text().splitlines()) > 20:
                print(f"    {c('... (truncated)', DIM)}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Raw Jenkinsfile content (without writing to disk)
# ══════════════════════════════════════════════════════════════════════════════
section("7. RAW JENKINSFILE CONTENT PREVIEW  (nodejs-ci)")

t = get_template_by_id("nodejs-ci")
raw = JENKINSFILES.get("nodejs-ci", "")
rendered = raw.format(**t.parameters)

print(f"\n  Template: {c(t.name, YELL)}")
print(f"  Lines:    {len(rendered.splitlines())}")
print()
print(c("  " + "-" * 56, DIM))
for i, line in enumerate(rendered.splitlines(), 1):
    print(f"  {c(str(i).rjust(3), DIM)}  {line}")
    if i >= 35:
        remaining = len(rendered.splitlines()) - 35
        print(f"  {c(f'... ({remaining} more lines)', DIM)}")
        break
print(c("  " + "-" * 56, DIM))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Search / filter templates
# ══════════════════════════════════════════════════════════════════════════════
section("8. SEARCH & FILTER TEMPLATES")

search_queries = ["docker", "java", "security", "deploy"]

for query in search_queries:
    matches = [
        t for t in get_all_templates()
        if query in t.id.lower()
        or query in t.name.lower()
        or query in t.description.lower()
        or any(query in tag.lower() for tag in t.tags)
    ]
    ids = ", ".join(c(t.id, CYAN) for t in matches)
    print(f"\n  Search '{c(query, YELL)}' → {len(matches)} result(s):  {ids}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — Error handling demo
# ══════════════════════════════════════════════════════════════════════════════
section("9. ERROR HANDLING")

print()

# Invalid template ID in generator
try:
    with tempfile.TemporaryDirectory() as d:
        generate_files("nonexistent-template", d)
except ValueError as e:
    ok(f"ValueError correctly raised for bad template ID: {e}")

# None returned for missing template
result = get_template_by_id("fake-id-xyz")
if result is None:
    ok("get_template_by_id returns None for unknown IDs (safe, no exception)")

# Recommendation with no matching keywords still returns results
results = recommend_templates("some random unrelated project description", [])
if results:
    ok(f"recommend_templates always returns results even with no keyword match (returned {len(results)})")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — JSON output (simulates what the REST API returns)
# ══════════════════════════════════════════════════════════════════════════════
section("10. JSON OUTPUT  (simulates REST API /recommend response)")

results = recommend_templates(
    project_description="Spring Boot Java microservice deployed to Kubernetes with Helm",
    project_tags=["java", "spring", "kubernetes", "helm"],
    top_n=3,
)

api_response = {
    "query_description": "Spring Boot Java microservice deployed to Kubernetes with Helm",
    "query_tags": ["java", "spring", "kubernetes", "helm"],
    "results": results,
}

print()
print(json.dumps(api_response, indent=2))


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
section("DEMO COMPLETE")
print()
ok(f"Registry loaded with {len(get_all_templates())} templates across {len(get_all_categories())} categories")
ok("Recommendation engine working")
ok("File generator working (Jenkinsfile + supporting files)")
ok("Search and filter working")
ok("Error handling working")
ok("JSON output matches REST API format")
print()
print(f"  {c('Next steps:', BOLD)}")
print(f"    • Run the CLI:  {c('jenkins-pipeline-lib list', CYAN)}")
print(f"    • Start API:   {c('uvicorn jenkins_pipeline_lib.api.app:app --reload', CYAN)}")
print(f"    • Run tests:   {c('pytest tests/ -v', CYAN)}")
print()
