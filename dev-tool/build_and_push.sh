#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

VERSION=$(python3 -c "import sys; sys.path.insert(0, '$SCRIPT_DIR/../api/$1-api/$1/setting'); from config import Settings; print(Settings.VERSION)")

if [ -z "$VERSION" ]; then
    echo "can't extract version"
    exit 1
fi

docker build --build-arg="SOURCE_DIR=api/$1-api" --build-arg="APP_DIR=$1" --platform linux/amd64 -t 760282210016.dkr.ecr.ap-northeast-2.amazonaws.com/dsail/playtherapy/$1-api:$VERSION $SCRIPT_DIR/../.

if [ $? -eq 0 ]; then
    docker push docker address$1-api:$VERSION
else
    echo "docker image push failed"
    exit 1
fi