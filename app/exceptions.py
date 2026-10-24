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

class BusinessRuleException(AppException):
    status_code = 400
    error_code = "BUSINESS_RULE_VIOLATION"
    message = "A operação viola uma regra de negócio do sistema."

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
            message=f"Usuário '{identifier}' não foi encontrado.",
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

class CategoryNotFoundException(NotFoundException):
    error_code = "CATEGORY_NOT_FOUND"

    def __init__(self, identifier: int):
        super().__init__(
            message=f"Categoria de id '{identifier}' não foi encontrada",
            details={"identifier": identifier},
        )

class CategoryAlreadyExistsException(ConflictException):
    error_code = "CATEGORY_ALREADY_EXISTS"

    def __init__(self, category_name: str, category_id: int):
        super().__init__(
            message=f"Já existe um categoria cadastrada com esse nome, seu nome: {category_name} id: {category_id}",
            details={"category_name": category_name, "category_id": category_id},
        )

class CategoryHasProductsException(ConflictException):
    error_code = "CATEGORY_STILL_HAS_PRODUCTS"

    def __init__(self, category: str):
        super().__init__(
            message=f"A categoria {category} tem produtos ativos anexados, desative-os primeiros para desativa-la ",
            details={"category": category},
        )

class SupplierConflictException(ConflictException):
    """Exceção base para qualquer colisão de dados de fornecedor."""

    error_code = "SUPPLIER_FIELD_CONFLICT"

    def __init__(
        self,
        field: str,
        value: str,
        existing_id: int | None = None,
        is_inactive: bool = False,
    ):
        status_desc = "desativado" if is_inactive else "ativo"
        action_desc = (
            " Restaure o registro em vez de criar outro."
            if is_inactive
            else " Informe um valor diferente."
        )

        super().__init__(
            message=(
                f"Já existe um fornecedor {status_desc} cadastrado com o {field} "
                f"'{value}' (ID: {existing_id}).{action_desc}"
            ),
            details={
                "conflicting_field": field,
                "value": value,
                "existing_supplier_id": existing_id,
                "is_inactive": is_inactive,
            },
        )


class SupplierAlreadyExistsException(ConflictException):
    error_code = "SUPPLIER_ALREADY_EXISTS"

    def __init__(self, name: str, id: int):
        super().__init__(
            message=f"Já existe um fornecedor cadastrado com esse nome, seu nome: {name} id: {id}",
            details={"name": name, "id": id},
        )

class SupplierHasProductsException(ConflictException):
    error_code = "SUPPLIER_STILL_HAS_PRODUCTS"

    def __init__(self, supplier: str):
        super().__init__(
            message=f"O fornecedor {supplier} tem produtos ativos anexados, desative-os primeiros para desativa-la ",
            details={"supplier": supplier},
        )


class AdminCantDeleteHimselfException(BusinessRuleException):
    message = "Você não pode excluir sua própria conta de administrador."

class AdminCantRevogateHimselfException(BusinessRuleException):
    message = "Você não pode tirar seus direitos de administrador."

class SupplierNotFoundException(NotFoundException):
    error_code = "SUPPLIER_NOT_FOUND"

    def __init__(self, supplier_id: int, is_inactive: bool = False):
        msg = (
            f"Fornecedor inativo com ID {supplier_id} não encontrado."
            if is_inactive
            else f"Fornecedor com ID {supplier_id} não encontrado."
        )
        super().__init__(
            message=msg,
            details={"supplier_id": supplier_id, "is_inactive": is_inactive},
        )




class SupplierConflictException(ConflictException):
    """Exceção base para qualquer colisão de dados de fornecedor."""

    error_code = "SUPPLIER_FIELD_CONFLICT"

    def __init__(
        self,
        field: str,
        value: str,
        existing_id: int | None = None,
        is_inactive: bool = False,
    ):
        status_desc = "desativado" if is_inactive else "ativo"
        action_desc = (
            " Restaure o registro em vez de criar outro."
            if is_inactive
            else " Informe um valor diferente."
        )

        super().__init__(
            message=(
                f"Já existe um fornecedor {status_desc} cadastrado com o {field} "
                f"'{value}' (ID: {existing_id}).{action_desc}"
            ),
            details={
                "conflicting_field": field,
                "value": value,
                "existing_supplier_id": existing_id,
                "is_inactive": is_inactive,
            },
        )

class SupplierRestoreConflictException(ConflictException):
    error_code = "SUPPLIER_RESTORE_CONFLICT"

    def __init__(self, conflicting_suppliers: list[str]):
        super().__init__(
            message=(
                f"Não é possível restaurar o fornecedor. Há conflito de dados "
                f"com o(s) fornecedor(es) ativo(s): {', '.join(conflicting_suppliers)}."
            ),
            details={"conflicts": conflicting_suppliers},
        )

class SupplierCnpjConflictException(SupplierConflictException):
    error_code = "SUPPLIER_CNPJ_ALREADY_EXISTS"

    def __init__(
        self, cnpj: str, existing_id: int | None = None, is_inactive: bool = False
    ):
        super().__init__(
            field="CNPJ",
            value=cnpj,
            existing_id=existing_id,
            is_inactive=is_inactive,
        )


class SupplierEmailConflictException(SupplierConflictException):
    error_code = "SUPPLIER_EMAIL_ALREADY_EXISTS"

    def __init__(
        self,
        email: str,
        existing_id: int | None = None,
        is_inactive: bool = False,
    ):
        super().__init__(
            field="E-mail",
            value=email,
            existing_id=existing_id,
            is_inactive=is_inactive,
        )


class SupplierPhoneConflictException(SupplierConflictException):
    error_code = "SUPPLIER_PHONE_ALREADY_EXISTS"

    def __init__(
        self,
        phone: str,
        existing_id: int | None = None,
        is_inactive: bool = False,
    ):
        super().__init__(
            field="Telefone",
            value=phone,
            existing_id=existing_id,
            is_inactive=is_inactive,
        )


class SupplierNameConflictException(SupplierConflictException):
    error_code = "SUPPLIER_NAME_ALREADY_EXISTS"

    def __init__(
        self, name: str, existing_id: int | None = None, is_inactive: bool = False
    ):
        super().__init__(
            field="Nome/Razão Social",
            value=name,
            existing_id=existing_id,
            is_inactive=is_inactive,
        )

class UserRestoreConflictException(ConflictException):
    error_code = "USER_RESTORE_CONFLICT"

    def __init__(self, conflicting_users: list[str]):
        super().__init__(
            message=(
                f"Não é possível restaurar o usuario. Há conflito de dados "
                f"com o(s) usuario(es) ativo(s): {', '.join(conflicting_users)}."
            ),
            details={"conflicts": conflicting_users},
        )
