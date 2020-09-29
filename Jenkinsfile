pipeline {
    agent { label 'docker-slave' }
    stages {
        stage ('Pull repo code from github') {
            steps {
                checkout scm
            }
        }
        stage('Install dependencies') {
            steps {
                sh "env"
                sh "virtualenv venv"
                sh ". venv/bin/activate; pip install pybuilder==0.12.9; pyb install_dependencies"
            }
        }
        stage('Test') {
            steps {
                sh ". venv/bin/activate; pyb coverage"
            }
        }
        stage('Build Docker image') {
            steps {
                sh "git fetch --tags && resources/bin/make_docker.sh build sodaliteh2020/alde"
            }
        }
        stage('SonarQube analysis') {
            environment {
                scannerHome = tool 'SonarQubeScanner'
            }
            steps {
                withSonarQubeEnv('SonarCloud') {
                    sh "${scannerHome}/bin/sonar-scanner"
                }
            }
        }
        stage('Push image to DockerHub') {
            steps {
                withDockerRegistry(credentialsId: 'jenkins-sodalite.docker_token', url: '') {
                    sh "resources/bin/make_docker.sh push sodaliteh2020/alde"
                }
            }
        }
    }
}
