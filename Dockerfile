FROM python:3.10.13-slim-bookworm

RUN apt-get update && apt-get -y install sudo

RUN sudo apt-get update

RUN sudo apt-get install pkg-config -y
RUN sudo apt-get install default-libmysqlclient-dev -y
RUN sudo apt-get install build-essential -y

RUN pip install poetry==1.7.1

RUN echo "deb http://archive.debian.org/debian stretch main" > /etc/apt/sources.list

RUN apt-get install -y tzdata

ENV TZ=Asia/Seoul

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG SOURCE_DIR

ARG APP_DIR

ENV APP_DIR=$APP_DIR

COPY ./$SOURCE_DIR /app/$SOURCE_DIR

COPY ./package  /app/package

WORKDIR /app/$SOURCE_DIR

RUN poetry install --sync

EXPOSE 8000 7860

ENTRYPOINT ["sh", "-c", "./entrypoint.sh"]