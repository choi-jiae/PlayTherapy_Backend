import os
import sys
from configparser import ConfigParser

from dependency_injector import providers
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from script.container import Container
from setting.config import settings
from script.exception import InvalidToken
from object.exception import UploadFailed, DownloadFailed

from script.route.monitor import router as monitor_router
from script.scheduler.script_batch import start_stt

config = providers.Configuration()
container = Container()
container.config.from_yaml(f"./script/config-{os.getenv('PHASE','LOCAL')}.yaml")

container.wire(packages=["script.route", "script.scheduler"])
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://playtherapy-console.dsail.skku.edu",
    "http://playtherapy-console-alpha.dsail.skku.edu",
    "playtherapy-argocd.dsail.skku.edu",
    "playtherapy-backend-alpha.dsail.skku.edu",
    "playtherapy-backend.dsail.skku.edu",
    "k8s-ingressn-ingressn-1653a1e369-42b18eda041d135d.elb.ap-northeast-2.amazonaws.com",
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI(
    debug=True,
    title=settings.APP_TITLE,
    version=settings.VERSION,
    middleware=middleware,
)


@app.exception_handler(InvalidToken)
async def invalid_token_handler(request: Request, exc: InvalidToken):
    return JSONResponse(
        status_code=exc.code,
        content={"message": exc.message},
    )


@app.exception_handler(UploadFailed)
async def upload_failed_handler(request: Request, exc: UploadFailed):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "error_code": exc.error_code},
    )


@app.exception_handler(DownloadFailed)
async def download_failed_handler(request: Request, exc: DownloadFailed):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "error_code": exc.error_code},
    )


def register_routers(app: FastAPI):
    app.include_router(monitor_router, prefix="/analyze/api/monitor")


start_stt()
register_routers(app)
