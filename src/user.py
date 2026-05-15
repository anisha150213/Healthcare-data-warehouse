# Anisha Tasnim
# tasnim@uwm.edu

class User:
    # Represents a user from credentials.csv.
    VALID_ROLES = {"admin", "clinician", "nurse", "management"}

    def __init__(self, username: str, password: str, role: str):
        self.username = username.strip()
        self.password = password.strip()
        self.role = role.strip().lower()
        if self.role not in self.VALID_ROLES:
            raise ValueError(f"Unknown role: {role}")

    def check_password(self, password: str):
        return self.password == password

    def can_access_phi(self):
        return self.role in {"clinician", "nurse"}

    def can_manage_patient_records(self):
        return self.role in {"clinician", "nurse"}

    def can_generate_statistics(self):
        return self.role in {"admin", "clinician", "nurse", "management"}

    def can_count_visits(self):
        return self.role in {"admin", "clinician", "nurse"}

    def can_monitor_workload(self):
        return self.role in {"admin", "clinician", "nurse"}

    def can_monitor_revenue(self):
        return self.role in {"management", "clinician", "nurse"}

    def can_identify_eligible_patients(self):
        return self.role in {"clinician", "nurse"}
