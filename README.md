# PlayTherapy_Backend

## Install Env

```bash
pip install poetry
```

## Install Dependency

```bash
cd api/auth-api
poetry install --sync
```

## Run 

```bash
poetry run uvicorn main:app --reload --app-dir auth
```

## Test

```bash
poetry run python -m unittest discover -s tests
```

## auth image build

전체 프로젝트 Root 에서 실행하세요.

```bash
docker build -t 760282210016.dkr.ecr.ap-northeast-2.amazonaws.com/dsail/playtherapy/auth-api . --build-arg SOURCE_DIR=api/auth-api --build-arg APP_DIR=auth
```

## auth image run 

```bash
docker run -ti -p 8000:8000 760282210016.dkr.ecr.ap-northeast-2.amazonaws.com/dsail/playtherapy/auth-api
```

## Build And Push by script

```bash
./build_and_push.sh auth
```

```bash
./build_and_push.bat auth
```

