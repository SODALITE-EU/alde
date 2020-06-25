#!/usr/bin/env bash
# 
# Builds or push an image. 
# Commits on branches (not master) are tagged with the branch name.
# Commits on master are tagged with latest and with the version number
# 
# Usage:
#   $0 [build|push] <image-name>

build() {
    set -x
    docker build --build-arg VERSION=${VERSION} --build-arg DATE=${DATE} -t ${IMAGE}:${VERSION} .
    set +x
}

push() {
    set -x
    docker push ${IMAGE}:${VERSION}
    set +x
    if [ "$BRANCH" = "master" ]; then
        set -x
        docker tag ${IMAGE}:${VERSION} ${IMAGE}:latest
        docker push ${IMAGE}:latest
        set +x
    fi
}


if [ $# -ne 2 ] || [[ "$1" != "build" && "$1" != "push" ]] ; then
    echo "Usage: $0 [build|push] <image-name>"
    exit 1
fi

ACTION=$1
IMAGE=$2
VERSION=$(git describe --always --dirty)
DATE=$(date -u +%Y-%m-%dT%H:%M:%S)
DEFAULT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
# Detect if under Jenkins; if not, use DEFAULT_BRANCH
BRANCH=${CHANGE_BRANCH:-$DEFAULT_BRANCH}
VERSION=$(echo $VERSION | sed -e"s/^v//")

if [ "$BRANCH" != "master" ]; then
    VERSION=$(echo $BRANCH | sed -e"s|/|-|")

else
    if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "Skipping untagged commit on master"
	exit 0
    fi
fi


if [ "$ACTION" = "build" ]; then
    build
else
    push
fi

