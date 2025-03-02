# PlayTherapy_Backend
**PlayTherapy**는 **놀이치료사를 위한 놀이 치료 과정 개선 도움 시스템**으로, 융합연구학점제 수업에서 진행한 프로젝트입니다.

PlayTherapy가 제공하는 주요 기능은 다음과 같습니다.

- 아동 별 놀이치료 기록 관리 페이지(case) 생성
- 놀이치료 회기 별(session) 동영상 업로드 및 축어록 자동 생성
- 축어록 수정 및 놀이치료 영상 확인
- 축어록 다운로드
- 놀이치료 축어록 분석 리포트

본 레포지토리에는 직접 개발에 참여한 부분들만 남겨두었습니다.
- 비디오 인코딩 및 s3 업로드
- script s3 업로드
- script 생성 api 검토

## Use Case Diagram
![image](https://github.com/user-attachments/assets/2fa59463-cc21-4fea-add7-b6eff1827a09)


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
