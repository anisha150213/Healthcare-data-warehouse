# Anisha Tasnim
# tasnim@uwm.edu

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Patient:
    patient_id: str
    age: int
    gender: str
    bmi: float
    a1c: float | None
    bp_sys: int
    bp_dia: int
    smoking: bool
    encounters: list["Encounter"] = field(default_factory=list)
    notes: list["Note"] = field(default_factory=list)

    def add_encounter(self, encounter: "Encounter") -> None:
        self.encounters.append(encounter)

    def add_note(self, note: "Note") -> None:
        self.notes.append(note)

    def encounter_count(self) -> int:
        return len(self.encounters)

    def most_recent_encounter(self) -> "Encounter | None":
        if not self.encounters:
            return None
        return max(self.encounters, key=lambda item: item.date_value())

    def matches_eligibility_criteria(self) -> bool:
        return (
            18 <= self.age <= 45
            and self.gender.lower() in {"female", "male"}
            and self.bmi >= 30
            and self.a1c is not None
            and self.a1c >= 5.7
        )

    def to_csv_row(self) -> dict[str, object]:
        return {
            "patient_id": self.patient_id,
            "age": self.age,
            "gender": self.gender,
            "bmi": self.bmi,
            "a1c": "" if self.a1c is None else self.a1c,
            "bp_sys": self.bp_sys,
            "bp_dia": self.bp_dia,
            "smoking": self.smoking,
        }


@dataclass
class Provider:
    provider_id: str
    name: str
    specialty: str
    department_id: str
    encounters: list["Encounter"] = field(default_factory=list)

    def add_encounter(self, encounter: "Encounter") -> None:
        self.encounters.append(encounter)

    def encounter_count(self) -> int:
        return len(self.encounters)

    def to_csv_row(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "specialty": self.specialty,
            "department_id": self.department_id,
        }


@dataclass
class Department:
    department_id: str
    name: str
    location: str
    encounters: list["Encounter"] = field(default_factory=list)

    def add_encounter(self, encounter: "Encounter") -> None:
        self.encounters.append(encounter)

    def encounter_count(self) -> int:
        return len(self.encounters)

    def to_csv_row(self) -> dict[str, object]:
        return {
            "department_id": self.department_id,
            "name": self.name,
            "location": self.location,
        }


@dataclass
class Encounter:
    encounter_id: str
    patient_id: str
    provider_id: str
    department_id: str
    encounter_date: str
    encounter_type: str
    patient: Patient | None = None
    provider: Provider | None = None
    department: Department | None = None
    procedures: list["Procedure"] = field(default_factory=list)
    notes: list["Note"] = field(default_factory=list)

    def date_value(self) -> datetime:
        try:
            return datetime.strptime(self.encounter_date, "%Y-%m-%d")
        except ValueError:
            return datetime.min

    def add_procedure(self, procedure: "Procedure") -> None:
        self.procedures.append(procedure)

    def add_note(self, note: "Note") -> None:
        self.notes.append(note)

    def total_cost(self) -> float:
        return sum(procedure.cost for procedure in self.procedures)

    def to_csv_row(self) -> dict[str, object]:
        return {
            "encounter_id": self.encounter_id,
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "department_id": self.department_id,
            "encounter_date": self.encounter_date,
            "encounter_type": self.encounter_type,
        }


@dataclass
class Procedure:
    procedure_id: str
    encounter_id: str
    patient_id: str
    procedure_code: str
    procedure_name: str
    cost: float
    encounter: Encounter | None = None

    def to_csv_row(self) -> dict[str, object]:
        return {
            "procedure_id": self.procedure_id,
            "encounter_id": self.encounter_id,
            "patient_id": self.patient_id,
            "procedure_code": self.procedure_code,
            "procedure_name": self.procedure_name,
            "cost": self.cost,
        }


@dataclass
class Note:
    note_id: str
    patient_id: str
    encounter_id: str
    note_date: str
    note_type: str
    note_text: str
    patient: Patient | None = None
    encounter: Encounter | None = None

    def to_csv_row(self) -> dict[str, object]:
        return {
            "note_id": self.note_id,
            "patient_id": self.patient_id,
            "encounter_id": self.encounter_id,
            "note_date": self.note_date,
            "note_type": self.note_type,
            "note_text": self.note_text,
        }
