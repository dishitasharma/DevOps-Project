"""Generates Jenkinsfile and supporting project files from templates."""

import os
from pathlib import Path
from typing import Dict, Optional
from jenkins_pipeline_lib.core.registry import get_template_by_id, TemplateMetadata

# ──────────────────────────────────────────────
#  Raw Jenkinsfile templates
# ──────────────────────────────────────────────

JENKINSFILES: Dict[str, str] = {

"python-ci": '''\
pipeline {{
    agent any

    environment {{
        PYTHON_VERSION = '{PYTHON_VERSION}'
        TEST_DIR       = '{TEST_DIR}'
        COVERAGE_THRESHOLD = '{COVERAGE_THRESHOLD}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}

        stage('Setup Python') {{
            steps {{
                sh """
                    python${{PYTHON_VERSION}} -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install flake8 pytest pytest-cov
                """
            }}
        }}

        stage('Lint') {{
            steps {{
                sh '. venv/bin/activate && flake8 . --max-line-length=120 --exclude=venv'
            }}
        }}

        stage('Test') {{
            steps {{
                sh ". venv/bin/activate && pytest ${{TEST_DIR}} --cov=. --cov-report=xml --cov-fail-under=${{COVERAGE_THRESHOLD}} -v"
            }}
            post {{
                always {{
                    junit 'test-results/*.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }}
            }}
        }}

        stage('Package') {{
            when {{ branch 'main' }}
            steps {{
                sh '. venv/bin/activate && python setup.py sdist bdist_wheel'
            }}
        }}
    }}

    post {{
        always {{
            cleanWs()
        }}
        failure {{
            mail to: '${{NOTIFY_EMAIL}}',
                 subject: "FAILED: ${{env.JOB_NAME}} [${{env.BUILD_NUMBER}}]",
                 body: "Check console: ${{env.BUILD_URL}}"
        }}
    }}
}}
''',

"nodejs-ci": '''\
pipeline {{
    agent any

    tools {{
        nodejs 'NodeJS-{NODE_VERSION}'
    }}

    environment {{
        NODE_VERSION   = '{NODE_VERSION}'
        PACKAGE_MANAGER = '{PACKAGE_MANAGER}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Install Dependencies') {{
            steps {{
                sh '${{PACKAGE_MANAGER}} install --frozen-lockfile'
            }}
        }}

        stage('Lint') {{
            steps {{
                sh '${{PACKAGE_MANAGER}} run lint'
            }}
        }}

        stage('Test') {{
            steps {{
                sh '${{PACKAGE_MANAGER}} run test -- --coverage --reporters=junit'
            }}
            post {{
                always {{
                    junit 'test-results/junit.xml'
                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: true,
                                 keepAll: true, reportDir: 'coverage',
                                 reportFiles: 'index.html', reportName: 'Coverage Report'])
                }}
            }}
        }}

        stage('Build') {{
            steps {{
                sh '{BUILD_CMD}'
            }}
        }}

        stage('Archive') {{
            when {{ branch 'main' }}
            steps {{
                archiveArtifacts artifacts: 'dist/**', fingerprint: true
            }}
        }}
    }}

    post {{
        always {{ cleanWs() }}
    }}
}}
''',

"java-maven-ci": '''\
pipeline {{
    agent any

    tools {{
        jdk  'JDK-{JAVA_VERSION}'
        maven 'Maven-3.9'
    }}

    environment {{
        JAVA_VERSION = '{JAVA_VERSION}'
        MAVEN_OPTS   = '{MAVEN_OPTS}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Compile') {{
            steps {{ sh 'mvn clean compile -B' }}
        }}

        stage('Test') {{
            steps {{ sh 'mvn test -B' }}
            post {{
                always {{
                    junit '**/target/surefire-reports/*.xml'
                    jacoco execPattern: '**/target/jacoco.exec'
                }}
            }}
        }}

        stage('SonarQube Analysis') {{
            when {{ expression {{ return env.SONAR_HOST?.trim() }} }}
            steps {{
                withSonarQubeEnv('SonarQube') {{
                    sh 'mvn sonar:sonar -B'
                }}
            }}
        }}

        stage('Package') {{
            steps {{ sh 'mvn package -DskipTests -B' }}
            post {{
                success {{
                    archiveArtifacts artifacts: '**/target/*.jar', fingerprint: true
                }}
            }}
        }}
    }}

    post {{
        always {{ cleanWs() }}
    }}
}}
''',

"java-gradle-ci": '''\
pipeline {{
    agent any

    tools {{
        jdk 'JDK-{JAVA_VERSION}'
    }}

    environment {{
        GRADLE_OPTS = '{GRADLE_OPTS}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Build & Test') {{
            steps {{
                sh './gradlew clean build ${{GRADLE_OPTS}}'
            }}
            post {{
                always {{
                    junit '**/build/test-results/**/*.xml'
                    publishHTML([reportDir: 'build/reports/tests/test',
                                 reportFiles: 'index.html', reportName: 'Test Report'])
                }}
            }}
        }}

        stage('Package') {{
            when {{ branch 'main' }}
            steps {{
                sh './gradlew jar ${{GRADLE_OPTS}}'
                archiveArtifacts artifacts: 'build/libs/*.jar', fingerprint: true
            }}
        }}
    }}

    post {{
        always {{ cleanWs() }}
    }}
}}
''',

"docker-build-push": '''\
pipeline {{
    agent any

    environment {{
        DOCKER_REGISTRY    = '{DOCKER_REGISTRY}'
        IMAGE_NAME         = '{IMAGE_NAME}'
        DOCKERFILE_PATH    = '{DOCKERFILE_PATH}'
        IMAGE_TAG          = "${{env.BRANCH_NAME}}-${{env.BUILD_NUMBER}}"
        FULL_IMAGE         = "${{DOCKER_REGISTRY}}/${{IMAGE_NAME}}:${{IMAGE_TAG}}"
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Build Image') {{
            steps {{
                sh "docker build -f ${{DOCKERFILE_PATH}} -t ${{FULL_IMAGE}} ."
            }}
        }}

        stage('Security Scan') {{
            steps {{
                sh "trivy image --exit-code 1 --severity HIGH,CRITICAL ${{FULL_IMAGE}}"
            }}
        }}

        stage('Push Image') {{
            when {{ anyOf {{ branch 'main'; branch 'develop' }} }}
            steps {{
                withCredentials([usernamePassword(credentialsId: 'docker-registry-creds',
                                                  usernameVariable: 'DOCKER_USER',
                                                  passwordVariable: 'DOCKER_PASS')]) {{
                    sh """
                        echo $DOCKER_PASS | docker login ${{DOCKER_REGISTRY}} -u $DOCKER_USER --password-stdin
                        docker push ${{FULL_IMAGE}}
                        docker tag ${{FULL_IMAGE}} ${{DOCKER_REGISTRY}}/${{IMAGE_NAME}}:latest
                        docker push ${{DOCKER_REGISTRY}}/${{IMAGE_NAME}}:latest
                    """
                }}
            }}
        }}
    }}

    post {{
        always {{
            sh "docker rmi ${{FULL_IMAGE}} || true"
            cleanWs()
        }}
    }}
}}
''',

"kubernetes-deploy": '''\
pipeline {{
    agent any

    environment {{
        K8S_NAMESPACE   = '{K8S_NAMESPACE}'
        DEPLOYMENT_NAME = '{DEPLOYMENT_NAME}'
        HELM_CHART_PATH = '{HELM_CHART_PATH}'
        KUBECONFIG      = credentials('{KUBECONFIG_CREDENTIAL}')
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Validate Manifests') {{
            steps {{
                sh "kubectl --dry-run=client apply -f ${{HELM_CHART_PATH}}"
            }}
        }}

        stage('Deploy') {{
            steps {{
                sh """
                    helm upgrade --install ${{DEPLOYMENT_NAME}} ${{HELM_CHART_PATH}} \\
                        --namespace ${{K8S_NAMESPACE}} \\
                        --create-namespace \\
                        --wait --timeout=5m \\
                        --set image.tag=${{env.BUILD_NUMBER}}
                """
            }}
        }}

        stage('Verify Rollout') {{
            steps {{
                sh "kubectl rollout status deployment/${{DEPLOYMENT_NAME}} -n ${{K8S_NAMESPACE}} --timeout=3m"
            }}
        }}
    }}

    post {{
        failure {{
            sh "helm rollback ${{DEPLOYMENT_NAME}} --namespace ${{K8S_NAMESPACE}} || true"
        }}
        always {{ cleanWs() }}
    }}
}}
''',

"terraform-iac": '''\
pipeline {{
    agent any

    environment {{
        TF_WORKSPACE  = '{TF_WORKSPACE}'
        TF_VAR_FILE   = '{TF_VAR_FILE}'
        AWS_REGION    = '{AWS_REGION}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Terraform Init') {{
            steps {{
                sh 'terraform init -backend=true'
                sh "terraform workspace select ${{TF_WORKSPACE}} || terraform workspace new ${{TF_WORKSPACE}}"
            }}
        }}

        stage('Terraform Validate') {{
            steps {{
                sh 'terraform validate'
                sh 'terraform fmt -check'
            }}
        }}

        stage('Terraform Plan') {{
            steps {{
                sh "terraform plan -var-file=${{TF_VAR_FILE}} -out=tfplan"
                sh 'terraform show -no-color tfplan > plan.txt'
                archiveArtifacts artifacts: 'plan.txt', fingerprint: true
            }}
        }}

        stage('Approval') {{
            when {{ branch 'main' }}
            steps {{
                input message: 'Apply Terraform changes?', ok: 'Apply'
            }}
        }}

        stage('Terraform Apply') {{
            when {{ branch 'main' }}
            steps {{
                sh 'terraform apply -auto-approve tfplan'
            }}
        }}
    }}

    post {{
        always {{ cleanWs() }}
    }}
}}
''',

"ansible-deploy": '''\
pipeline {{
    agent any

    environment {{
        ANSIBLE_PLAYBOOK         = '{ANSIBLE_PLAYBOOK}'
        INVENTORY_FILE           = '{INVENTORY_FILE}'
        ANSIBLE_FORCE_COLOR      = '1'
        ANSIBLE_HOST_KEY_CHECKING = 'False'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Syntax Check') {{
            steps {{
                sh "ansible-playbook ${{ANSIBLE_PLAYBOOK}} --syntax-check -i ${{INVENTORY_FILE}}"
            }}
        }}

        stage('Dry Run') {{
            steps {{
                sh "ansible-playbook ${{ANSIBLE_PLAYBOOK}} --check -i ${{INVENTORY_FILE}}"
            }}
        }}

        stage('Deploy') {{
            when {{ branch 'main' }}
            steps {{
                withCredentials([string(credentialsId: 'ansible-vault-pass', variable: 'VAULT_PASS')]) {{
                    sh """
                        echo "$VAULT_PASS" > .vault_pass
                        ansible-playbook ${{ANSIBLE_PLAYBOOK}} -i ${{INVENTORY_FILE}} \\
                            --vault-password-file=.vault_pass
                        rm -f .vault_pass
                    """
                }}
            }}
        }}
    }}

    post {{
        always {{
            sh 'rm -f .vault_pass || true'
            cleanWs()
        }}
    }}
}}
''',

"microservices-ci-cd": '''\
pipeline {{
    agent any

    environment {{
        SERVICES_DIR    = '{SERVICES_DIR}'
        DOCKER_REGISTRY = '{DOCKER_REGISTRY}'
        K8S_NAMESPACE   = '{K8S_NAMESPACE}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Detect Changed Services') {{
            steps {{
                script {{
                    def changedFiles = sh(
                        script: "git diff --name-only HEAD~1 HEAD",
                        returnStdout: true
                    ).trim().split('\\n')
                    env.CHANGED_SERVICES = changedFiles
                        .findAll {{ it.startsWith(SERVICES_DIR) }}
                        .collect {{ it.split('/')[1] }}
                        .unique()
                        .join(',')
                    echo "Changed services: ${{env.CHANGED_SERVICES}}"
                }}
            }}
        }}

        stage('Build & Test Services') {{
            steps {{
                script {{
                    def services = env.CHANGED_SERVICES.split(',')
                    services.each {{ svc ->
                        dir("${{SERVICES_DIR}}/${{svc}}") {{
                            sh "docker build -t ${{DOCKER_REGISTRY}}/${{svc}}:${{env.BUILD_NUMBER}} ."
                            sh "docker run --rm ${{DOCKER_REGISTRY}}/${{svc}}:${{env.BUILD_NUMBER}} npm test || true"
                        }}
                    }}
                }}
            }}
        }}

        stage('Push Images') {{
            when {{ branch 'main' }}
            steps {{
                script {{
                    def services = env.CHANGED_SERVICES.split(',')
                    services.each {{ svc ->
                        sh "docker push ${{DOCKER_REGISTRY}}/${{svc}}:${{env.BUILD_NUMBER}}"
                    }}
                }}
            }}
        }}

        stage('Deploy to K8s') {{
            when {{ branch 'main' }}
            steps {{
                script {{
                    def services = env.CHANGED_SERVICES.split(',')
                    services.each {{ svc ->
                        sh """
                            kubectl set image deployment/${{svc}} \\
                                ${{svc}}=${{DOCKER_REGISTRY}}/${{svc}}:${{env.BUILD_NUMBER}} \\
                                -n ${{K8S_NAMESPACE}}
                        """
                    }}
                }}
            }}
        }}
    }}

    post {{
        always {{ cleanWs() }}
    }}
}}
''',

"static-site-deploy": '''\
pipeline {{
    agent any

    environment {{
        BUILD_CMD            = '{BUILD_CMD}'
        BUILD_DIR            = '{BUILD_DIR}'
        S3_BUCKET            = '{S3_BUCKET}'
        CDN_DISTRIBUTION_ID  = '{CDN_DISTRIBUTION_ID}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Install') {{
            steps {{ sh 'npm ci' }}
        }}

        stage('Build') {{
            steps {{ sh '${{BUILD_CMD}}' }}
        }}

        stage('Deploy to S3') {{
            when {{ branch 'main' }}
            steps {{
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-credentials'
                ]]) {{
                    sh """
                        aws s3 sync ${{BUILD_DIR}} s3://${{S3_BUCKET}} --delete
                        aws cloudfront create-invalidation \\
                            --distribution-id ${{CDN_DISTRIBUTION_ID}} \\
                            --paths "/*"
                    """
                }}
            }}
        }}
    }}

    post {{
        always {{ cleanWs() }}
    }}
}}
''',

"database-migration": '''\
pipeline {{
    agent any

    environment {{
        DB_URL        = '{DB_URL}'
        MIGRATION_DIR = '{MIGRATION_DIR}'
        TOOL          = '{MIGRATION_TOOL}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Validate Migrations') {{
            steps {{
                sh "${{TOOL}} validate -url=${{DB_URL}} -locations=filesystem:${{MIGRATION_DIR}}"
            }}
        }}

        stage('Migration Info') {{
            steps {{
                sh "${{TOOL}} info -url=${{DB_URL}} -locations=filesystem:${{MIGRATION_DIR}}"
            }}
        }}

        stage('Run Migrations') {{
            when {{ branch 'main' }}
            steps {{
                input message: 'Proceed with database migration?', ok: 'Migrate'
                withCredentials([usernamePassword(credentialsId: 'db-credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {{
                    sh "${{TOOL}} migrate -url=${{DB_URL}} -user=$DB_USER -password=$DB_PASS -locations=filesystem:${{MIGRATION_DIR}}"
                }}
            }}
        }}
    }}

    post {{
        failure {{
            sh "${{TOOL}} repair -url=${{DB_URL}} -locations=filesystem:${{MIGRATION_DIR}} || true"
        }}
        always {{ cleanWs() }}
    }}
}}
''',

"security-scan": '''\
pipeline {{
    agent any

    environment {{
        SCAN_TARGET        = '{SCAN_TARGET}'
        SEVERITY_THRESHOLD = '{SEVERITY_THRESHOLD}'
        REPORT_FORMAT      = '{REPORT_FORMAT}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Dependency Scan') {{
            steps {{
                sh "trivy fs --exit-code 0 --severity ${{SEVERITY_THRESHOLD}} --format ${{REPORT_FORMAT}} -o dep-report.${{REPORT_FORMAT}} ."
            }}
        }}

        stage('SAST Scan') {{
            steps {{
                sh "semgrep --config=auto --json --output=sast-report.json . || true"
            }}
        }}

        stage('Container Scan') {{
            when {{ expression {{ return env.SCAN_TARGET?.trim() }} }}
            steps {{
                sh "trivy image --exit-code 1 --severity ${{SEVERITY_THRESHOLD}} ${{SCAN_TARGET}}"
            }}
        }}

        stage('OWASP ZAP Scan') {{
            steps {{
                sh """
                    docker run --rm -v ${{WORKSPACE}}:/zap/wrk \\
                        owasp/zap2docker-stable zap-baseline.py \\
                        -t ${{SCAN_TARGET}} -r zap-report.html || true
                """
            }}
        }}

        stage('Publish Reports') {{
            steps {{
                publishHTML([allowMissing: true, reportDir: '.', reportFiles: 'zap-report.html',
                             reportName: 'ZAP Security Report'])
                archiveArtifacts artifacts: '*-report.*', fingerprint: true
            }}
        }}
    }}

    post {{
        always {{ cleanWs() }}
    }}
}}
''',

"release-management": '''\
pipeline {{
    agent any

    environment {{
        VERSION_STRATEGY = '{VERSION_STRATEGY}'
        CHANGELOG_FILE   = '{CHANGELOG_FILE}'
        GIT_CREDENTIAL   = '{GIT_CREDENTIAL}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
                sh 'git fetch --tags'
            }}
        }}

        stage('Determine Version') {{
            steps {{
                script {{
                    def latestTag = sh(script: "git describe --tags --abbrev=0 2>/dev/null || echo 'v0.0.0'",
                                       returnStdout: true).trim()
                    echo "Latest tag: ${{latestTag}}"
                    env.NEW_VERSION = latestTag  // Replace with semver bump logic
                }}
            }}
        }}

        stage('Generate Changelog') {{
            steps {{
                sh "git log $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD)..HEAD --oneline > /tmp/new_changes.txt"
                sh "cat /tmp/new_changes.txt >> ${{CHANGELOG_FILE}}"
            }}
        }}

        stage('Create Release') {{
            when {{ branch 'main' }}
            steps {{
                withCredentials([string(credentialsId: '${{GIT_CREDENTIAL}}', variable: 'GH_TOKEN')]) {{
                    sh """
                        git config user.email 'jenkins@ci.local'
                        git config user.name 'Jenkins'
                        git tag -a ${{env.NEW_VERSION}} -m "Release ${{env.NEW_VERSION}}"
                        git push origin ${{env.NEW_VERSION}}
                        gh release create ${{env.NEW_VERSION}} --notes-file /tmp/new_changes.txt
                    """
                }}
            }}
        }}
    }}

    post {{
        always {{ cleanWs() }}
    }}
}}
''',

"multi-branch-pipeline": '''\
pipeline {{
    agent any

    environment {{
        MAIN_BRANCH    = '{MAIN_BRANCH}'
        DEVELOP_BRANCH = '{DEVELOP_BRANCH}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Build') {{
            steps {{ sh 'echo "Building branch: ${{env.BRANCH_NAME}}"' }}
        }}

        stage('Unit Tests') {{
            steps {{ sh 'echo "Running unit tests..."' }}
        }}

        stage('Integration Tests') {{
            when {{ anyOf {{ branch '${{DEVELOP_BRANCH}}'; branch '${{MAIN_BRANCH}}' }} }}
            steps {{ sh 'echo "Running integration tests..."' }}
        }}

        stage('Deploy to Staging') {{
            when {{ branch '${{DEVELOP_BRANCH}}' }}
            steps {{ sh 'echo "Deploying to staging..."' }}
        }}

        stage('Deploy to Production') {{
            when {{ branch '${{MAIN_BRANCH}}' }}
            steps {{
                input message: 'Deploy to Production?', ok: 'Deploy'
                sh 'echo "Deploying to production..."'
            }}
        }}
    }}

    post {{
        always {{ cleanWs() }}
        success {{
            echo "Pipeline succeeded on ${{env.BRANCH_NAME}}"
        }}
    }}
}}
''',

"performance-test": '''\
pipeline {{
    agent any

    environment {{
        TEST_TOOL     = '{TEST_TOOL}'
        SCRIPT_PATH   = '{SCRIPT_PATH}'
        VIRTUAL_USERS = '{VIRTUAL_USERS}'
        DURATION      = '{DURATION}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{ checkout scm }}
        }}

        stage('Run Performance Tests') {{
            steps {{
                script {{
                    if (env.TEST_TOOL == 'k6') {{
                        sh "k6 run --vus ${{VIRTUAL_USERS}} --duration ${{DURATION}} --out json=results.json ${{SCRIPT_PATH}}"
                    }} else if (env.TEST_TOOL == 'jmeter') {{
                        sh "jmeter -n -t ${{SCRIPT_PATH}} -l results.jtl -e -o report/"
                    }} else {{
                        sh "gatling.sh -sf ${{SCRIPT_PATH}} -rd 'Performance Test'"
                    }}
                }}
            }}
        }}

        stage('Publish Results') {{
            steps {{
                perfReport 'results.jtl'
                publishHTML([reportDir: 'report', reportFiles: 'index.html',
                             reportName: 'Performance Test Report'])
            }}
        }}

        stage('Threshold Check') {{
            steps {{
                sh 'echo "Checking performance thresholds..."'
            }}
        }}
    }}

    post {{
        always {{
            archiveArtifacts artifacts: 'results.*', fingerprint: true
            cleanWs()
        }}
    }}
}}
''',
}


