properties([
  pipelineTriggers([]),
  durabilityHint('PERFORMANCE_OPTIMIZED')
])

pipeline {

    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  containers:

  - name: dind
    image: docker:dind
    securityContext:
      privileged: true
    command: ["dockerd-entrypoint.sh"]
    args:
      - "--host=tcp://0.0.0.0:2375"
      - "--insecure-registry=nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085"
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent

  - name: sonar-scanner
    image: sonarsource/sonar-scanner-cli
    command: ["cat"]
    tty: true
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent

  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["cat"]
    tty: true
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent

  volumes:
  - name: workspace-volume
    emptyDir: {}
"""
        }
    }

    options { skipDefaultCheckout() }

    environment {
        DOCKER_IMAGE = "pdfhub"
        SONAR_TOKEN = "sqp_dca7bdafc7a5c9af27ff2a09bcae4d283cd83a27"
        REGISTRY_HOST = "nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085"
        REGISTRY = "${REGISTRY_HOST}/2401146"
        NAMESPACE = "2401146"
    }

    stages {

        stage('Checkout Code') {
            steps {
                deleteDir()
                sh "git clone https://github.com/SaritaPaliwal/PDFProject_deploy.git ."
                echo "✔ Source code cloned successfully"
            }
        }

        stage('Build Docker Image') {
            steps {
                container('dind') {
                    sh """
                        docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} -t ${DOCKER_IMAGE}:latest .
                        docker image ls
                    """
                }
            }
        }

        stage('Run Tests & Coverage') {
            steps {
                container('dind') {
                    sh """
                        docker run --rm \
                        -v $PWD:/workspace \
                        -w /workspace \
                        ${DOCKER_IMAGE}:latest \
                        pytest --maxfail=1 --disable-warnings --cov=. --cov-report=xml
                    """
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                container('sonar-scanner') {
                    sh """
                        sonar-scanner \
                        -Dsonar.projectKey=pdfhub \
                        -Dsonar.projectName=PDFhub \
                        -Dsonar.host.url=http://sonarqube-sonarqube.sonarqube.svc.cluster.local:9000 \
                        -Dsonar.token=${SONAR_TOKEN} \
                        -Dsonar.python.coverage.reportPaths=coverage.xml
                    """
                }
            }
        }

        stage('Login to Nexus') {
            steps {
                container('dind') {
                    sh """
                        echo 'Logging into Nexus registry...'
                        docker login ${REGISTRY_HOST} -u admin -p Changeme@2025
                    """
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                container('dind') {
                    sh """
                        docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER}
                        docker push ${REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER}
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    sh """
                        kubectl apply -f k8s-deployment/deployment.yaml
                        kubectl set image deployment/pdfhub-app pdfhub-container=${REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} -n ${NAMESPACE}
                        kubectl rollout status deployment/pdfhub-app -n ${NAMESPACE}
                    """
                }
            }
        }
    }

    post {
        success { echo "🎉 PDFhub CI/CD Pipeline completed successfully!" }
        failure { echo "❌ Pipeline failed" }
        always  { echo "🔄 Pipeline finished" }
    }
}
