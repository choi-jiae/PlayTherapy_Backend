class ServiceException(Exception):
    """Service Exception"""

    pass


class UploadFailed(ServiceException):
    """Upload Failed"""

    def __init__(self, file: str):
        self.message = f"File [{file}] Upload failed."
        self.status_code = 400
        self.error_code = 1000
        super().__init__(self.message)


class DownloadFailed(ServiceException):
    """Download Failed"""

    def __init__(self, file: str):
        self.message = f"File [{file}] Download failed."
        self.status_code = 400
        self.error_code = 1001
        super().__init__(self.message)
