from dataclasses import dataclass


@dataclass
class Employee:

    employee_id: int

    firstname: str

    lastname: str

    salary: float

    address: str

    transport: str

    declared_sport: str

    distance_km: float | None = None

    eligible_transport: bool = False

    bonus: float = 0

    wellbeing_days: int = 0