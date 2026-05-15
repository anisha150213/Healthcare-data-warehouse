# Anisha Tasnim
# tasnim@uwm.edu

import csv
from datetime import datetime
from pathlib import Path


class UsageLogger:
    # Stores login attempts and actions in an easy-to-read CSV file.

    FIELDNAMES = ["timestamp", "username", "role", "action", "status", "detail"]

    def __init__(self, output_folder: str = "output"):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.log_path = self.output_folder / "usage_statistics.csv"
        if not self.log_path.exists():
            with open(self.log_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.FIELDNAMES)
                writer.writeheader()

    def log(self, username: str, role: str, action: str, status: str, detail: str = ""):
        with open(self.log_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.FIELDNAMES)
            writer.writerow(
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "username": username,
                    "role": role,
                    "action": action,
                    "status": status,
                    "detail": detail,
                }
            )
