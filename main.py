# Anisha Tasnim
# tasnim@uwm.edu

from src.app import ClinicalDataApp, default_paths


def main():
    data_folder, output_folder = default_paths()
    app = ClinicalDataApp(data_folder=data_folder, output_folder=output_folder)
    app.run()


if __name__ == "__main__":
    main()
