import math
from datetime import datetime
from enum import Enum
import json
import sys
from typing import Any

try:
    from pydantic import BaseModel, Field, ValidationError, model_validator
except ModuleNotFoundError:
    print(
        "Make sure you have the required pydantic package installed\n"
        "Instalation:\n"
        "   pip install 'pydantic>=2.0'"
    )
    sys.exit(1)

# Mission constraints are grouped to avoid hidden magic numbers.
MEMBER_ID_MIN_LEN = 3
MEMBER_ID_MAX_LEN = 10
MEMBER_NAME_MIN_LEN = 2
MEMBER_NAME_MAX_LEN = 50
MEMBER_AGE_MIN = 18
MEMBER_AGE_MAX = 80
SPECIALIZATION_MIN_LEN = 3
SPECIALIZATION_MAX_LEN = 30
YEARS_EXPERIENCE_MIN = 0
YEARS_EXPERIENCE_MAX = 50

MISSION_ID_MIN_LEN = 5
MISSION_ID_MAX_LEN = 15
MISSION_ID_PREFIX = "M"

MISSION_NAME_MIN_LEN = 3
MISSION_NAME_MAX_LEN = 100

DESTINATION_MIN_LEN = 3
DESTINATION_MAX_LEN = 50

DURATION_DAYS_MIN = 1
DURATION_DAYS_MAX = 3650

CREW_SIZE_MIN = 1
CREW_SIZE_MAX = 12

DEFAULT_MISSION_STATUS = "planned"

BUDGET_MILLIONS_MIN = 1.0
BUDGET_MILLIONS_MAX = 10000.0

LONG_MISSION_DAY_THRESHOLD = 365
EXPERIENCED_CREW_YEARS = 5
EXPERIENCED_CREW_FRACTION = 0.5

DEFAULT_MEMBER_ACTIVE = True


class Rank(str, Enum):
    CADET = "cadet"
    OFFICER = "officer"
    LIEUTENANT = "lieutenant"
    CAPTAIN = "captain"
    COMMANDER = "commander"


COMMAND_RANKS: frozenset[Rank] = frozenset({Rank.CAPTAIN, Rank.COMMANDER})


class CrewMember(BaseModel):
    # CrewMember validates each person before mission-level checks run.
    member_id: str = Field(
        ...,
        min_length=MEMBER_ID_MIN_LEN,
        max_length=MEMBER_ID_MAX_LEN,
    )
    name: str = Field(
        ...,
        min_length=MEMBER_NAME_MIN_LEN,
        max_length=MEMBER_NAME_MAX_LEN,
    )
    rank: Rank
    age: int = Field(..., ge=MEMBER_AGE_MIN, le=MEMBER_AGE_MAX)
    specialization: str = Field(
        ...,
        min_length=SPECIALIZATION_MIN_LEN,
        max_length=SPECIALIZATION_MAX_LEN,
    )
    years_experience: int = Field(
        ...,
        ge=YEARS_EXPERIENCE_MIN,
        le=YEARS_EXPERIENCE_MAX,
    )
    is_active: bool = Field(default=DEFAULT_MEMBER_ACTIVE)


class SpaceMission(BaseModel):
    # SpaceMission composes nested CrewMember models plus mission metadata.
    mission_id: str = Field(
        ...,
        min_length=MISSION_ID_MIN_LEN,
        max_length=MISSION_ID_MAX_LEN,
    )
    mission_name: str = Field(
        ...,
        min_length=MISSION_NAME_MIN_LEN,
        max_length=MISSION_NAME_MAX_LEN,
    )
    destination: str = Field(
        ...,
        min_length=DESTINATION_MIN_LEN,
        max_length=DESTINATION_MAX_LEN,
    )
    launch_date: datetime
    duration_days: int = Field(..., ge=DURATION_DAYS_MIN, le=DURATION_DAYS_MAX)
    crew: list[CrewMember] = Field(
        ...,
        min_length=CREW_SIZE_MIN,
        max_length=CREW_SIZE_MAX,
    )
    mission_status: str = Field(default=DEFAULT_MISSION_STATUS)
    budget_millions: float = Field(
        ...,
        ge=BUDGET_MILLIONS_MIN,
        le=BUDGET_MILLIONS_MAX,
    )

    @model_validator(mode="after")
    def enforce_mission_safety(self) -> "SpaceMission":
        # Cross-member safety rules are enforced once all fields are parsed.
        if not self.mission_id.startswith(MISSION_ID_PREFIX):
            raise ValueError(
                f'Mission ID must start with "{MISSION_ID_PREFIX}"',
            )
        if not any(member.rank in COMMAND_RANKS for member in self.crew):
            raise ValueError(
                "Mission must have at least one Commander or Captain",
            )
        if not all(member.is_active for member in self.crew):
            raise ValueError("All crew members must be active")
        if self.duration_days > LONG_MISSION_DAY_THRESHOLD:
            required_experienced = math.ceil(
                len(self.crew) * EXPERIENCED_CREW_FRACTION,
            )
            experienced_count = sum(
                1
                for member in self.crew
                if member.years_experience >= EXPERIENCED_CREW_YEARS
            )
            if experienced_count < required_experienced:
                pct = int(EXPERIENCED_CREW_FRACTION * 100)
                raise ValueError(
                    "Long missions (over "
                    f"{LONG_MISSION_DAY_THRESHOLD} days) need "
                    f"{pct}% experienced crew "
                    f"({EXPERIENCED_CREW_YEARS}+ years)",
                )
        return self