EXTRA_FILES: Dict[str, Dict[str, str]] = {
    "python-ci": {
        "requirements.txt": "# Add your project dependencies here\nflask\nrequests\n",
        "setup.py": (
            "from setuptools import setup, find_packages\n\n"
            "setup(\n    name='my-python-app',\n    version='1.0.0',\n"
            "    packages=find_packages(),\n)\n"
        ),
        ".flake8": "[flake8]\nmax-line-length = 120\nexclude = venv, .git, __pycache__\n",
        "tests/__init__.py": "",
        "tests/test_sample.py": (
            "def test_sample():\n    assert 1 + 1 == 2\n"
        ),
    },
    "nodejs-ci": {
        "package.json": (
            '{\n  "name": "my-node-app",\n  "version": "1.0.0",\n'
            '  "scripts": {\n    "build": "echo build",\n'
            '    "test": "jest --coverage",\n    "lint": "eslint ."\n  }\n}\n'
        ),
        ".eslintrc.json": '{\n  "extends": "eslint:recommended",\n  "env": { "node": true, "es2020": true }\n}\n',
    },
    "java-maven-ci": {
        "pom.xml": (
            "<project>\n  <modelVersion>4.0.0</modelVersion>\n"
            "  <groupId>com.example</groupId>\n  <artifactId>my-app</artifactId>\n"
            "  <version>1.0-SNAPSHOT</version>\n</project>\n"
        ),
    },
    "docker-build-push": {
        "Dockerfile": (
            "FROM python:3.11-slim\nWORKDIR /app\n"
            "COPY requirements.txt .\nRUN pip install -r requirements.txt\n"
            "COPY . .\nCMD [\"python\", \"app.py\"]\n"
        ),
        ".dockerignore": "__pycache__\n*.pyc\nvenv\n.git\n",
    },
    "kubernetes-deploy": {
        "helm/Chart.yaml": (
            "apiVersion: v2\nname: my-app\ndescription: My App Helm Chart\nversion: 0.1.0\n"
        ),
        "helm/values.yaml": "replicaCount: 1\nimage:\n  repository: my-app\n  tag: latest\n",
    },
    "terraform-iac": {
        "main.tf": "# Define your Terraform resources here\n\nprovider \"aws\" {\n  region = var.region\n}\n",
        "variables.tf": "variable \"region\" {\n  default = \"us-east-1\"\n}\n",
        "terraform.tfvars": "region = \"us-east-1\"\n",
        ".terraform-version": "1.6.0\n",
    },
    "security-scan": {
        ".trivyignore": "# Add CVE IDs to ignore\n# CVE-2021-XXXXX\n",
    },
    "static-site-deploy": {
        "package.json": (
            '{\n  "name": "my-static-site",\n  "version": "1.0.0",\n'
            '  "scripts": { "build": "echo build to dist" }\n}\n'
        ),
    },
}


def generate_files(template_id: str, output_dir: str, params: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Generate Jenkinsfile + supporting files for a template.
    Returns a dict of {relative_path: content}.
    """
    meta = get_template_by_id(template_id)
    if not meta:
        raise ValueError(f"Template '{template_id}' not found.")

    merged_params = dict(meta.parameters)
    if params:
        merged_params.update(params)

    # Render Jenkinsfile
    raw = JENKINSFILES.get(template_id, "// Jenkinsfile for " + meta.name + "\npipeline { agent any stages {} }")
    jenkinsfile_content = raw.format(**{k: v for k, v in merged_params.items()})

    files: Dict[str, str] = {"Jenkinsfile": jenkinsfile_content}

    # Add extra supporting files
    if template_id in EXTRA_FILES:
        files.update(EXTRA_FILES[template_id])

    # Write files
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = {}
    for rel_path, content in files.items():
        full_path = out / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if not full_path.exists():
            full_path.write_text(content)
            written[rel_path] = str(full_path)

    return written
