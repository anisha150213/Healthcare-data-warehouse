import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

NUM_PATIENTS = 200
NUM_PROVIDERS = 20
NUM_ENCOUNTERS = 400
NUM_PROCEDURES = 250
NUM_NOTES = 350
DATA_DIR = Path("Data")

random.seed(42)


def write_csv(filename, header, rows):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def generate_credentials():
    rows = [
        ["alice", "pass123", "clinician"],
        ["brandon", "pass124", "clinician"],
        ["carmen", "pass125", "clinician"],
        ["nina", "pass201", "nurse"],
        ["omar", "pass202", "nurse"],
        ["paige", "pass203", "nurse"],
        ["dave", "pass000", "admin"],
        ["erin", "admin456", "admin"],
        ["frank", "admin789", "admin"],
        ["carol", "pass789", "management"],
        ["mia", "mgmt456", "management"],
        ["sam", "mgmt789", "management"],
    ]

    write_csv("credentials.csv", ["username", "password", "role"], rows)


def generate_patients():
    genders = ["Male", "Female", "Non-binary"]
    rows = []

    for i in range(NUM_PATIENTS):
        patient = [
            f"P{i+1}",
            random.randint(18, 90),
            random.choice(genders),
            round(random.uniform(18, 40), 1),
            "" if random.random() < 0.1 else round(random.uniform(4.5, 10.0), 1),
            random.randint(100, 170),
            random.randint(60, 100),
            random.choice([True, False]),
        ]
        rows.append(patient)

    write_csv(
        "patients.csv",
        ["patient_id", "age", "gender", "bmi", "a1c", "bp_sys", "bp_dia", "smoking"],
        rows,
    )


def generate_providers():
    specialties = [
        "Cardiology",
        "Primary Care",
        "Endocrinology",
        "Pulmonology",
        "Oncology",
        "Pediatric",
        "Emergency Medicine",
    ]

    rows = []

    for i in range(NUM_PROVIDERS):
        rows.append([
            f"PR{i+1}",
            f"Dr_{i+1}",
            random.choice(specialties),
            f"D{random.randint(1, 4)}",
        ])

    write_csv("providers.csv", ["provider_id", "name", "specialty", "department_id"], rows)


def generate_departments():
    departments = [
        ("D1", "Cardiology", "Building A"),
        ("D2", "Primary Care", "Building B"),
        ("D3", "Endocrinology", "Building C"),
        ("D4", "Pulmonology", "Building D"),
    ]

    write_csv("departments.csv", ["department_id", "name", "location"], departments)


def generate_encounters():
    encounter_types = ["Outpatient", "Inpatient", "Emergency"]
    rows = []

    for i in range(NUM_ENCOUNTERS):
        date = datetime.today() - timedelta(days=random.randint(0, 365))

        patient_id = f"P{random.randint(1, NUM_PATIENTS)}"
        provider_id = f"PR{random.randint(1, NUM_PROVIDERS)}"
        department_id = f"D{random.randint(1, 4)}"

        rows.append([
            f"E{i+1}",
            patient_id,
            provider_id,
            department_id,
            date.strftime("%Y-%m-%d"),
            random.choice(encounter_types),
        ])

    write_csv(
        "encounters.csv",
        ["encounter_id", "patient_id", "provider_id", "department_id", "encounter_date", "encounter_type"],
        rows,
    )

    return rows


def generate_procedures(encounters):
    procedure_catalog = [
        ("93000", "Electrocardiogram"),
        ("80053", "Metabolic Panel"),
        ("83036", "Hemoglobin A1C Test"),
        ("71020", "Chest X-Ray"),
        ("85025", "Complete Blood Count"),
        ("80048", "Basic Metabolic Panel"),
        ("84443", "Thyroid Stimulating Hormone Test"),
        ("80061", "Lipid Panel"),
        ("85610", "Prothrombin Time Test"),
        ("81001", "Urinalysis"),
        ("82565", "Creatinine Blood Test"),
        ("82947", "Glucose Blood Test"),
        ("83540", "Iron Test"),
        ("84153", "Prostate Specific Antigen Test"),
        ("90658", "Influenza Vaccination"),
        ("90471", "Immunization Administration"),
        ("90715", "Tdap Vaccination"),
        ("90732", "Pneumococcal Vaccination"),
        ("71045", "Chest X-Ray Single View"),
        ("71250", "CT Scan Chest"),
        ("70450", "CT Scan Head"),
        ("74176", "CT Scan Abdomen"),
        ("93306", "Echocardiogram"),
        ("93880", "Carotid Ultrasound"),
        ("76700", "Abdominal Ultrasound"),
        ("45378", "Colonoscopy"),
        ("43235", "Upper GI Endoscopy"),
        ("99213", "Office Visit Established Patient"),
        ("12001", "Simple Wound Repair"),
        ("17000", "Skin Lesion Removal"),
        ("20610", "Joint Injection"),
    ]

    rows = []

    for i in range(NUM_PROCEDURES):
        code, name = random.choice(procedure_catalog)

        encounter = random.choice(encounters)
        encounter_id = encounter[0]
        patient_id = encounter[1]

        rows.append([
            f"PROC{i+1}",
            encounter_id,
            patient_id,
            code,
            name,
            round(random.uniform(100, 2000), 2),
        ])

    write_csv(
        "procedures.csv",
        ["procedure_id", "encounter_id", "patient_id", "procedure_code", "procedure_name", "cost"],
        rows,
    )


def generate_notes(encounters):
    note_types = [
        "Progress",
        "Discharge",
        "Nursing",
        "Consult",
        "Oncology",
        "Emergency",
    ]

    note_templates = [
        "Patient was evaluated during this encounter. Symptoms were reviewed and care plan was discussed.",
        "Patient reports ongoing symptoms. Medication and follow-up instructions were provided.",
        "Clinical assessment completed. Patient advised to return if symptoms worsen.",
        "Care team reviewed patient history, current concerns, and treatment options.",
        "Patient tolerated the visit well. Follow-up appointment recommended.",
        "Provider discussed test results and answered patient questions.",
    ]

    rows = []

    for i in range(NUM_NOTES):
        encounter = random.choice(encounters)

        encounter_id = encounter[0]
        patient_id = encounter[1]
        encounter_date = encounter[4]

        rows.append([
            f"N{i+1}",
            patient_id,
            encounter_id,
            encounter_date,
            random.choice(note_types),
            random.choice(note_templates),
        ])

    write_csv(
        "notes.csv",
        ["note_id", "patient_id", "encounter_id", "note_date", "note_type", "note_text"],
        rows,
    )


def main():
    generate_credentials()
    generate_patients()
    generate_providers()
    generate_departments()

    encounters = generate_encounters()
    generate_procedures(encounters)
    generate_notes(encounters)

    print("Synthetic dataset generated.")
    print("Generated files:")
    print("- Data/credentials.csv")
    print("- Data/patients.csv")
    print("- Data/providers.csv")
    print("- Data/departments.csv")
    print("- Data/encounters.csv")
    print("- Data/procedures.csv")
    print("- Data/notes.csv")


if __name__ == "__main__":
    main()