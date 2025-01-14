from apscheduler.schedulers.background import BackgroundScheduler
from script.container import Container
from dependency_injector.wiring import inject, Provide

from script.service.preprocessing import PreprocessingService
from script.service.script import ScriptGenerateService

sched = BackgroundScheduler(timezone='Asia/Seoul')


@sched.scheduled_job('cron', second='0', id='script')
@inject
def script_job(script_generate_service: ScriptGenerateService = Provide[Container.script_generate_service]):
    print("script start")
    script_generate_service.run_from_db()

@sched.scheduled_job('cron', second='0', id='encoding')
@inject
def encoding_job(preprocessing_service: PreprocessingService = Provide[Container.preprocessing_service]):
    print("encoding start")
    preprocessing_service.download_and_upload_encode_video()

def start_stt():
    sched.start()
