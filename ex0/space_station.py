from datetime import datetime
import json
import sys
from typing import Any, Optional
try:
    from pydantic import BaseModel, Field, ValidationError
except ModuleNotFoundError:
    print(
        "Make sure you have the required pydantic package installed\n"
        "Instalation:\n"
        "   pip install 'pydantic>=2.0'"
    )
    sys.exit(1)

# Centralized limits keep validation rules explicit and reusable.
STATION_ID_MIN_LEN = 3
STATION_ID_MAX_LEN = 10
NAME_MIN_LEN = 1
NAME_MAX_LEN = 50
CREW_SIZE_MIN = 1
CREW_SIZE_MAX = 20
POWER_LEVEL_MIN = 0.0
POWER_LEVEL_MAX = 100.0
OXYGEN_LEVEL_MIN = 0.0
OXYGEN_LEVEL_MAX = 100.0
NOTES_MAX_LEN = 200

DEFAULT_OPERATIONAL = True


class SpaceStation(BaseModel):
    # Field constraints enforce data integrity before business logic runs.
    station_id: str = Field(
        ...,
        min_length=STATION_ID_MIN_LEN,
        max_length=STATION_ID_MAX_LEN,
    )
    name: str = Field(
        ...,
        min_length=NAME_MIN_LEN,
        max_length=NAME_MAX_LEN,
    )
    crew_size: int = Field(
        ...,
        ge=CREW_SIZE_MIN,
        le=CREW_SIZE_MAX,
    )
    power_level: float = Field(
        ...,
        ge=POWER_LEVEL_MIN,
        le=POWER_LEVEL_MAX,
    )
    oxygen_level: float = Field(
        ...,
        ge=OXYGEN_LEVEL_MIN,
        le=OXYGEN_LEVEL_MAX,
    )
    last_maintenance: datetime = Field(...)
    is_operational: bool = Field(default=DEFAULT_OPERATIONAL)
    notes: Optional[str] = Field(default=None, max_length=NOTES_MAX_LEN)


def print_validation_error(exc: ValidationError) -> None:
    # Show the first human-readable validation message from Pydantic.
    errors = exc.errors()
    if not errors:
        print(exc)
        return
    first: Any = errors[0]
    message = first.get("msg", str(exc))
    print(message)


def invalid_station_payload() -> dict[str, Any]:
    return {
        "station_id": "ISS001",
        "name": "International Space Station",
        "crew_size": CREW_SIZE_MAX + 1,
        "power_level": 85.5,
        "oxygen_level": 92.3,
        "last_maintenance": datetime(2024, 1, 15, 10, 30, 0),
        "is_operational": True,
    }


def valid_station_payload() -> dict[str, Any]:
    return {
        "station_id": "ISS001",
        "name": "International Space Station",
        "crew_size": 6,
        "power_level": 85.5,
        "oxygen_level": 92.3,
        "last_maintenance": datetime(2024, 1, 15, 10, 30, 0),
        "is_operational": True,
    }


def json_payload(jsonfile: str) -> list[dict[str, Any]]:
    with open(jsonfile, "r", encoding="utf-8") as jf:
        payload: Any = json.load(jf)
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def print_station(station: SpaceStation) -> None:
    print("=" * 40)
    print("Valid station created:")
    print(f"ID: {station.station_id}")
    print(f"Name: {station.name}")
    print(f"Crew: {station.crew_size} people")
    print(f"Power: {station.power_level}%")
    print(f"Oxygen: {station.oxygen_level}%")
    status = "Operational" if station.is_operational else "Non-operational"
    print(f"Status: {status}")
    print()


def main() -> None:
    js = False
    station_records: list[dict[str, Any]] = []
    station_payload: dict[str, Any] = {}
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        station_records = json_payload(sys.argv[1])
        js = True
    elif len(sys.argv) == 1:
        station_payload = valid_station_payload()
    else:
        print(
            "Usage:\n"
            "   python3 space_station.py filename.json\n"
            "or:\n"
            "   python3 space_station.py"
        )
        sys.exit()

    print("Space Station Data Validation")
    # This instance demonstrates a successful model validation.
    if js:
        # Test json file
        for s in station_records:
            try:
                valid = SpaceStation.model_validate(s)
                print_station(valid)
            except ValidationError as exc:
                print_validation_error(exc)
    else:
        # Test Hardcode Valid station
        valid = SpaceStation.model_validate(station_payload)
        print_station(valid)

        try:
            print("=" * 40)
            print("Expected validation error:")
            # This payload intentionally violates the crew_size upper bound.
            invalid = SpaceStation.model_validate(invalid_station_payload())
            print_station(invalid)
        except ValidationError as exc:
            print_validation_error(exc)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Unexpected error: {exc}")
