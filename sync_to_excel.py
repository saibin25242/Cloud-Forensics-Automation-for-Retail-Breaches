import pandas as pd
import os
import time

CSV_FILE = "forensic_report.csv"
EXCEL_FILE = "forensic_report.xlsx"

last_modified = 0

print("Monitoring CSV changes...")

while True:

    if os.path.exists(CSV_FILE):

        current_modified = os.path.getmtime(CSV_FILE)

        if current_modified != last_modified:

            last_modified = current_modified

            df = pd.read_csv(CSV_FILE)

            df.to_excel(EXCEL_FILE, index=False)

            print("Excel file updated!")

    time.sleep(3)