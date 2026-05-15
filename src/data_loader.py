# Anisha Tasnim
# tasnim@uwm.edu

import csv
from pathlib import Path

from src.models import Department, Encounter, Note, Patient, Procedure, Provider
from src.user import User


PATIENT_FIELDS = ["patient_id", "age", "gender", "bmi", "a1c", "bp_sys", "bp_dia", "smoking"]
PROVIDER_FIELDS = ["provider_id", "name", "specialty", "department_id"]
DEPARTMENT_FIELDS = ["department_id", "name", "location"]
ENCOUNTER_FIELDS = ["encounter_id", "patient_id", "provider_id", "department_id", "encounter_date", "encounter_type"]
PROCEDURE_FIELDS = ["procedure_id", "encounter_id", "patient_id", "procedure_code", "procedure_name", "cost"]
NOTE_FIELDS = ["note_id", "patient_id", "encounter_id", "note_date", "note_type", "note_text"]


def to_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def to_int(value: object, default: int = 0) -> int:
    text = str(value).strip()
    if not text:
        return default
    return int(float(text))


def to_float(value: object, default: float | None = None) -> float | None:
    text = str(value).strip()
    if not text:
        return default
    return float(text)


class DataLoader:
    """Loads and saves all required project CSV files from the Data folder."""

    def __init__(self, data_folder: str = "Data") -> None:
        self.data_folder = Path(data_folder)

    def path(self, filename: str) -> Path:
        return self.data_folder / filename

    def load_users(self) -> dict[str, User]:
        users: dict[str, User] = {}
        with open(self.path("credentials.csv"), newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                user = User(row["username"], row["password"], row["role"])
                users[user.username] = user
        return users

    def load_all(self) -> tuple[
        dict[str, Patient],
        dict[str, Provider],
        dict[str, Department],
        dict[str, Encounter],
        dict[str, Procedure],
        dict[str, Note],
    ]:
        patients = self.load_patients()
        providers = self.load_providers()
        departments = self.load_departments()
        encounters = self.load_encounters()
        procedures = self.load_procedures()
        notes = self.load_notes()
        self.link_objects(patients, providers, departments, encounters, procedures, notes)
        return patients, providers, departments, encounters, procedures, notes

    def load_patients(self) -> dict[str, Patient]:
        patients: dict[str, Patient] = {}
        with open(self.path("patients.csv"), newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                patient = Patient(
                    patient_id=row["patient_id"].strip(),
                    age=to_int(row["age"]),
                    gender=row["gender"].strip(),
                    bmi=float(to_float(row["bmi"], 0.0) or 0.0),
                    a1c=to_float(row.get("a1c", ""), None),
                    bp_sys=to_int(row["bp_sys"]),
                    bp_dia=to_int(row["bp_dia"]),
                    smoking=to_bool(row.get("smoking", "")),
                )
                patients[patient.patient_id] = patient
        return patients

    def load_providers(self) -> dict[str, Provider]:
        providers: dict[str, Provider] = {}
        with open(self.path("providers.csv"), newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                provider = Provider(
                    provider_id=row["provider_id"].strip(),
                    name=row["name"].strip(),
                    specialty=row["specialty"].strip(),
                    department_id=row["department_id"].strip(),
                )
                providers[provider.provider_id] = provider
        return providers

    def load_departments(self) -> dict[str, Department]:
        departments: dict[str, Department] = {}
        with open(self.path("departments.csv"), newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                department = Department(
                    department_id=row["department_id"].strip(),
                    name=row["name"].strip(),
                    location=row["location"].strip(),
                )
                departments[department.department_id] = department
        return departments

    def load_encounters(self) -> dict[str, Encounter]:
        encounters: dict[str, Encounter] = {}
        with open(self.path("encounters.csv"), newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                encounter = Encounter(
                    encounter_id=row["encounter_id"].strip(),
                    patient_id=row["patient_id"].strip(),
                    provider_id=row["provider_id"].strip(),
                    department_id=row["department_id"].strip(),
                    encounter_date=row["encounter_date"].strip(),
                    encounter_type=row["encounter_type"].strip(),
                )
                encounters[encounter.encounter_id] = encounter
        return encounters

    def load_procedures(self) -> dict[str, Procedure]:
        procedures: dict[str, Procedure] = {}
        with open(self.path("procedures.csv"), newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                procedure = Procedure(
                    procedure_id=row["procedure_id"].strip(),
                    encounter_id=row["encounter_id"].strip(),
                    patient_id=row["patient_id"].strip(),
                    procedure_code=row["procedure_code"].strip(),
                    procedure_name=row["procedure_name"].strip(),
                    cost=float(to_float(row["cost"], 0.0) or 0.0),
                )
                procedures[procedure.procedure_id] = procedure
        return procedures

    def load_notes(self) -> dict[str, Note]:
        notes: dict[str, Note] = {}
        with open(self.path("notes.csv"), newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                note = Note(
                    note_id=row["note_id"].strip(),
                    patient_id=row["patient_id"].strip(),
                    encounter_id=row["encounter_id"].strip(),
                    note_date=row["note_date"].strip(),
                    note_type=row["note_type"].strip(),
                    note_text=row["note_text"].strip(),
                )
                notes[note.note_id] = note
        return notes

    def link_objects(
        self,
        patients: dict[str, Patient],
        providers: dict[str, Provider],
        departments: dict[str, Department],
        encounters: dict[str, Encounter],
        procedures: dict[str, Procedure],
        notes: dict[str, Note],
    ) -> None:
        # Rebuild object links after loading or modifying CSV-backed records.
        for patient in patients.values():
            patient.encounters.clear()
            patient.notes.clear()
        for provider in providers.values():
            provider.encounters.clear()
        for department in departments.values():
            department.encounters.clear()
        for encounter in encounters.values():
            encounter.procedures.clear()
            encounter.notes.clear()
            encounter.patient = patients.get(encounter.patient_id)
            encounter.provider = providers.get(encounter.provider_id)
            encounter.department = departments.get(encounter.department_id)
            if encounter.patient:
                encounter.patient.add_encounter(encounter)
            if encounter.provider:
                encounter.provider.add_encounter(encounter)
            if encounter.department:
                encounter.department.add_encounter(encounter)
        for procedure in procedures.values():
            procedure.encounter = encounters.get(procedure.encounter_id)
            if procedure.encounter:
                procedure.encounter.add_procedure(procedure)
        for note in notes.values():
            note.patient = patients.get(note.patient_id)
            note.encounter = encounters.get(note.encounter_id)
            if note.patient:
                note.patient.add_note(note)
            if note.encounter:
                note.encounter.add_note(note)

    def save_mutable_files(
        self,
        patients: dict[str, Patient],
        encounters: dict[str, Encounter],
        procedures: dict[str, Procedure],
        notes: dict[str, Note],
    ) -> None:
        # Only patient-related files change during add/remove operations.
        self.write_rows("patients.csv", PATIENT_FIELDS, [p.to_csv_row() for p in sorted(patients.values(), key=lambda x: x.patient_id)])
        self.write_rows("encounters.csv", ENCOUNTER_FIELDS, [e.to_csv_row() for e in sorted(encounters.values(), key=lambda x: x.encounter_id)])
        self.write_rows("procedures.csv", PROCEDURE_FIELDS, [p.to_csv_row() for p in sorted(procedures.values(), key=lambda x: x.procedure_id)])
        self.write_rows("notes.csv", NOTE_FIELDS, [n.to_csv_row() for n in sorted(notes.values(), key=lambda x: x.note_id)])

    def write_rows(self, filename: str, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
        self.data_folder.mkdir(parents=True, exist_ok=True)
        with open(self.path(filename), "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
