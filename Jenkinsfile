// =============================================================================
// NairaTrack Backend CI/CD Pipeline
// =============================================================================
// Push-to-deploy: main branch → build → ECR → ECS
// Uses Cloudflare Tunnel for exposure (no ALB)
// =============================================================================

pipeline {
    agent any

    environment {
        AWS_REGION = 'us-east-1'
        ECR_REPO = '911027631608.dkr.ecr.us-east-1.amazonaws.com/personal-finance'
        ECS_CLUSTER = 'nameless-cluster'
        ECS_SERVICE = 'nairatrack-api'
        TASK_FAMILY = 'nairatrack-api'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "✅ Code checked out successfully"
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def gitHash = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = gitHash
                    env.FULL_IMAGE = "${ECR_REPO}:${gitHash}"

                    echo "🔨 Building image: ${env.FULL_IMAGE}"
                    sh "docker build -t ${env.FULL_IMAGE} -t ${ECR_REPO}:latest ."
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    echo "🧪 Running smoke tests..."

                    // Test 1: Basic Python/Django import (bypass entrypoint to skip DB operations)
                    sh """
                        docker run --rm --entrypoint python ${env.FULL_IMAGE} -c "
import sys
print('Python version:', sys.version)
print('Django import test...')
import django
print('Django version:', django.VERSION)
print('✅ Django import test passed!')
"
                    """

                    // Test 2: Validate Django app configuration (use dev settings with bypass)
                    echo "🔍 Validating Django app and URL configuration..."
                    sh """
                        docker run --rm --entrypoint python \
                            -e DJANGO_SETTINGS_MODULE=config.settings.dev \
                            ${env.FULL_IMAGE} -c "
import django
django.setup()
from django.urls import get_resolver
get_resolver()
print('✅ Django URL configuration validated!')
"
                    """

                    echo "✅ All smoke tests passed!"
                }
            }
        }

        stage('Push to ECR') {
            steps {
                script {
                    echo "📤 Pushing to ECR..."
                    sh """
                        aws ecr get-login-password --region ${AWS_REGION} | \
                            docker login --username AWS --password-stdin ${ECR_REPO}

                        docker push ${env.FULL_IMAGE}
                        docker push ${ECR_REPO}:latest
                    """
                    echo "✅ Image pushed: ${env.FULL_IMAGE}"
                }
            }
        }

        stage('Deploy to ECS') {
            steps {
                script {
                    echo "🚀 Deploying to ECS..."

                    sh """
                        aws ecs update-service \
                            --cluster ${ECS_CLUSTER} \
                            --service ${ECS_SERVICE} \
                            --force-new-deployment \
                            --region ${AWS_REGION}
                    """

                    echo "✅ ECS service update initiated!"
                    echo "📍 Access via: https://api.personal-finance.namelesscompany.cc"
                    echo "📦 Image deployed: ${env.FULL_IMAGE} (also tagged as :latest)"
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                script {
                    echo "🔍 Waiting for ECS deployment to complete (this may take 2-3 minutes)..."

                    sh """
                        aws ecs wait services-stable \
                            --cluster ${ECS_CLUSTER} \
                            --services ${ECS_SERVICE} \
                            --region ${AWS_REGION}
                    """

                    echo "✅ ECS service deployment complete and stable!"

                    def status = sh(
                        script: """
                            aws ecs describe-services \
                                --cluster ${ECS_CLUSTER} \
                                --services ${ECS_SERVICE} \
                                --region ${AWS_REGION} \
                                --query 'services[0].{running:runningCount,desired:desiredCount,deployments:length(deployments)}' \
                                --output json
                        """,
                        returnStdout: true
                    ).trim()

                    def statusMap = readJSON text: status
                    echo "Final status: running=${statusMap.running}, desired=${statusMap.desired}, deployments=${statusMap.deployments}"
                }
            }
        }
    }

    post {
        success {
            echo """
╔═══════════════════════════════════════════════════════════════════╗
║  🎉 DEPLOYMENT SUCCESSFUL!                                         ║
║                                                                     ║
║  Image: ${env.FULL_IMAGE}                                          ║
║  Service: ${ECS_SERVICE}                                           ║
║  Cluster: ${ECS_CLUSTER}                                           ║
║                                                                     ║
║  Access: https://api.personal-finance.namelesscompany.cc           ║
╚═══════════════════════════════════════════════════════════════════╝
"""
        }
        failure {
            echo "❌ Pipeline failed! Check the logs for details."
        }
        cleanup {
            sh 'docker system prune -f || true'
        }
    }
}
