# TUI Fitness Seller

This project contains a Python script to read data from an Excel file named `containers.xlsx`.

## Prerequisites

- Python 3.x installed
- Virtual environment set up in `.venv` with `openpyxl` installed

## Setup

1. Activate the virtual environment:
   - On Windows: `.\.venv\Scripts\Activate.ps1`
   - On macOS/Linux: `source .venv/bin/activate`

Running from a different drive (Windows)

If your project folder is on the `C:` drive (for example `C:\code\TUI_FitnessSeller`), open PowerShell or Command Prompt and run:

- PowerShell:

```powershell
C:\
cd d:\code\TUI_FitnessSeller
.\.venv\Scripts\Activate.ps1
pip install openpyxl textual requests beautifulsoup4 lxml
python main.py
```

- Command Prompt (cmd.exe):

```cmd
C:
cd \code\TUI_FitnessSeller
.\\.venv\\Scripts\\activate.bat
pip install openpyxl textual requests beautifulsoup4 lxml
python main.py
```

If you use Git Bash or WSL, use the appropriate `activate` command for that shell (e.g., `source .venv/bin/activate`).

## Running the Script

1. Place the `containers.xlsx` file in the `input/` directory.
2. Update `config.yaml` with the path to the Excel file if needed (default: `input/containers.xlsx`).
3. Run the TUI: `python main.py`

The TUI allows you to process the file (reads data, saves to `data/containers_data.csv`), and print the data in the interface.