def print_validation_error(exc: ValidationError) -> None:
    # Keep output readable by surfacing the first relevant message.
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


def valid_mission_payload() -> dict[str, Any]:
    return {
        "mission_id": "M2024_MARS",
        "mission_name": "Mars Colony Establishment",
        "destination": "Mars",
        "launch_date": datetime(2024, 6, 1, 8, 0, 0),
        "duration_days": 900,
        "budget_millions": 2500.0,
        "crew": [
            {
                "member_id": "CM001",
                "name": "Sarah Connor",
                "rank": Rank.COMMANDER,
                "age": 42,
                "specialization": "Mission Command",
                "years_experience": 12,
            },
            {
                "member_id": "CM002",
                "name": "John Smith",
                "rank": Rank.LIEUTENANT,
                "age": 35,
                "specialization": "Navigation",
                "years_experience": 8,
            },
            {
                "member_id": "CM003",
                "name": "Alice Johnson",
                "rank": Rank.OFFICER,
                "age": 31,
                "specialization": "Engineering",
                "years_experience": 6,
            },
        ],
    }


def invalid_mission_payload() -> dict[str, Any]:
    return {
        "mission_id": "M2024_TEST",
        "mission_name": "Short Lunar Sortie",
        "destination": "Moon",
        "launch_date": datetime(2024, 3, 1, 12, 0, 0),
        "duration_days": 30,
        "budget_millions": 120.0,
        "crew": [
            {
                "member_id": "CM010",
                "name": "Michael Brown",
                "rank": Rank.LIEUTENANT,
                "age": 40,
                "specialization": "Navigation",
                "years_experience": 10,
            },
            {
                "member_id": "CM011",
                "name": "Emma Davis",
                "rank": Rank.OFFICER,
                "age": 29,
                "specialization": "Engineering",
                "years_experience": 5,
            },
        ],
    }


def print_mission(mission: SpaceMission) -> None:
    print("Valid mission created:")
    print(f"Mission: {mission.mission_name}")
    print(f"ID: {mission.mission_id}")
    print(f"Destination: {mission.destination}")
    print(f"Duration: {mission.duration_days} days")
    print(f"Budget: ${mission.budget_millions}M")
    print(f"Crew size: {len(mission.crew)}")
    print("Crew members:")
    for member in mission.crew:
        print(
            f"- {member.name} ({member.rank.value}) - {member.specialization}",
        )
    print()
    print("=" * 40)


def main() -> None:
    mission_records: list[dict[str, Any]] = []
    load_from_json = False
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        mission_records = json_payload(sys.argv[1])
        load_from_json = True
    elif len(sys.argv) != 1:
        print(
            "Usage:\n"
            "   python3 space_crew.py filename.json\n"
            "or:\n"
            "   python3 space_crew.py",
        )
        return

    print("Space Mission Crew Validation")
    print("=" * 40)

    if load_from_json:
        for payload in mission_records:
            try:
                mission = SpaceMission.model_validate(payload)
                print_mission(mission)
            except ValidationError as exc:
                print("Expected validation error:")
                print_validation_error(exc)
        return

    # Valid long mission: includes command rank and enough experienced crew.
    valid = SpaceMission.model_validate(valid_mission_payload())
    print_mission(valid)

    try:
        invalid = SpaceMission.model_validate(invalid_mission_payload())
        print_mission(invalid)
    except ValidationError as exc:
        print("Expected validation error:")
        print_validation_error(exc)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Unexpected runtime error: {exc}")
