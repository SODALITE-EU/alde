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
                sh "virtualenv venv"
                sh ". venv/bin/activate; pip install pybuilder==0.11.17; pyb install_dependencies"
            }
        }
        stage('Test') {
            steps {
                sh ". venv/bin/activate; pyb"
            }
        }
        stage('Build Docker image') {
            steps {
                sh "git fetch --tags && resources/bin/make_docker.sh build sodaliteh2020/alde"
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
