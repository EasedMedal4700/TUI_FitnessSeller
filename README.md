# TUI Fitness Seller

A terminal-based UI (TUI) for managing shipping container data: reading Excel files,
fetching container tracking HTML, extracting ETAs, downloading attachments, and cleaning up old data.

---

## Project structure

```
TUI_FitnessSeller/
├── main.py                    # Entry point
├── config.yaml                # Runtime configuration (Excel path, etc.)
├── requirements.txt
├── input/                     # Place your containers.xlsx here
├── data/
│   ├── containers_data.csv    # Generated from Excel
│   ├── etas.json / etas.csv   # Extracted ETAs
│   └── container_HTML/        # Fetched HTML + JSON + downloaded attachments
└── code/
    ├── common/
    │   ├── base_screen.py     # BaseScreen: shared arrow-key nav + back/exit handling
    │   └── nav_buttons.py     # BackHome, ExitApp buttons (ExitApp shows confirm dialog)
    ├── models/                # M in MVC — pure business logic, no Textual imports
    │   ├── containers_model.py  # Excel → CSV read/write
    │   ├── clean_model.py       # CSV backup, download organiser, attachment cleaner
    │   └── html_model.py        # Fetch HTML, parse tracking/POD, download attachments
    ├── home_screen.py         # Home menu (V)
    ├── read_containers.py     # Containers + Clean screens + ContainerApp (C/entry)
    ├── html_screen.py         # Fetch Container HTML screen
    ├── eta_screen.py          # Extract ETAs screen
    └── download_screen.py     # Download Attachments screen
```

---

## Setup

### Prerequisites
- Python 3.11+
- A virtual environment (recommended)

### Install

```powershell
cd d:\code\TUI_FitnessSeller
.\.venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt
```

```bash
source .venv/bin/activate              # macOS / Linux / Git Bash
pip install -r requirements.txt
```

### config.yaml

```yaml
excel_file: input/containers.xlsx
```

---

## Running

```powershell
python main.py
```

---

## Navigation

| Key | Action |
|-----|--------|
| `←` / `↑` | Focus previous button |
| `→` / `↓` | Focus next button |
| `Enter` | Activate focused button |
| `↑` / `↓` (on list) | Move through menu items |

---

## Screens

### Home
Central menu. Choose any feature from the list; press `Enter` to open it.

### Read Containers
- **Process File** — reads `input/containers.xlsx`, writes `data/containers_data.csv`
- **Print Data** — displays the CSV in the output area
- **Clean Data** — opens the Clean Data screen

### Fetch Container HTML
- **Fetch All HTML** — for every URL in the CSV, downloads the tracking page HTML, parses
  tracking events and POD data, saves `data/container_HTML/<stem>.html` and `.json`
- **List Files** — shows all files in `data/container_HTML/` grouped by container

### Extract ETAs
- **Run ETA Extraction** — scans all JSON files in `data/container_HTML/`, extracts ETA entries,
  writes `data/etas.json` and `data/etas.csv`, then displays a summary table

### Download Attachments
- **Run Attachment Downloader** — scans JSON files for packing lists, invoices, and bills of lading;
  downloads them into `data/container_HTML/` and updates the JSON `attachments` list

### Clean Data
- **Clean CSV** — backs up `data/containers_data.csv` with a timestamp, then creates a fresh empty one
- **Organize Downloads** — moves files from `data/container_HTML/` into:
  - `data/html/` — `.html` / `.htm`
  - `data/json/` — `.json`
  - `data/pdfs/` — `.pdf`
  - `data/other/` — everything else
- **Clean Attachments** — moves downloader-created attachment files to a timestamped backup folder
  (`data/attachments_backup_YYYYMMDD_HHMMSS/`) and clears attachment lists from JSONs

---

## MVC design

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Model** | `code/models/` | All file I/O, network requests, parsing — no Textual |
| **View** | `code/*_screen.py` | Compose UI, display results from model |
| **Controller** | `ContainerApp` in `read_containers.py` | Screen registry, app lifecycle |

Shared behaviour (arrow-key navigation, Back to Home, Exit with confirmation) lives in
`code/common/base_screen.py` and `code/common/nav_buttons.py` so it is never duplicated.

---

## Exit confirmation

Pressing **Exit** on any screen shows a confirmation dialog ("Are you sure you want to exit?").
Press `Yes` to quit or `No` to cancel.
