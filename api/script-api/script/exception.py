class ServiceException(Exception):
    """Service Exception"""
    pass

class InvalidToken(ServiceException):
    """Invalid Token"""

    def __init__(self, token: str):
        self.message = f"access token {token} is invalid"
        self.code = 401
        super().__init__(self.message)
