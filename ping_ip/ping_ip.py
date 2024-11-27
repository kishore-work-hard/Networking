import pandas as pd
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor


def ping_ip(ip):
    """Ping the given IP and return whether it's alive or dead."""
    try:
        os_name = platform.system().lower()
        if "windows" in os_name:
            result = subprocess.run(["ping", "-n", "1", "-w", "1000", ip],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            result = subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "ALIVE" if result.returncode == 0 else "DEAD"
    except Exception as e:
        return f"Error: {e}"


def process_sheet(sheet):
    """Ping IPs in the sheet and update the STATUS column."""
    if "IP" in sheet.columns:
        sheet["STATUS"] = sheet["IP"].apply(ping_ip)
    return sheet


def process_excel(file_path, output_path, max_workers=10):
    """Read Excel file, ping IPs, update STATUS, and save the result."""
    writer = pd.ExcelWriter(output_path, engine="openpyxl")  # Output file
    sheets = pd.read_excel(file_path, sheet_name=None)  # Read all sheets

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_sheet, sheet): name for name, sheet in sheets.items()}
        for future in futures:
            sheet_name = futures[future]
            try:
                updated_sheet = future.result()
                updated_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception as e:
                print(f"Error processing sheet {sheet_name}: {e}")

    writer.close()  # Use close() instead of save()
    print(f"Updated Excel saved at: {output_path}")


# Example Usage
process_excel("IP.xlsx", "output.xlsx", max_workers=20)
