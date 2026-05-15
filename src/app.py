import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Callable

from src.clinical_data_system import ClinicalDataSystem
from src.data_loader import DataLoader
from src.usage_logger import UsageLogger
from src.user import User


COLORS = {
    "background": "#f4f7fb",
    "card": "#ffffff",
    "text": "#1f2937",
    "muted": "#64748b",
    "primary": "#2563eb",
    "primary_dark": "#1d4ed8",
}


class ClinicalDataApp:
    """Main UI application class."""

    def __init__(self, data_folder: str = "Data", output_folder: str = "output") -> None:
        self.data_folder = data_folder
        self.output_folder = output_folder
        self.loader = DataLoader(data_folder)
        self.logger = UsageLogger(output_folder)
        self.users: dict[str, User] = {}
        self.system: ClinicalDataSystem | None = None
        self.current_user: User | None = None

        self.root = tk.Tk()
        self.root.title("Clinical Data Warehouse")
        self.root.geometry("880x650")
        self.root.minsize(760, 560)
        self.root.configure(bg=COLORS["background"])

        self.main_frame = ttk.Frame(self.root, padding=28, style="App.TFrame")
        self.main_frame.pack(fill="both", expand=True)
        self.configure_styles()

    def run(self) -> None:
        try:
            self.users = self.loader.load_users()
        except FileNotFoundError:
            messagebox.showerror(
                "Missing Data files",
                "Could not find Data/credentials.csv. Run python data_generator.py first.",
            )
            self.root.destroy()
            return
        self.show_login()
        self.root.mainloop()

    def configure_styles(self) -> None:
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.style.configure("App.TFrame", background=COLORS["background"])
        self.style.configure("Card.TFrame", background=COLORS["card"], relief="flat")
        self.style.configure(
            "Title.TLabel",
            background=COLORS["card"],
            foreground=COLORS["text"],
            font=("Arial", 24, "bold"),
            padding=(0, 6),
        )
        self.style.configure(
            "Subtitle.TLabel",
            background=COLORS["card"],
            foreground=COLORS["muted"],
            font=("Arial", 11),
        )
        self.style.configure(
            "Field.TLabel",
            background=COLORS["card"],
            foreground=COLORS["text"],
            font=("Arial", 10, "bold"),
        )
        self.style.configure("Menu.TButton", font=("Arial", 11, "bold"), padding=10)
        self.style.configure(
            "Primary.TButton",
            font=("Arial", 11, "bold"),
            padding=(14, 9),
            background=COLORS["primary"],
            foreground="white",
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", COLORS["primary_dark"]), ("pressed", COLORS["primary_dark"])],
            foreground=[("active", "white"), ("pressed", "white")],
        )
        self.style.configure("TEntry", padding=6)

    def clear_frame(self) -> None:
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_login(self) -> None:
        self.clear_frame()
        card = ttk.Frame(self.main_frame, padding=38, style="Card.TFrame")
        card.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(card, text="Clinical Data Warehouse", style="Title.TLabel").pack()
        ttk.Label(card, text="Log in with your assigned username and password.", style="Subtitle.TLabel").pack(pady=(0, 20))

        form = ttk.Frame(card, style="Card.TFrame")
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Username", style="Field.TLabel").grid(row=0, column=0, sticky="e", padx=(0, 14), pady=8)
        username_entry = ttk.Entry(form, width=34)
        username_entry.grid(row=0, column=1, sticky="ew", pady=8)

        ttk.Label(form, text="Password", style="Field.TLabel").grid(row=1, column=0, sticky="e", padx=(0, 14), pady=8)
        password_entry = ttk.Entry(form, width=34, show="*")
        password_entry.grid(row=1, column=1, sticky="ew", pady=8)

        def attempt_login() -> None:
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            user = self.users.get(username)
            if user is None or not user.check_password(password):
                self.logger.log(username, "", "login", "failed", "Invalid username or password")
                messagebox.showerror("Login failed", "Invalid username or password.")
                return

            try:
                self.system = ClinicalDataSystem(self.loader)
            except FileNotFoundError as error:
                messagebox.showerror("Missing Data file", f"Could not load clinical data:\n\n{error}")
                return

            self.current_user = user
            self.logger.log(user.username, user.role, "login", "success", "User logged in")
            self.show_menu()

        ttk.Button(form, text="Log in", command=attempt_login, style="Primary.TButton").grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(18, 0),
        )
        password_entry.bind("<Return>", lambda _event: attempt_login())
        username_entry.focus_set()

    def show_menu(self) -> None:
        if self.current_user is None:
            self.show_login()
            return

        self.clear_frame()
        user = self.current_user
        ttk.Label(self.main_frame, text=f"Welcome, {user.username}", style="Title.TLabel").pack()
        ttk.Label(self.main_frame, text=f"Role: {user.role}", style="Subtitle.TLabel").pack(pady=(0, 20))

        buttons = self.menu_buttons_for(user)
        grid = ttk.Frame(self.main_frame)
        grid.pack()
        for index, (label, command) in enumerate(buttons):
            button = ttk.Button(grid, text=label, command=command, width=32, style="Menu.TButton")
            button.grid(row=index // 2, column=index % 2, padx=10, pady=7, sticky="ew")

        ttk.Button(self.main_frame, text="Exit", command=self.action_exit, style="Primary.TButton").pack(pady=(26, 0))

    def menu_buttons_for(self, user: User) -> list[tuple[str, Callable[[], None]]]:
        buttons: list[tuple[str, Callable[[], None]]] = []
        # Build the menu from role permissions so non-clinical users are not shown PHI actions.
        if user.can_manage_patient_records():
            buttons.extend(
                [
                    ("Retrieve_patient", self.action_retrieve_patient),
                    ("Add_patient", self.action_add_patient),
                    ("Remove_patient", self.action_remove_patient),
                    ("View_Note", self.action_view_note),
                    ("Identify eligible patients", self.action_identify_eligible),
                ]
            )
        if user.can_count_visits():
            buttons.extend(
                [
                    ("Count_visits", self.action_count_visits),
                    ("Count encounters per patient", self.action_encounters_per_patient),
                    ("Count encounters by department", self.action_encounters_by_department),
                ]
            )
        if user.can_generate_statistics():
            buttons.append(("Generate key statistics", self.action_generate_statistics))
        if user.can_monitor_workload():
            buttons.append(("Monitor_workload", self.action_monitor_workload))
        if user.can_monitor_revenue():
            buttons.append(("Monitor_revenue", self.action_monitor_revenue))
        return buttons

    def require_system(self) -> ClinicalDataSystem:
        if self.system is None:
            raise RuntimeError("Clinical data has not been loaded.")
        return self.system

    def log_action(self, action: str, detail: str = "") -> None:
        if self.current_user:
            self.logger.log(self.current_user.username, self.current_user.role, action, "success", detail)

    def show_text_window(self, title: str, content: str) -> None:
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("760x520")
        frame = ttk.Frame(window, padding=12)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, wrap="word", font=("Consolas", 10))
        text.insert("1.0", content)
        text.configure(state="disabled")
        text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.configure(yscrollcommand=scrollbar.set)

    def action_retrieve_patient(self) -> None:
        patient_id = simpledialog.askstring("Retrieve_patient", "Enter Patient_ID:", parent=self.root)
        if not patient_id:
            return
        result = self.require_system().retrieve_patient(patient_id)
        if result is None:
            messagebox.showwarning("Not found", f"Patient {patient_id} was not found.")
            return
        self.show_text_window("Patient information", result)
        self.log_action("retrieve_patient", patient_id)

    def action_add_patient(self) -> None:
        system = self.require_system()
        window = tk.Toplevel(self.root)
        window.title("Add_patient")
        window.geometry("620x680")
        frame = ttk.Frame(window, padding=16)
        frame.pack(fill="both", expand=True)

        help_text = (
            "Enter Patient_ID. If it already exists, only visit fields are required. "
            "If it is new, demographic fields are required. A note may be added with the visit."
        )
        ttk.Label(frame, text=help_text, wraplength=560).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        entries: dict[str, tk.Widget] = {}
        fields = [
            ("patient_id", "Patient_ID"),
            ("age", "Age"),
            ("gender", "Gender"),
            ("bmi", "BMI"),
            ("a1c", "A1c"),
            ("bp_sys", "Systolic BP"),
            ("bp_dia", "Diastolic BP"),
            ("smoking", "Smoking"),
            ("encounter_date", "Visit_time/date (YYYY-MM-DD)"),
            ("provider_id", "Provider_ID"),
            ("department_id", "Department_ID"),
            ("encounter_type", "Encounter type"),
            ("note_type", "Note type"),
            ("note_text", "Note text / chief complaint"),
        ]
        for row_index, (key, label) in enumerate(fields, start=1):
            ttk.Label(frame, text=label + ":").grid(row=row_index, column=0, sticky="e", padx=6, pady=5)
            if key == "gender":
                widget = ttk.Combobox(frame, values=["Female", "Male", "Non-binary"], width=34)
            elif key == "smoking":
                widget = ttk.Combobox(frame, values=["False", "True"], width=34)
                widget.set("False")
            elif key == "encounter_type":
                widget = ttk.Combobox(frame, values=["Outpatient", "Inpatient", "Emergency"], width=34)
                widget.set("Outpatient")
            elif key == "note_type":
                widget = ttk.Combobox(frame, values=["Progress", "Nursing", "Consult", "Discharge"], width=34)
                widget.set("Progress")
            else:
                widget = ttk.Entry(frame, width=37)
            widget.grid(row=row_index, column=1, sticky="w", padx=6, pady=5)
            entries[key] = widget

        provider_examples = ", ".join(sorted(system.providers)[:8])
        departments = ", ".join(f"{key}={value.name}" for key, value in sorted(system.departments.items()))
        ttk.Label(frame, text=f"Provider examples: {provider_examples}", wraplength=560).grid(row=15, column=0, columnspan=2, pady=(10, 2))
        ttk.Label(frame, text=f"Departments: {departments}", wraplength=560).grid(row=16, column=0, columnspan=2, pady=(0, 10))

        def value(key: str) -> str:
            widget = entries[key]
            return widget.get().strip()  # type: ignore[union-attr]

        def submit() -> None:
            values = {key: value(key) for key, _label in fields}
            try:
                message = system.add_patient_or_visit(values)
            except Exception as error:
                messagebox.showerror("Could not save", str(error))
                return
            self.log_action("add_patient", values["patient_id"])
            messagebox.showinfo("Saved", message)
            window.destroy()

        ttk.Button(frame, text="Submit", command=submit, style="Primary.TButton").grid(row=17, column=0, columnspan=2, pady=12)

    def action_remove_patient(self) -> None:
        patient_id = simpledialog.askstring("Remove_patient", "Enter Patient_ID:", parent=self.root)
        if not patient_id:
            return
        if not messagebox.askyesno("Confirm", f"Remove all information for {patient_id}?"):
            return
        removed = self.require_system().remove_patient(patient_id)
        if removed:
            messagebox.showinfo("Removed", f"Patient {patient_id} and related records were removed.")
            self.log_action("remove_patient", patient_id)
        else:
            messagebox.showwarning("Not found", f"Patient {patient_id} was not found.")

    def action_count_visits(self) -> None:
        visit_date = simpledialog.askstring("Count_visits", "Enter date (YYYY-MM-DD):", parent=self.root)
        if not visit_date:
            return
        try:
            result = self.require_system().count_visits(visit_date)
        except ValueError as error:
            messagebox.showerror("Invalid date", str(error))
            return
        lines = [f"Date: {result['date']}", f"Total visits: {result['total']}", "", "Visits per patient:"]
        lines.extend(f"{key}: {value}" for key, value in result["by_patient"].items())
        lines.extend(["", "Visits by department:"])
        lines.extend(f"{key}: {value}" for key, value in result["by_department"].items())
        self.show_text_window("Visit counts", "\n".join(lines))
        self.log_action("count_visits", visit_date)

    def action_view_note(self) -> None:
        patient_id = simpledialog.askstring("View_Note", "Enter Patient_ID:", parent=self.root)
        if not patient_id:
            return
        note_date = simpledialog.askstring("View_Note", "Enter note date (YYYY-MM-DD):", parent=self.root)
        if not note_date:
            return
        try:
            result = self.require_system().view_notes(patient_id, note_date)
        except ValueError as error:
            messagebox.showerror("Invalid date", str(error))
            return
        self.show_text_window("Clinical notes", result)
        self.log_action("view_note", f"{patient_id} {note_date}")

    def action_identify_eligible(self) -> None:
        ids = self.require_system().identify_eligible_patients()
        self.show_text_window("Eligible patients", f"Eligible patients: {len(ids)}\n\n" + "\n".join(ids))
        self.log_action("identify_eligible_patients", str(len(ids)))

    def action_generate_statistics(self) -> None:
        content = self.require_system().generate_key_statistics(self.output_folder)
        self.show_text_window("Key statistics", content + "\n\nSaved to output/key_statistics.txt")
        self.log_action("generate_key_statistics", "output/key_statistics.txt")

    def action_encounters_per_patient(self) -> None:
        result = self.require_system().count_encounters_per_patient()
        self.require_system().export_dict_to_csv("encounters_per_patient.csv", result, self.output_folder)
        self.show_text_window("Encounters per patient", "\n".join(f"{k}: {v}" for k, v in result.items()))
        self.log_action("count_encounters_per_patient", "output/encounters_per_patient.csv")

    def action_encounters_by_department(self) -> None:
        result = self.require_system().count_encounters_by_department()
        self.require_system().export_dict_to_csv("encounters_by_department.csv", result, self.output_folder)
        self.show_text_window("Encounters by department", "\n".join(f"{k}: {v}" for k, v in result.items()))
        self.log_action("count_encounters_by_department", "output/encounters_by_department.csv")

    def action_monitor_workload(self) -> None:
        workload = self.require_system().monitor_provider_workload()
        self.require_system().export_workload_to_csv(self.output_folder)
        lines = ["Provider workload ranking:", ""]
        lines.extend(f"{provider_id} ({name}): {count} encounters" for provider_id, name, count in workload)
        self.show_text_window("Provider workload", "\n".join(lines) + "\n\nSaved to output/provider_workload.csv")
        self.log_action("monitor_provider_workload", "output/provider_workload.csv")

    def action_monitor_revenue(self) -> None:
        revenue = self.require_system().monitor_department_revenue()
        self.require_system().export_dict_to_csv("department_revenue.csv", revenue, self.output_folder)
        lines = ["Department revenue:", ""]
        for department_id, total in revenue.items():
            department = self.require_system().departments.get(department_id)
            label = department.name if department else department_id
            lines.append(f"{department_id} ({label}): ${total:,.2f}")
        self.show_text_window("Department revenue", "\n".join(lines) + "\n\nSaved to output/department_revenue.csv")
        self.log_action("monitor_department_revenue", "output/department_revenue.csv")

    def action_exit(self) -> None:
        if self.current_user:
            self.logger.log(self.current_user.username, self.current_user.role, "exit", "success", "User exited")
        self.root.destroy()


def default_paths() -> tuple[str, str]:
    base_dir = Path(__file__).resolve().parent.parent
    return str(base_dir / "Data"), str(base_dir / "output")
