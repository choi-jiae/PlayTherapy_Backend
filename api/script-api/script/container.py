from dependency_injector import containers, providers

from core.repository.session import SessionRepository
from core.db.connection import ConnectionManager
from core.repository.state_type import StateTypeRepository
from core.service.security import SecurityService
from script.service.llm_service import LLMService
from script.service.nonverbal import NonVerbalService
from script.service.preprocessing import PreprocessingService
from object.storage.client import ClientManager
from object.repository.video import VideoRepository
from object.repository.script import ScriptRepository
from object.service.script import ScriptService
from object.service.video import VideoService
from script.service.script import ScriptGenerateService
from script.service.stt import SttService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["."])

    config = providers.Configuration()

    # object services
    client_manager = providers.Singleton(
        ClientManager,
        aws_access_key_id=config.aws.access_key,
        aws_secret_access_key=config.aws.secret_key,
        region_name=config.aws.region,
    )

    video_repository = providers.Singleton(
        VideoRepository,
        bucket=config.aws.bucket,
        client_manager=client_manager,
    )

    script_repository = providers.Singleton(
        ScriptRepository,
        bucket=config.aws.bucket,
        client_manager=client_manager,
    )

    video_service = providers.Singleton(
        VideoService,
        video_repository=video_repository,
    )

    script_service = providers.Singleton(
        ScriptService,
        script_repository=script_repository,
    )

    # core services
    connection_manager = providers.Singleton(
        ConnectionManager,
        db_url=config.mysql.db_url,
        pool_recycle=config.mysql.pool_recycle,
    )

    security_service = providers.Singleton(
        SecurityService,
        secret_key=config.security.secret_key,
        algorithm=config.security.algorithm,
        expires_delta=config.security.expires_delta,
    )

    # repositories
    session_repository = providers.Singleton(
        SessionRepository, connection_manager=connection_manager
    )

    state_type_repository = providers.Singleton(
        StateTypeRepository, connection_manager=connection_manager
    )

    # service
    llm_service = providers.Singleton(
        LLMService,
        model_name=config.open_ai.model,
        token=config.open_ai.token,
        temperature=config.open_ai.temperature
    )

    non_verbal_service = providers.Singleton(
        NonVerbalService,
        gpt_token=config.open_ai.token
    )


    preprocessing_service = providers.Singleton(
        PreprocessingService,
        connection_manager=connection_manager,
        session_repository=session_repository,
        video_service=video_service,
        video_split_output_path=config.preprocessing.video_split_output_path,
        encoding_video_output=config.preprocessing.encoding_video_output,
    )

    stt_service = providers.Singleton(
        SttService,
        llm_service=llm_service
    )

    script_generate_service = providers.Singleton(
        ScriptGenerateService,
        connection_manager=connection_manager,
        session_repository=session_repository,
        state_type_repository=state_type_repository,
        preprocessing_service=preprocessing_service,
        script_service=script_service,
        external_volume_path=config.external_volume.path,
        stt_service=stt_service,
        non_verbal_service=non_verbal_service,
    )
