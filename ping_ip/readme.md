# Ping IPs and Update Excel Sheets

This Python script processes an Excel file containing multiple sheets, each with an "IP" column. It pings the IP addresses, determines if they are "ALIVE" or "DEAD," and updates the corresponding "STATUS" column in the Excel file. The updated Excel file is saved as a new file.

---

## Features
- **Ping IPs**: Checks if IPs are reachable using the appropriate system commands for Windows or Linux/MacOS.
- **Multi-Sheet Processing**: Handles Excel files with multiple sheets, updating each sheet containing an "IP" column.
- **Concurrency**: Utilizes `ThreadPoolExecutor` for faster processing by pinging multiple IPs in parallel.
- **Compatibility**: Works on both Windows and Linux/MacOS.

---

## Requirements

### Python Modules
Ensure the following Python modules are installed:
- `pandas`
- `openpyxl`

Install these modules using pip:
```bash
pip install pandas openpyxl
```

### System Requirements
- Python 3.6 or higher.
- Compatible with Windows, Linux, or MacOS.

---

## Usage

1. **Prepare Input File**:
   - The input Excel file should contain one or more sheets.
   - Each sheet should have at least the following columns:
     - `IP`: The IP addresses to be pinged.
     - `STATUS`: This column will be updated with "ALIVE" or "DEAD."

2. **Run the Script**:
   ```bash
   python script.py
   ```
   Replace `script.py` with the name of your script file.

3. **Output**:
   - The updated Excel file will be saved with the name specified in the `output_path` variable (e.g., `output.xlsx`).

### Example
For an input file named `IP.xlsx`:
```python
process_excel("IP.xlsx", "output.xlsx", max_workers=20)
```
This reads `IP.xlsx`, pings the IP addresses, updates their statuses, and saves the result as `output.xlsx`.

---

## Code Explanation

### Functions
1. **`ping_ip(ip)`**:
   - Pings the given IP address and determines its status.
   - Uses system-specific commands (`ping -n` for Windows, `ping -c` for Linux/MacOS).
   - Returns:
     - `ALIVE` if the ping is successful.
     - `DEAD` if the ping fails.

2. **`process_sheet(sheet)`**:
   - Processes a single Excel sheet.
   - Applies the `ping_ip` function to the "IP" column.
   - Updates the "STATUS" column with the results.

3. **`process_excel(file_path, output_path, max_workers=10)`**:
   - Reads the entire Excel file, processes each sheet in parallel, and saves the updated data to a new file.
   - Parameters:
     - `file_path`: Path to the input Excel file.
     - `output_path`: Path to save the updated Excel file.
     - `max_workers`: Number of threads for concurrent processing.

---

## Customization
- **Concurrency**: Adjust `max_workers` to control the number of threads for parallel processing.
- **Output File Name**: Change the `output_path` variable to save the result under a different name or location.

---

## Error Handling
- If a sheet does not have an "IP" column, it will be skipped.
- Errors during sheet processing are printed but do not halt execution.

---

## Example Input
| IP            | TYPE       | USERNAME | PASSWORD | STATUS |
|---------------|------------|----------|----------|--------|
| 192.168.1.1   | Router     | admin    | admin123 |        |
| 192.168.1.2   | Switch     | user     | pass456  |        |

---

## Example Output
| IP            | TYPE       | USERNAME | PASSWORD | STATUS |
|---------------|------------|----------|----------|--------|
| 192.168.1.1   | Router     | admin    | admin123 | ALIVE  |
| 192.168.1.2   | Switch     | user     | pass456  | DEAD   |

---

## License
This project is open-source and available under the [MIT License](https://opensource.org/licenses/MIT).
