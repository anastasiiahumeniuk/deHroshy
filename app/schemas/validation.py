import re
from decimal import Decimal


PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9\s])\S{8,128}$"
)

AMOUNT_PATTERN = re.compile(
    r"^\d+(?:[.,]\d{1,2})?$"
)

NAME_PATTERN = re.compile(
    r"^[A-Za-zА-Яа-яІіЇїЄєҐґ0-9]"
    r"[A-Za-zА-Яа-яІіЇїЄєҐґ0-9 .,'’()&/+\-]*$"
)

ACCOUNT_TYPE_PATTERN = re.compile(
    r"^[A-Za-zА-Яа-яІіЇїЄєҐґ0-9]"
    r"[A-Za-zА-Яа-яІіЇїЄєҐґ0-9 \-]*$"
)


def normalize_email(value: object) -> object:
    if isinstance(value, str):
        return value.strip().lower()

    return value


def validate_password_strength(value: str) -> str:
    if not PASSWORD_PATTERN.fullmatch(value):
        raise ValueError(
            "Password must contain an uppercase letter, "
            "a lowercase letter, a number, a special character "
            "and must not contain spaces"
        )

    return value


def normalize_amount(value: object) -> object:
    if isinstance(value, bool):
        raise ValueError("Amount must be a number")

    if isinstance(value, str):
        normalized_value = value.strip()

        if not AMOUNT_PATTERN.fullmatch(normalized_value):
            raise ValueError(
                "Amount must be a positive number with up to "
                "2 decimal places; use '.' or ',' as decimal separator"
            )

        return normalized_value.replace(",", ".")

    if isinstance(value, (int, float, Decimal)):
        return value

    raise ValueError("Amount must be a number")


def normalize_whitespace(value: str) -> str:
    """Trim surrounding whitespace and collapse internal whitespace."""
    return " ".join(value.split())


def normalize_name(value: object, field_name: str) -> object:
    if not isinstance(value, str):
        return value

    normalized_value = normalize_whitespace(value)

    if not normalized_value:
        raise ValueError(f"{field_name} must not be blank")

    if not NAME_PATTERN.fullmatch(normalized_value):
        raise ValueError(
            f"{field_name} may contain only letters, numbers, spaces, "
            "and . , ' - ( ) & / +"
        )

    return normalized_value


def normalize_account_type(value: object) -> object:
    if not isinstance(value, str):
        return value

    normalized_value = normalize_whitespace(value).lower()

    if not normalized_value:
        raise ValueError("Account type must not be blank")

    if not ACCOUNT_TYPE_PATTERN.fullmatch(normalized_value):
        raise ValueError(
            "Account type may contain only letters, numbers, "
            "spaces, and hyphens"
        )

    return normalized_value


def normalize_optional_comment(value: object) -> object:
    if value is None or not isinstance(value, str):
        return value

    normalized_value = normalize_whitespace(value)
    return normalized_value or None
