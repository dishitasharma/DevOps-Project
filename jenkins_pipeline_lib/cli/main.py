"""
Jenkins Pipeline Template Library - CLI Tool
Usage: jenkins-pipeline-lib <command> [options]
"""

import argparse
import json
import sys
import os
from pathlib import Path

from jenkins_pipeline_lib.core.registry import (
    get_all_templates,
    get_template_by_id,
    get_all_categories,
    get_templates_by_category,
)
from jenkins_pipeline_lib.core.scorer import recommend_templates
from jenkins_pipeline_lib.core.generator import generate_files


# ─── ANSI colours ──────────────────────────────────────────────────────────────
BOLD   = "\033[1m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
DIM    = "\033[2m"


def _color(text: str, *codes: str) -> str:
    if not sys.stdout.isatty():
        return text
    return "".join(codes) + text + RESET


def _header(text: str) -> None:
    width = 60
    print()
    print(_color("─" * width, CYAN))
    print(_color(f"  {text}", BOLD + CYAN))
    print(_color("─" * width, CYAN))


def _success(msg: str) -> None:
    print(_color(f"  ✔  {msg}", GREEN))


def _warn(msg: str) -> None:
    print(_color(f"  ⚠  {msg}", YELLOW))


def _error(msg: str) -> None:
    print(_color(f"  ✖  {msg}", RED), file=sys.stderr)


def _badge(text: str, colour: str = CYAN) -> str:
    return _color(f"[{text}]", colour)


# ─── Command handlers ──────────────────────────────────────────────────────────

def cmd_list(args: argparse.Namespace) -> None:
    """List all available Jenkins pipeline templates."""
    templates = get_all_templates()

    if args.category:
        templates = [t for t in templates if t.category == args.category]
        if not templates:
            _warn(f"No templates found for category '{args.category}'")
            return

    _header(f"Jenkins Pipeline Templates ({len(templates)} total)")

    category_order: dict = {}
    for t in templates:
        category_order.setdefault(t.category, []).append(t)

    for cat, items in sorted(category_order.items()):
        print(f"\n  {_color(cat.upper(), BOLD + YELLOW)}")
        for t in items:
            complexity_colour = {
                "simple": GREEN, "moderate": YELLOW, "advanced": RED
            }.get(t.complexity, CYAN)
            print(
                f"    {_color(t.id, CYAN):<35} "
                f"{_badge(t.complexity, complexity_colour):<20} "
                f"{DIM}{t.description[:60]}...{RESET}"
                if len(t.description) > 60
                else f"    {_color(t.id, CYAN):<35} {_badge(t.complexity, complexity_colour):<20} {DIM}{t.description}{RESET}"
            )

    if args.json:
        data = [
            {"id": t.id, "name": t.name, "category": t.category, "complexity": t.complexity}
            for t in templates
        ]
        print("\n" + json.dumps(data, indent=2))


