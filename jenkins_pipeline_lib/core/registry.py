"""Central registry for all Jenkins pipeline templates."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class TemplateMetadata:
    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    parameters: Dict[str, str]
    use_cases: List[str]
    complexity: str  # simple | moderate | advanced
    requirements: List[str] = field(default_factory=list)
    score_keywords: List[str] = field(default_factory=list)


TEMPLATE_REGISTRY: List[TemplateMetadata] = [
    TemplateMetadata(
        id="python-ci",
        name="Python CI Pipeline",
        description="Full CI pipeline for Python projects: lint, test, coverage, package.",
        category="ci",
        tags=["python", "pytest", "flake8", "pip", "coverage"],
        parameters={
            "PYTHON_VERSION": "3.11",
            "TEST_DIR": "tests/",
            "COVERAGE_THRESHOLD": "80",
        },
        use_cases=["Python web apps", "Python microservices", "Python libraries"],
        complexity="moderate",
        requirements=["Python", "pip"],
        score_keywords=["python", "django", "flask", "fastapi", "pytest", "pip"],
    ),
    TemplateMetadata(
        id="nodejs-ci",
        name="Node.js CI Pipeline",
        description="CI pipeline for Node.js apps: install, lint, test, build.",
        category="ci",
        tags=["nodejs", "npm", "jest", "eslint"],
        parameters={
            "NODE_VERSION": "18",
            "PACKAGE_MANAGER": "npm",
            "BUILD_CMD": "npm run build",
        },
        use_cases=["Node.js APIs", "React/Vue/Angular apps", "NPM packages"],
        complexity="moderate",
        requirements=["Node.js", "npm or yarn"],
        score_keywords=["node", "nodejs", "npm", "yarn", "react", "vue", "angular", "javascript", "typescript"],
    ),
    TemplateMetadata(
        id="java-maven-ci",
        name="Java Maven CI Pipeline",
        description="CI pipeline for Java Maven projects: compile, test, package, SonarQube.",
        category="ci",
        tags=["java", "maven", "junit", "sonarqube"],
        parameters={
            "JAVA_VERSION": "17",
            "MAVEN_OPTS": "-Xmx1024m",
            "SONAR_HOST": "",
        },
        use_cases=["Spring Boot apps", "Java microservices", "Java libraries"],
        complexity="moderate",
        requirements=["Java JDK", "Maven"],
        score_keywords=["java", "maven", "spring", "springboot", "junit", "gradle"],
    ),
    TemplateMetadata(
        id="java-gradle-ci",
        name="Java Gradle CI Pipeline",
        description="CI pipeline for Java Gradle projects with build caching.",
        category="ci",
        tags=["java", "gradle", "junit"],
        parameters={
            "JAVA_VERSION": "17",
            "GRADLE_OPTS": "--no-daemon",
        },
        use_cases=["Android projects", "Gradle-based Java apps"],
        complexity="moderate",
        requirements=["Java JDK", "Gradle"],
        score_keywords=["gradle", "android", "kotlin"],
    ),
    TemplateMetadata(
        id="docker-build-push",
        name="Docker Build & Push Pipeline",
        description="Build Docker image, run security scan, and push to registry.",
        category="docker",
        tags=["docker", "registry", "trivy", "container"],
        parameters={
            "DOCKER_REGISTRY": "docker.io",
            "IMAGE_NAME": "my-app",
            "DOCKERFILE_PATH": "Dockerfile",
        },
        use_cases=["Containerized apps", "Microservices", "Any Dockerfile project"],
        complexity="simple",
        requirements=["Docker", "Registry credentials"],
        score_keywords=["docker", "container", "dockerfile", "image", "registry", "dockerhub", "ecr", "gcr"],
    ),
    TemplateMetadata(
        id="kubernetes-deploy",
        name="Kubernetes Deployment Pipeline",
        description="Deploy application to Kubernetes cluster with rolling updates and rollback.",
        category="deployment",
        tags=["kubernetes", "kubectl", "helm", "k8s"],
        parameters={
            "K8S_NAMESPACE": "default",
            "DEPLOYMENT_NAME": "my-app",
            "HELM_CHART_PATH": "./helm",
            "KUBECONFIG_CREDENTIAL": "kubeconfig",
        },
        use_cases=["K8s workloads", "Helm chart deployments", "Cloud-native apps"],
        complexity="advanced",
        requirements=["kubectl", "Helm (optional)", "K8s cluster access"],
        score_keywords=["kubernetes", "k8s", "kubectl", "helm", "eks", "gke", "aks", "pod"],
    ),
    TemplateMetadata(
        id="terraform-iac",
        name="Terraform Infrastructure Pipeline",
        description="Terraform plan, validate, apply pipeline with state management and approval gate.",
        category="infrastructure",
        tags=["terraform", "iac", "aws", "azure", "gcp"],
        parameters={
            "TF_WORKSPACE": "default",
            "TF_VAR_FILE": "terraform.tfvars",
            "AWS_REGION": "us-east-1",
        },
        use_cases=["Cloud infrastructure provisioning", "IaC workflows"],
        complexity="advanced",
        requirements=["Terraform CLI", "Cloud provider credentials"],
        score_keywords=["terraform", "infrastructure", "iac", "aws", "azure", "gcp", "cloud"],
    ),
    TemplateMetadata(
        id="ansible-deploy",
        name="Ansible Deployment Pipeline",
        description="Run Ansible playbooks for server configuration and application deployment.",
        category="deployment",
        tags=["ansible", "playbook", "configuration-management"],
        parameters={
            "ANSIBLE_PLAYBOOK": "deploy.yml",
            "INVENTORY_FILE": "inventory/hosts",
            "ANSIBLE_VAULT_CREDENTIAL": "",
        },
        use_cases=["Server configuration", "App deployment to VMs", "Configuration management"],
        complexity="moderate",
        requirements=["Ansible CLI", "SSH access to targets"],
        score_keywords=["ansible", "playbook", "configuration", "vm", "server"],
    ),
    TemplateMetadata(
        id="microservices-ci-cd",
        name="Microservices CI/CD Pipeline",
        description="Monorepo-aware pipeline detecting changed services and running per-service CI/CD.",
        category="ci-cd",
        tags=["microservices", "monorepo", "docker", "kubernetes"],
        parameters={
            "SERVICES_DIR": "services/",
            "DOCKER_REGISTRY": "docker.io",
            "K8S_NAMESPACE": "production",
        },
        use_cases=["Monorepo microservices", "Independent service deployments"],
        complexity="advanced",
        requirements=["Docker", "kubectl", "Git"],
        score_keywords=["microservices", "monorepo", "services", "independent deploy"],
    ),
    TemplateMetadata(
        id="static-site-deploy",
        name="Static Site Deployment Pipeline",
        description="Build and deploy static sites to S3/CloudFront, Netlify, or GitHub Pages.",
        category="deployment",
        tags=["static", "s3", "cloudfront", "cdn", "netlify"],
        parameters={
            "BUILD_CMD": "npm run build",
            "BUILD_DIR": "dist/",
            "S3_BUCKET": "",
            "CDN_DISTRIBUTION_ID": "",
        },
        use_cases=["React/Vue/Angular SPA", "Hugo/Jekyll sites", "Static documentation"],
        complexity="simple",
        requirements=["Node.js (or build tool)", "AWS CLI or Netlify CLI"],
        score_keywords=["static", "s3", "spa", "gatsby", "hugo", "jekyll", "nextjs", "nuxt"],
    ),
    TemplateMetadata(
        id="database-migration",
        name="Database Migration Pipeline",
        description="Run database migrations safely with pre/post validation and rollback support.",
        category="database",
        tags=["database", "migration", "flyway", "liquibase", "sql"],
        parameters={
            "DB_URL": "",
            "MIGRATION_TOOL": "flyway",
            "MIGRATION_DIR": "db/migrations",
        },
        use_cases=["SQL schema migrations", "Flyway/Liquibase workflows", "DB version control"],
        complexity="moderate",
        requirements=["Flyway or Liquibase", "DB credentials"],
        score_keywords=["database", "migration", "flyway", "liquibase", "sql", "postgres", "mysql"],
    ),
    TemplateMetadata(
        id="security-scan",
        name="Security Scanning Pipeline",
        description="SAST, DAST, dependency vulnerability scanning with OWASP and Trivy.",
        category="security",
        tags=["security", "owasp", "trivy", "sast", "dast", "snyk"],
        parameters={
            "SCAN_TARGET": "",
            "SEVERITY_THRESHOLD": "HIGH",
            "REPORT_FORMAT": "html",
        },
        use_cases=["Security audits", "Compliance pipelines", "DevSecOps workflows"],
        complexity="advanced",
        requirements=["OWASP ZAP / Trivy / Snyk CLI"],
        score_keywords=["security", "owasp", "sast", "dast", "vulnerability", "compliance", "devsecops"],
    ),
    TemplateMetadata(
        id="release-management",
        name="Release Management Pipeline",
        description="Semantic versioning, changelog generation, GitHub/GitLab release creation.",
        category="release",
        tags=["release", "semver", "changelog", "git-tag"],
        parameters={
            "VERSION_STRATEGY": "semver",
            "CHANGELOG_FILE": "CHANGELOG.md",
            "GIT_CREDENTIAL": "github-token",
        },
        use_cases=["Library releases", "Versioned API releases", "Open source projects"],
        complexity="moderate",
        requirements=["Git", "GitHub/GitLab token"],
        score_keywords=["release", "version", "semver", "changelog", "tag", "publish"],
    ),
    TemplateMetadata(
        id="multi-branch-pipeline",
        name="Multi-Branch Pipeline",
        description="Branch-aware CI with different behaviors for feature, develop, and main branches.",
        category="ci",
        tags=["multibranch", "gitflow", "feature-branch"],
        parameters={
            "MAIN_BRANCH": "main",
            "DEVELOP_BRANCH": "develop",
            "DEPLOY_ON_MAIN": "true",
        },
        use_cases=["GitFlow workflows", "Feature branch testing", "PR validation"],
        complexity="moderate",
        requirements=["Git branching strategy"],
        score_keywords=["branch", "gitflow", "feature", "pull request", "pr", "merge"],
    ),
    TemplateMetadata(
        id="performance-test",
        name="Performance Testing Pipeline",
        description="Run load/performance tests with JMeter or k6 and publish results.",
        category="testing",
        tags=["performance", "load-test", "jmeter", "k6", "gatling"],
        parameters={
            "TEST_TOOL": "k6",
            "SCRIPT_PATH": "tests/load/script.js",
            "VIRTUAL_USERS": "100",
            "DURATION": "5m",
        },
        use_cases=["API load testing", "Stress testing", "Performance regression detection"],
        complexity="moderate",
        requirements=["k6 or JMeter or Gatling"],
        score_keywords=["performance", "load", "stress", "jmeter", "k6", "gatling"],
    ),
]

TEMPLATE_MAP: Dict[str, TemplateMetadata] = {t.id: t for t in TEMPLATE_REGISTRY}


def get_all_templates() -> List[TemplateMetadata]:
    return TEMPLATE_REGISTRY


def get_template_by_id(template_id: str) -> Optional[TemplateMetadata]:
    return TEMPLATE_MAP.get(template_id)


def get_templates_by_category(category: str) -> List[TemplateMetadata]:
    return [t for t in TEMPLATE_REGISTRY if t.category == category]


def get_all_categories() -> List[str]:
    return sorted(set(t.category for t in TEMPLATE_REGISTRY))
