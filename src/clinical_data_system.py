# Anisha Tasnim
# tasnim@uwm.edu

import csv
import random
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

from src.data_loader import DataLoader
from src.models import Encounter, Note, Patient


class ClinicalDataSystem:

    def __init__(self, loader: DataLoader) -> None:
        self.loader = loader
        (
            self.patients,
            self.providers,
            self.departments,
            self.encounters,
            self.procedures,
            self.notes,
        ) = loader.load_all()

    def relink(self) -> None:
        self.loader.link_objects(
            self.patients,
            self.providers,
            self.departments,
            self.encounters,
            self.procedures,
            self.notes,
        )

    def persist_changes(self) -> None:
        self.loader.save_mutable_files(self.patients, self.encounters, self.procedures, self.notes)

    def retrieve_patient(self, patient_id: str) -> str | None:
        patient = self.patients.get(patient_id.strip())
        if patient is None:
            return None

        lines = [
            f"Patient ID: {patient.patient_id}",
            f"Age: {patient.age}",
            f"Gender: {patient.gender}",
            f"BMI: {patient.bmi}",
            f"A1c: {'missing' if patient.a1c is None else patient.a1c}",
            f"Blood pressure: {patient.bp_sys}/{patient.bp_dia}",
            f"Smoking: {patient.smoking}",
            f"Total encounters: {patient.encounter_count()}",
        ]
        recent = patient.most_recent_encounter()
        if recent:
            provider = recent.provider.name if recent.provider else recent.provider_id
            department = recent.department.name if recent.department else recent.department_id
            lines.extend(
                [
                    "",
                    "Most recent visit:",
                    f"Encounter ID: {recent.encounter_id}",
                    f"Date: {recent.encounter_date}",
                    f"Type: {recent.encounter_type}",
                    f"Provider: {provider}",
                    f"Department: {department}",
                    f"Procedure cost: ${recent.total_cost():,.2f}",
                    f"Notes on encounter: {len(recent.notes)}",
                ]
            )
        return "\n".join(lines)

    def add_patient_or_visit(self, values: dict[str, Any]) -> str:
        patient_id = str(values.get("patient_id", "")).strip()
        if not patient_id:
            raise ValueError("Patient_ID is required.")

        existing_patient = patient_id in self.patients
        if not existing_patient:
            self.patients[patient_id] = Patient(
                patient_id=patient_id,
                age=self._required_int(values, "age"),
                gender=self._required_text(values, "gender"),
                bmi=self._required_float(values, "bmi"),
                a1c=self._optional_float(values.get("a1c")),
                bp_sys=self._required_int(values, "bp_sys"),
                bp_dia=self._required_int(values, "bp_dia"),
                smoking=str(values.get("smoking", "")).strip().lower() in {"true", "yes", "1"},
            )

        encounter_date = str(values.get("encounter_date", "")).strip()
        if existing_patient and not encounter_date:
            raise ValueError("Existing patients need a Visit_time/date for the new visit.")

        added_visit = False
        if encounter_date:
            self._validate_date(encounter_date)
            provider_id = self._required_text(values, "provider_id")
            department_id = self._required_text(values, "department_id")
            if provider_id not in self.providers:
                raise ValueError(f"Provider_ID {provider_id} does not exist.")
            if department_id not in self.departments:
                raise ValueError(f"Department_ID {department_id} does not exist.")

            # Existing patients receive a new encounter; new patients may also start with one.
            encounter_id = self._random_unique_id("E", self.encounters)
            self.encounters[encounter_id] = Encounter(
                encounter_id=encounter_id,
                patient_id=patient_id,
                provider_id=provider_id,
                department_id=department_id,
                encounter_date=encounter_date,
                encounter_type=str(values.get("encounter_type", "Outpatient")).strip() or "Outpatient",
            )
            note_text = str(values.get("note_text", "")).strip()
            if note_text:
                note_id = self._random_unique_id("N", self.notes)
                self.notes[note_id] = Note(
                    note_id=note_id,
                    patient_id=patient_id,
                    encounter_id=encounter_id,
                    note_date=encounter_date,
                    note_type=str(values.get("note_type", "Progress")).strip() or "Progress",
                    note_text=note_text,
                )
            added_visit = True

        self.relink()
        self.persist_changes()
        if existing_patient:
            return f"Added new visit for existing patient {patient_id}."
        if added_visit:
            return f"Added new patient {patient_id} with an initial visit."
        return f"Added new patient {patient_id}."

    def remove_patient(self, patient_id: str) -> bool:
        patient_id = patient_id.strip()
        if patient_id not in self.patients:
            return False
        del self.patients[patient_id]
        removed_encounter_ids = {eid for eid, e in self.encounters.items() if e.patient_id == patient_id}
        self.encounters = {eid: e for eid, e in self.encounters.items() if e.patient_id != patient_id}
        self.procedures = {
            pid: p
            for pid, p in self.procedures.items()
            if p.patient_id != patient_id and p.encounter_id not in removed_encounter_ids
        }
        self.notes = {
            nid: n
            for nid, n in self.notes.items()
            if n.patient_id != patient_id and n.encounter_id not in removed_encounter_ids
        }
        self.relink()
        self.persist_changes()
        return True

    def count_visits(self, visit_date: str) -> dict[str, Any]:
        visit_date = visit_date.strip()
        self._validate_date(visit_date)
        matches = [e for e in self.encounters.values() if e.encounter_date == visit_date]
        by_patient: dict[str, int] = {}
        by_department: dict[str, int] = {}
        for encounter in matches:
            by_patient[encounter.patient_id] = by_patient.get(encounter.patient_id, 0) + 1
            department = encounter.department.name if encounter.department else encounter.department_id
            by_department[department] = by_department.get(department, 0) + 1
        return {
            "date": visit_date,
            "total": len(matches),
            "by_patient": dict(sorted(by_patient.items())),
            "by_department": dict(sorted(by_department.items())),
        }

    def view_notes(self, patient_id: str, note_date: str) -> str:
        patient_id = patient_id.strip()
        note_date = note_date.strip()
        self._validate_date(note_date)
        matches = [
            note
            for note in self.notes.values()
            if note.patient_id == patient_id and note.note_date == note_date
        ]
        if not matches:
            return "No notes found for that patient and date."
        blocks = []
        for note in sorted(matches, key=lambda item: item.note_id):
            blocks.append(
                f"Note ID: {note.note_id}\n"
                f"Date: {note.note_date}\n"
                f"Type: {note.note_type}\n"
                f"Encounter ID: {note.encounter_id}\n\n"
                f"{note.note_text}"
            )
        return "\n\n---\n\n".join(blocks)

    def count_encounters_per_patient(self) -> dict[str, int]:
        return {pid: patient.encounter_count() for pid, patient in sorted(self.patients.items())}

    def count_encounters_by_department(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for department_id, department in sorted(self.departments.items()):
            result[f"{department_id} - {department.name}"] = department.encounter_count()
        return result

    def identify_eligible_patients(self) -> list[str]:
        return sorted(
            patient.patient_id
            for patient in self.patients.values()
            if patient.matches_eligibility_criteria()
        )

    def generate_key_statistics(self, output_folder: str) -> str:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        ages = [patient.age for patient in self.patients.values()]
        bmis = [patient.bmi for patient in self.patients.values()]
        a1cs = [patient.a1c for patient in self.patients.values() if patient.a1c is not None]
        gender_counts: dict[str, int] = {}
        for patient in self.patients.values():
            gender_counts[patient.gender] = gender_counts.get(patient.gender, 0) + 1

        lines = [
            "Clinical Data Warehouse Key Statistics",
            "======================================",
            f"Patients: {len(self.patients)}",
            f"Providers: {len(self.providers)}",
            f"Departments: {len(self.departments)}",
            f"Encounters: {len(self.encounters)}",
            f"Procedures: {len(self.procedures)}",
            f"Clinical notes: {len(self.notes)}",
            "",
            "Patient summary:",
            f"Average age: {statistics.mean(ages):.1f}" if ages else "Average age: n/a",
            f"Average BMI: {statistics.mean(bmis):.1f}" if bmis else "Average BMI: n/a",
            f"Average A1c: {statistics.mean(a1cs):.1f}" if a1cs else "Average A1c: n/a",
            "",
            "Gender counts:",
        ]
        lines.extend(f"{gender}: {count}" for gender, count in sorted(gender_counts.items()))
        lines.extend(["", "Encounters by department:"])
        lines.extend(f"{department}: {count}" for department, count in self.count_encounters_by_department().items())
        lines.extend(["", f"Eligible patients: {len(self.identify_eligible_patients())}"])

        content = "\n".join(lines)
        (output_path / "key_statistics.txt").write_text(content, encoding="utf-8")
        self._write_gender_plot(output_path, gender_counts)
        return content

    def monitor_department_revenue(self) -> dict[str, float]:
        revenue = {department_id: 0.0 for department_id in self.departments}
        for encounter in self.encounters.values():
            revenue.setdefault(encounter.department_id, 0.0)
            revenue[encounter.department_id] += encounter.total_cost()
        return {key: round(value, 2) for key, value in sorted(revenue.items())}

    def monitor_provider_workload(self) -> list[tuple[str, str, int]]:
        workload = [
            (provider.provider_id, provider.name, provider.encounter_count())
            for provider in self.providers.values()
        ]
        return sorted(workload, key=lambda item: item[2], reverse=True)

    def export_dict_to_csv(self, filename: str, rows: dict[str, object], output_folder: str) -> Path:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path / filename
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["key", "value"])
            writer.writerows(rows.items())
        return file_path

    def export_workload_to_csv(self, output_folder: str) -> Path:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path / "provider_workload.csv"
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["provider_id", "provider_name", "encounter_count"])
            writer.writerows(self.monitor_provider_workload())
        return file_path

    def _random_unique_id(self, prefix: str, existing: dict[str, Any]) -> str:
        while True:
            value = f"{prefix}{random.randint(100000, 999999)}"
            if value not in existing:
                return value

    def _validate_date(self, value: str) -> None:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as error:
            raise ValueError("Date must use YYYY-MM-DD format.") from error

    def _required_text(self, values: dict[str, Any], key: str) -> str:
        value = str(values.get(key, "")).strip()
        if not value:
            raise ValueError(f"{key} is required.")
        return value

    def _required_int(self, values: dict[str, Any], key: str) -> int:
        return int(float(self._required_text(values, key)))

    def _required_float(self, values: dict[str, Any], key: str) -> float:
        return float(self._required_text(values, key))

    def _optional_float(self, value: object) -> float | None:
        text = str(value or "").strip()
        return None if not text else float(text)

    def _write_gender_plot(self, output_path: Path, gender_counts: dict[str, int]) -> None:
        try:
            import matplotlib.pyplot as plt
        except Exception:
            return
        if not gender_counts:
            return
        labels = list(gender_counts.keys())
        counts = list(gender_counts.values())
        plt.figure(figsize=(7, 4))
        plt.bar(labels, counts)
        plt.title("Patient Count by Gender")
        plt.xlabel("Gender")
        plt.ylabel("Patients")
        plt.tight_layout()
        plt.savefig(output_path / "patient_gender_counts.png")
        plt.close()