def cmd_info(args: argparse.Namespace) -> None:
    """Show detailed info about a template."""
    t = get_template_by_id(args.template_id)
    if not t:
        _error(f"Template '{args.template_id}' not found. Run 'list' to see all templates.")
        sys.exit(1)

    _header(f"Template: {t.name}")
    print(f"\n  {_color('ID:', BOLD)}          {t.id}")
    print(f"  {_color('Category:', BOLD)}    {t.category}")
    print(f"  {_color('Complexity:', BOLD)}  {t.complexity}")
    print(f"  {_color('Description:', BOLD)}\n    {t.description}")

    print(f"\n  {_color('Tags:', BOLD)}")
    print("    " + "  ".join(_badge(tag) for tag in t.tags))

    print(f"\n  {_color('Parameters:', BOLD)}")
    for k, v in t.parameters.items():
        print(f"    {_color(k, YELLOW):<35} default: {_color(v or '<empty>', DIM)}")

    print(f"\n  {_color('Use Cases:', BOLD)}")
    for uc in t.use_cases:
        print(f"    • {uc}")

    print(f"\n  {_color('Requirements:', BOLD)}")
    for req in t.requirements:
        print(f"    • {req}")

    if args.json:
        import dataclasses
        print("\n" + json.dumps(dataclasses.asdict(t), indent=2))


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate Jenkinsfile and supporting files from a template."""
    t = get_template_by_id(args.template_id)
    if not t:
        _error(f"Template '{args.template_id}' not found.")
        sys.exit(1)

    output_dir = args.output or os.getcwd()

    # Parse param overrides: KEY=VALUE
    params = {}
    if args.param:
        for p in args.param:
            if "=" not in p:
                _error(f"Invalid param '{p}'. Use KEY=VALUE format.")
                sys.exit(1)
            k, v = p.split("=", 1)
            params[k] = v

    _header(f"Generating: {t.name}")
    print(f"  Output dir: {_color(output_dir, CYAN)}")
    if params:
        print(f"  Overrides:  {params}")

    written = generate_files(args.template_id, output_dir, params)

    print()
    for rel, full in written.items():
        _success(f"Created  {rel}")

    print()
    print(_color(f"  Generated {len(written)} files in {output_dir}", GREEN + BOLD))
    print()
    print(f"  {DIM}Next steps:{RESET}")
    print(f"    1. Review and customise {_color('Jenkinsfile', CYAN)}")
    print(f"    2. Commit to your repository")
    print(f"    3. Configure Jenkins credentials as noted in the Jenkinsfile")


def cmd_recommend(args: argparse.Namespace) -> None:
    """Recommend best templates for a project."""
    tags = args.tag or []
    description = args.description or ""

    if not description and not tags:
        _error("Provide at least --description or --tag to get recommendations.")
        sys.exit(1)

    _header("Template Recommendations")
    print(f"  Description: {description or '(none)'}")
    print(f"  Tags:        {', '.join(tags) or '(none)'}")

    results = recommend_templates(description, tags, top_n=args.top or 3)

    if not results:
        _warn("No matching templates found.")
        return

    print()
    for r in results:
        score_pct = int(r["score"] * 100)
        bar = ("█" * (score_pct // 5)).ljust(20)
        score_colour = GREEN if score_pct >= 60 else YELLOW if score_pct >= 30 else RED
        print(
            f"  {_color(str(r['rank']) + '.', BOLD)} "
            f"{_color(r['id'], CYAN):<35} "
            f"{_color(bar, score_colour)} {score_pct:>3}%"
        )
        print(f"     {DIM}{r['description'][:70]}{RESET}")
        if r["matched_keywords"]:
            print(f"     Matched: {', '.join(_badge(k, GREEN) for k in r['matched_keywords'])}")
        print()

    best = results[0]
    print(_color(f"  ★ Best match: jenkins-pipeline-lib generate {best['id']} --output .", BOLD + GREEN))

    if args.json:
        print("\n" + json.dumps(results, indent=2))


def cmd_categories(args: argparse.Namespace) -> None:
    """List all template categories."""
    cats = get_all_categories()
    _header("Template Categories")
    for cat in cats:
        items = get_templates_by_category(cat)
        print(f"  {_color(cat, CYAN):<20} {len(items)} template(s)")


def cmd_search(args: argparse.Namespace) -> None:
    """Search templates by keyword."""
    query = args.query.lower()
    results = [
        t for t in get_all_templates()
        if query in t.id.lower()
        or query in t.name.lower()
        or query in t.description.lower()
        or any(query in tag.lower() for tag in t.tags)
    ]

    _header(f"Search: '{args.query}' — {len(results)} result(s)")
    if not results:
        _warn("No templates matched your query.")
        return

    for t in results:
        print(f"  {_color(t.id, CYAN):<35} {DIM}{t.description[:65]}{RESET}")


# ─── Main ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jenkins-pipeline-lib",
        description=_color("Jenkins Pipeline Template Library CLI", BOLD),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  jenkins-pipeline-lib list\n"
            "  jenkins-pipeline-lib list --category ci\n"
            "  jenkins-pipeline-lib info python-ci\n"
            "  jenkins-pipeline-lib generate python-ci --output ./my-project\n"
            "  jenkins-pipeline-lib generate python-ci --param PYTHON_VERSION=3.12\n"
            "  jenkins-pipeline-lib recommend --description 'Node.js API' --tag docker\n"
            "  jenkins-pipeline-lib search docker\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="command")

    # list
    p_list = sub.add_parser("list", help="List all available pipeline templates")
    p_list.add_argument("--category", "-c", help="Filter by category")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")
    p_list.set_defaults(func=cmd_list)

    # info
    p_info = sub.add_parser("info", help="Show details about a template")
    p_info.add_argument("template_id", help="Template ID (e.g. python-ci)")
    p_info.add_argument("--json", action="store_true", help="Output as JSON")
    p_info.set_defaults(func=cmd_info)

    # generate
    p_gen = sub.add_parser("generate", help="Generate Jenkinsfile + files from a template")
    p_gen.add_argument("template_id", help="Template ID (e.g. python-ci)")
    p_gen.add_argument("--output", "-o", help="Output directory (default: current directory)")
    p_gen.add_argument("--param", "-p", action="append",
                        help="Override parameter: KEY=VALUE (repeatable)")
    p_gen.set_defaults(func=cmd_generate)

    # recommend
    p_rec = sub.add_parser("recommend", help="Recommend templates for your project")
    p_rec.add_argument("--description", "-d", help="Project description")
    p_rec.add_argument("--tag", "-t", action="append", help="Project tags (repeatable)")
    p_rec.add_argument("--top", type=int, default=3, help="Number of recommendations (default 3)")
    p_rec.add_argument("--json", action="store_true", help="Output as JSON")
    p_rec.set_defaults(func=cmd_recommend)

    # categories
    p_cat = sub.add_parser("categories", help="List all template categories")
    p_cat.set_defaults(func=cmd_categories)

    # search
    p_srch = sub.add_parser("search", help="Search templates by keyword")
    p_srch.add_argument("query", help="Search term")
    p_srch.set_defaults(func=cmd_search)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
