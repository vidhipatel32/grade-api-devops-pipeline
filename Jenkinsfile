pipeline {
    agent any

    environment {
        APP_NAME        = 'grade-api'
        DOCKER_IMAGE    = 'grade-api'
        STAGING_PORT    = '5001'
        PROD_PORT       = '5000'
        RELEASE_VERSION = "v1.0.${BUILD_NUMBER}"
        STAGING_PROJECT = 'grade-api-staging'
        PROD_PROJECT    = 'grade-api-prod'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code from Git...'
                checkout scm
                bat 'git rev-parse --short HEAD > git-commit.txt'
                script {
                    env.SHORT_COMMIT = readFile('git-commit.txt').trim()
                }
                echo "Commit: ${env.SHORT_COMMIT}"
            }
        }

        stage('Build') {
            steps {
                echo "Building Docker image ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                bat "docker build --pull -t ${DOCKER_IMAGE}:${BUILD_NUMBER} -t ${DOCKER_IMAGE}:latest ."
                bat """
                    echo Image: %DOCKER_IMAGE%:%BUILD_NUMBER% > build-metadata.txt
                    echo Release: %RELEASE_VERSION% >> build-metadata.txt
                    echo Commit: %SHORT_COMMIT% >> build-metadata.txt
                    echo Build: %BUILD_NUMBER% >> build-metadata.txt
                """
            }
            post {
                success {
                    archiveArtifacts artifacts: 'build-metadata.txt', fingerprint: true
                }
            }
        }

        stage('Test') {
            steps {
                echo 'Running unit and API integration tests with pytest...'
                bat """
                    docker run --rm ^
                        -v "%CD%":/app ^
                        -w /app ^
                        python:3.11-slim ^
                        sh -c "pip install -r requirements-dev.txt -q && pytest test_app.py -v --tb=short --junitxml=test-results.xml --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing"
                """
            }
            post {
                always {
                    junit 'test-results.xml'
                    archiveArtifacts artifacts: 'coverage.xml', allowEmptyArchive: true, fingerprint: true
                }
            }
        }

        stage('Code Quality') {
            steps {
                echo 'Running pylint with a quality threshold...'
                bat """
                    docker run --rm ^
                        -v "%CD%":/app ^
                        -w /app ^
                        python:3.11-slim ^
                        sh -c "pip install -r requirements-dev.txt -q && pylint app.py calculator.py --fail-under=8.0 --output-format=text > pylint-report.txt"
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: 'pylint-report.txt', fingerprint: true
                }
            }
        }

        stage('Security') {
            steps {
                echo 'Running Bandit source-code security scan...'
                bat """
                    docker run --rm ^
                        -v "%CD%":/app ^
                        -w /app ^
                        python:3.11-slim ^
                        sh -c "pip install -r requirements-dev.txt -q && bandit -r app.py calculator.py -ll -ii -f txt -o bandit-report.txt"
                """

                echo 'Running Trivy filesystem scan for dependency, secret, and config risks...'
                bat """
                    docker run --rm ^
                        -v "%CD%":/workspace ^
                        aquasec/trivy:latest fs ^
                        --severity HIGH,CRITICAL ^
                        --scanners vuln,secret,misconfig ^
                        --skip-version-check ^
                        --format json ^
                        --output /workspace/trivy-fs-report.json ^
                        /workspace
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.txt, trivy-fs-report.json', allowEmptyArchive: true, fingerprint: true
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying ${DOCKER_IMAGE}:${BUILD_NUMBER} to staging on port ${STAGING_PORT}"
                bat "docker compose -p ${STAGING_PROJECT} -f docker-compose.staging.yml down --remove-orphans || exit /b 0"
                bat "docker compose -p ${STAGING_PROJECT} -f docker-compose.staging.yml up -d"
                bat 'powershell -NoProfile -Command "Start-Sleep -Seconds 20"'
            }
        }

        stage('Staging Smoke Test') {
            steps {
                echo 'Verifying staging health endpoint...'
                bat "curl.exe -f -s http://localhost:${STAGING_PORT}/health"
            }
        }

        stage('Release') {
            steps {
                echo "Promoting image to release tag ${RELEASE_VERSION}"
                bat "docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:${RELEASE_VERSION}"
                bat "git tag ${RELEASE_VERSION} || echo Release tag already exists"
                bat """
                    echo Release Version: %RELEASE_VERSION% > release-notes.txt
                    echo Docker Image: %DOCKER_IMAGE%:%RELEASE_VERSION% >> release-notes.txt
                    echo Build Number: %BUILD_NUMBER% >> release-notes.txt
                    echo Git Commit: %SHORT_COMMIT% >> release-notes.txt
                    echo Build Date: %DATE% %TIME% >> release-notes.txt
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: 'release-notes.txt', fingerprint: true
                }
            }
        }

        stage('Deploy Production') {
            steps {
                echo "Deploying release ${RELEASE_VERSION} to production on port ${PROD_PORT}"
                bat "docker compose -p ${PROD_PROJECT} -f docker-compose.production.yml down --remove-orphans || exit /b 0"
                bat "docker compose -p ${PROD_PROJECT} -f docker-compose.production.yml up -d"
                bat 'powershell -NoProfile -Command "Start-Sleep -Seconds 30"'
                bat "curl.exe -f -s http://localhost:${PROD_PORT}/health"
            }
        }

        stage('Monitoring') {
            steps {
                echo 'Verifying Prometheus, Alertmanager, Grafana, and application metrics...'
                bat 'curl.exe -f -s http://localhost:9090/-/healthy'
                bat 'curl.exe -f -s http://localhost:9093/-/healthy'
                bat "curl.exe -f -s http://localhost:${PROD_PORT}/metrics"
                echo 'Grafana: http://localhost:3000 (admin / admin123)'
                echo 'Prometheus: http://localhost:9090'
                echo 'Alertmanager: http://localhost:9093'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully.'
            echo "Production app: http://localhost:${PROD_PORT}"
            echo "Release version: ${RELEASE_VERSION}"
        }
        failure {
            echo 'Pipeline failed. Check the failed stage log and archived reports.'
        }
        always {
            archiveArtifacts artifacts: '*.txt, *.xml', allowEmptyArchive: true
        }
    }
}
