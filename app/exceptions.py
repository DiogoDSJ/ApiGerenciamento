from typing import Any


class AppException(Exception):
    """Classe base para todas as exceções de domínio da aplicação."""

    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"
    message: str = "Ocorreu um erro interno inesperado."

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.message = message or self.message
        self.details = details or {}
        self.headers = headers or {}
        super().__init__(self.message)


# --- Sub-raízes por Tipo de Problema ---


class NotFoundException(AppException):
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    message = "O recurso solicitado não foi encontrado."


class ConflictException(AppException):
    status_code = 409
    error_code = "RESOURCE_CONFLICT"
    message = "Houve um conflito com o estado atual do recurso."


class AuthenticationException(AppException):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"
    message = "Nome de usuário ou senha incorretos."


class UserAlreadyExistsException(ConflictException):
    error_code = "USER_ALREADY_EXISTS"

    def __init__(self, username: str):
        super().__init__(
            message=f"Já existe um usuário cadastrado com o username '{username}'.",
            details={"username": username},
        )

class EmailAlreadyExistsException(ConflictException):
    error_code = "USER_ALREADY_EXISTS"

    def __init__(self, email: str):
        super().__init__(
            message=f"Já existe um usuário cadastrado com o email '{email}'.",
            details={"email": email},
        )

class UserNotFoundException(NotFoundException):
    error_code = "USER_NOT_FOUND"

    def __init__(self, identifier: str):
        super().__init__(
            message=f"Usuário '{identifier}' não foi encontrado ou está inativo.",
            details={"identifier": identifier},
        )

class InvalidCredentialsException(AuthenticationException):
    message = "Credenciais inválidas ou token expirado."

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message or self.message,
            details=details,
            headers={"WWW-Authenticate": "Bearer"},
        )

class InvalidTokenType(AppException):
    status_code = 401
    error_code = "INVALID_TOKEN_TYPE"
    message = "Tipo de token inválido. Esperava-se um refresh token."

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message or self.message,
            details=details,
            headers={"WWW-Authenticate": "Bearer"},
        )

class InsufficientPermision(AppException):
    status_code = 401
    error_code = "ACESS_DENIED"
    message = "Operação permitida apenas para administradores"

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message or self.message,
            details=details,
        )
