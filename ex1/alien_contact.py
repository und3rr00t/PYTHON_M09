from datetime import datetime
from enum import Enum
import json
import sys
from typing import Any, Optional

try:
    from pydantic import BaseModel, Field, ValidationError, model_validator
except ModuleNotFoundError:
    print(
        "Make sure you have the required pydantic package installed\n"
        "Instalation:\n"
        "   pip install 'pydantic>=2.0'"
    )
    sys.exit(1)

# These constants map each field and business rule to one source of truth.
CONTACT_ID_MIN_LEN = 5
CONTACT_ID_MAX_LEN = 15
CONTACT_ID_PREFIX = "AC"

LOCATION_MIN_LEN = 3
LOCATION_MAX_LEN = 100

SIGNAL_STRENGTH_MIN = 0.0
SIGNAL_STRENGTH_MAX = 10.0

DURATION_MINUTES_MIN = 1
DURATION_MINUTES_MAX = 1440

WITNESS_COUNT_MIN = 1
WITNESS_COUNT_MAX = 100

MESSAGE_MAX_LEN = 500

STRONG_SIGNAL_THRESHOLD = 7.0
TELEPATHIC_MIN_WITNESSES = 3

DEFAULT_VERIFIED = False


class ContactType(str, Enum):
    RADIO = "radio"
    VISUAL = "visual"
    PHYSICAL = "physical"
    TELEPATHIC = "telepathic"


class AlienContact(BaseModel):
    # Field-level constraints validate shape and primitive bounds.
    contact_id: str = Field(
        ...,
        min_length=CONTACT_ID_MIN_LEN,
        max_length=CONTACT_ID_MAX_LEN,
    )
    timestamp: datetime
    location: str = Field(
        ...,
        min_length=LOCATION_MIN_LEN,
        max_length=LOCATION_MAX_LEN,
    )
    contact_type: ContactType
    signal_strength: float = Field(
        ...,
        ge=SIGNAL_STRENGTH_MIN,
        le=SIGNAL_STRENGTH_MAX,
    )
    duration_minutes: int = Field(
        ...,
        ge=DURATION_MINUTES_MIN,
        le=DURATION_MINUTES_MAX,
    )
    witness_count: int = Field(
        ...,
        ge=WITNESS_COUNT_MIN,
        le=WITNESS_COUNT_MAX,
    )
    message_received: Optional[str] = Field(
        default=None,
        max_length=MESSAGE_MAX_LEN,
    )
    is_verified: bool = Field(default=DEFAULT_VERIFIED)

    @model_validator(mode="after")
    def enforce_contact_rules(self) -> "AlienContact":
        # Model-level validation handles cross-field domain requirements.
        if not self.contact_id.startswith(CONTACT_ID_PREFIX):
            raise ValueError(
                f'Contact ID must start with "{CONTACT_ID_PREFIX}" '
                "(Alien Contact)",
            )
        if self.contact_type is ContactType.PHYSICAL and not self.is_verified:
            raise ValueError(
                "Physical contact reports must be verified",
            )
        if (
            self.contact_type is ContactType.TELEPATHIC
            and self.witness_count < TELEPATHIC_MIN_WITNESSES
        ):
            raise ValueError(
                "Telepathic contact requires at least "
                f"{TELEPATHIC_MIN_WITNESSES} witnesses",
            )
        if self.signal_strength > STRONG_SIGNAL_THRESHOLD:
            empty = (
                self.message_received is None
                or not self.message_received.strip()
            )
            if empty:
                raise ValueError(
                    "Strong signals (above "
                    f"{STRONG_SIGNAL_THRESHOLD}) should include "
                    "received messages",
                )
        return self


def print_validation_error(exc: ValidationError) -> None:
    # Prefer custom errors, then fallback to generic Pydantic messages.
    for err in exc.errors():
        ctx = err.get("ctx")
        if isinstance(ctx, dict) and "error" in ctx:
            error_obj = ctx["error"]
            if isinstance(error_obj, ValueError):
                print(str(error_obj))
                return
        if err.get("type") == "value_error":
            print(err.get("msg", str(exc)))
            return
    errors = exc.errors()
    if errors:
        first: Any = errors[0]
        print(first.get("msg", str(exc)))
    else:
        print(str(exc))


def json_payload(jsonfile: str) -> list[dict[str, Any]]:
    with open(jsonfile, "r", encoding="utf-8") as jf:
        payload: Any = json.load(jf)
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def valid_contact_payload() -> dict[str, Any]:
    return {
        "contact_id": "AC_2024_001",
        "timestamp": datetime(2024, 1, 15, 14, 30, 0),
        "location": "Area 51, Nevada",
        "contact_type": ContactType.RADIO,
        "signal_strength": 8.5,
        "duration_minutes": 45,
        "witness_count": 5,
        "message_received": "Greetings from Zeta Reticuli",
        "is_verified": False,
    }


def invalid_contact_payload() -> dict[str, Any]:
    return {
        "contact_id": "AC_2024_002",
        "timestamp": datetime(2024, 1, 16, 9, 15, 0),
        "location": "Roswell",
        "contact_type": ContactType.TELEPATHIC,
        "signal_strength": 6.2,
        "duration_minutes": 30,
        "witness_count": TELEPATHIC_MIN_WITNESSES - 1,
        "message_received": None,
        "is_verified": False,
    }


def print_contact(contact: AlienContact) -> None:
    print("Valid contact report:")
    print(f"ID: {contact.contact_id}")
    print(f"Type: {contact.contact_type.value}")
    print(f"Location: {contact.location}")
    print(f"Signal: {contact.signal_strength}/10")
    print(f"Duration: {contact.duration_minutes} minutes")
    print(f"Witnesses: {contact.witness_count}")
    print(f"Message: {contact.message_received!r}")
    print()
    print("=" * 40)


def main() -> None:
    contact_records: list[dict[str, Any]] = []
    load_from_json = False
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        contact_records = json_payload(sys.argv[1])
        load_from_json = True
    elif len(sys.argv) != 1:
        print(
            "Usage:\n"
            "   python3 alien_contact.py filename.json\n"
            "or:\n"
            "   python3 alien_contact.py",
        )
        return

    print("Alien Contact Log Validation")
    print("=" * 40)

    if load_from_json:
        for payload in contact_records:
            try:
                valid = AlienContact.model_validate(payload)
                print_contact(valid)
            except ValidationError as exc:
                print("Expected validation error:")
                print_validation_error(exc)
        return

    # Valid report: satisfies enum, ranges, and model validator rules.
    valid = AlienContact.model_validate(valid_contact_payload())
    print_contact(valid)
    print("Expected validation error:")

    try:
        invalid = AlienContact.model_validate(invalid_contact_payload())
        print_contact(invalid)
    except ValidationError as exc:
        print_validation_error(exc)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Unexpected runtime error: {exc}")
