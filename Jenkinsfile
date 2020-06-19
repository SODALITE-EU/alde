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
        stage('Docker') {
            steps {
                sh "git fetch --tags && resources/bin/make_docker.sh alde"
            }
        }
    }
}
