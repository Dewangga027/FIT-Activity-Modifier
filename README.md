# FIT Activity Modifier

A professional, lightweight Python utility and GUI application designed to inspect, modify, and generate Garmin FIT (`.fit`) and CSV (`.csv`) workout activity files. Easily adjust key fitness metrics—such as Heart Rate time-series, Total Calories, Start Timestamp, and Workout Duration—before exporting or uploading directly to platforms like **Strava**. Built on top of Garmin's official **FitCSVTool**.

---

## 🔄 Workflow Architecture

```text
┌──────────────┐     ┌───────────────┐     ┌──────────────────────┐     ┌───────────────┐     ┌──────────────┐
│  FIT Binary  │ ──► │  Decode to    │ ──► │  Modify Metrics via  │ ──► │  Encode to    │ ──► │ Modified FIT │
│   Input      │     │  CSV Format   │     │  Python Algorithms   │     │  FIT Binary   │     │ Output File  │
└──────────────┘     └───────────────┘     └──────────────────────┘     └───────────────┘     └──────────────┘
```

1. **Decode:** Converts `.fit` binary files to temporary structured `.csv` files using Garmin's `FitCSVTool.jar`.
2. **Modify / Generate:** Adjusts target metrics (HR scaling, active/elapsed duration, calorie counts, timestamp offsets) or generates daily workout batches (HIIT, Running, Cycling).
3. **Encode:** Re-encodes the modified/generated `.csv` data back into a compliant `.fit` binary file.
4. **Upload (Optional):** Automatically pushes the modified FIT activity to Strava via the REST API.

---

## ✨ Features

- **Dual Graphical & Command Line Interface:** 
  - **GUI (`tkinter` & `matplotlib`):** Interactive visual editor featuring side-by-side Heart Rate BPM comparison charts, duration presets, single/batch workout creation tabs, and Strava activity manager.
  - **CLI Mode:** Command-line options ideal for batch processing, automated scripts, and server/headless environments.
- **Proportional Heart Rate Scaling:** Adjusts average HR (bpm) across the entire workout time-series while preserving natural physiological variance and boundaries (40–220 bpm).
- **Humanized HR Algorithm (Generative Mode):** Simulates realistic physiological patterns including exponential smoothing for intensity transitions, micro-fluctuations (Gaussian jitter), and cardiac drift in later workout stages.
- **Duration & Timestamp Compression/Expansion:** Scales time gaps between records while updating elapsed/timer time headers to adjust workout duration dynamically.
- **Synthetic FIT File & Daily Batch Generator (`fit-creator`):** Generates realistic synthetic `.fit` activities for multiple sports modes (Running, Cycling, Swimming, Walking, Hiking, HIIT/Training) individually or as daily calorie batches (e.g. 3,000 kcal split across 5 sessions/day with non-overlapping schedules).
- **Strava API Integration:** 
  - Direct activity upload with custom names and descriptions.
  - Fetch recent activities, rename, or delete activities directly from the app.
- **Batch Processing:** Seamlessly processes single files or entire directories of FIT/CSV files.

---

## 📋 Prerequisites & System Requirements

- **Python 3.8+**
- **Java Runtime Environment (JRE 8+)**: Required to execute `FitCSVTool.jar`.

### Installation

This project utilizes modern Python packaging (`pyproject.toml`). It is recommended to install it in editable mode for development.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Dewangga027/FIT-Activity-Modifier.git
   cd FIT-Activity-Modifier
   ```

2. **Install the package locally:**
   ```bash
   pip install -e .
   ```
   *This automatically installs dependencies (`requests`, `matplotlib`) and creates global commands (`fit-modifier`, `fit-creator`).*

3. **Linux / Termux System Dependencies (for GUI):**
   ```bash
   # Ubuntu / Debian
   sudo apt update && sudo apt install python3-tk default-jre

   # Termux (Android)
   pkg install python-tkinter openjdk-17
   ```

---

## 🚀 Usage Guide

After running `pip install -e .`, the CLI commands become globally available on your system.

### 1. Graphical User Interface (GUI)

Launch the interactive Activity Modifier GUI:
```bash
fit-modifier
```
*(Alternatively: `python -m fit_modifier` or `python -m fit_modifier.modifier`)*

Launch the Synthetic FIT Activity & Daily Batch Generator GUI:
```bash
fit-creator
```
*(Alternatively: `python -m fit_modifier.creator`)*

---

### 2. Command Line Interface (CLI)

Perform programmatic modifications or batch workout generation:

#### Modify Activity (`fit-modifier`)
```bash
fit-modifier <input_path> -o <output_directory> [options]
```

##### CLI Options (`fit-modifier`)

| Flag | Long Flag | Description | Example |
| :--- | :--- | :--- | :--- |
| `-hr` | `--hr` | Target Average Heart Rate (bpm) | `-hr 150` |
| `-c` | `--cal`, `--calories` | Target Total Calories (kcal) | `-c 450` |
| `-d` | `--date` | Target Start Date (`YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`) | `-d 2026-07-27` |
| `-t` | `--time` | Target Start Time (`HH:MM:SS`) | `-t 08:30:00` |
| | `--dur`, `--duration` | Target Workout Duration (`HH:MM:SS`, `45m`, `2700s`) | `--dur 45m` |
| | `--now` | Set start timestamp to current local time | `--now` |
| | `--shift-days` | Shift start date by N days (+/-) | `--shift-days 1` |
| | `--shift-hours` | Shift start time by N hours (+/-) | `--shift-hours -2` |
| | `--upload` | Automatically upload output `.fit` file to Strava | `--upload` |
| | `--list-strava` | Display the 5 most recent Strava activities | `--list-strava` |

#### Create / Batch Generate Workouts (`fit-creator`)
```bash
fit-creator [options]
```

##### CLI Options (`fit-creator`)

| Flag | Long Flag | Description | Example |
| :--- | :--- | :--- | :--- |
| | `--batch` | Enable daily batch workout generator mode | `--batch` |
| `-o` | `--output` | Output directory for created `.fit` files | `-o fit_created/` |
| | `--sport` | Sport Mode (`Running`, `Cycling`, `HIIT / Training`, etc.) | `--sport "HIIT / Training"` |
| | `--date` | Target Date (`YYYY-MM-DD`) | `--date 2026-07-31` |
| | `--daily-calories` | Target daily calorie total (kcal) for batch mode | `--daily-calories 3000` |
| | `--calorie-tolerance` | Additional max tolerance calories (+kcal) | `--calorie-tolerance 500` |
| | `--sessions` | Number of workout sessions per day for batch mode | `--sessions 5` |
| | `--time` | Start time for single creator mode (`HH:MM:SS`) | `--time 07:30:00` |
| | `--duration` | Duration for single creator mode (`45m`, `00:45:00`) | `--duration 45m` |
| | `--hr` | Target avg HR for single creator mode (bpm) | `--hr 150` |
| | `--calories` | Target calories for single creator mode (kcal) | `--calories 450` |
| | `--gui` | Launch interactive graphical user interface | `--gui` |

#### CLI Usage Examples

```bash
# Modify average HR to 150 bpm and set duration to 45 minutes
fit-modifier examples/Activity.fit -o output/ -hr 150 --dur 45m

# Generate a daily batch of 5 HIIT sessions totaling 3,000 (+500) kcal
fit-creator --batch --daily-calories 3000 --calorie-tolerance 500 --sessions 5 --date 2026-07-31

# Shift start timestamps of all activities in a directory forward by 1 day
fit-modifier fit/ -o output/ --shift-days 1

# Modify activity metrics and automatically upload to Strava
fit-modifier examples/Activity.fit -o output/ -hr 150 --upload --name "Morning Run"
```

---

## 🟧 Strava Integration Setup

To enable direct Strava uploads and activity management:

1. Create a Strava API Application via the [Strava Developer Portal](https://www.strava.com/settings/api).
2. Copy the template from `examples/strava_config.example.json` to a new file in your working directory named `strava_config.json`:
   ```bash
   cp examples/strava_config.example.json strava_config.json
   ```
3. Populate `client_id`, `client_secret`, and `refresh_token` inside `strava_config.json`.
4. Run authorization using `python -m fit_modifier.strava_auth` or use the `--upload` CLI flag / GUI buttons directly.

---

## 📁 Repository Structure

```text
FIT-Activity-Modifier/
├── .github/                       # GitHub workflow & issue templates
├── .gitignore
├── LICENSE.txt
├── README.md
├── CONTRIBUTING.md
├── pyproject.toml                 # Standard modern Python packaging file
├── docs/                          # Architecture guides & documentation
│   └── huawei_strava_plan.md
├── src/                           # Python core package
│   └── fit_modifier/
│       ├── __init__.py
│       ├── __main__.py            # Default entrypoint
│       ├── modifier.py
│       ├── creator.py
│       ├── strava_api.py
│       └── strava_auth.py
├── tests/                         # Unit tests
│   ├── __init__.py
│   ├── test_creator.py
│   └── test_modifier.py
├── tools/                         # Garmin SDK & Java utility binaries
│   ├── FitCSVTool/
│   │   └── FitCSVTool.jar
│   └── ActivityRepairTool/
│       └── ActivityRepairTool.jar
└── examples/                      # Sample files & Configs
    ├── Activity.fit
    ├── Activity.csv
    └── strava_config.example.json # Strava configuration template
```

---

## 🤝 Contributing

Contributions are welcome! Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for details on our development workflow, branching strategies, and commit conventions.

---

## 📄 License

This project is licensed under the terms described in [LICENSE.txt](LICENSE.txt). Garmin FIT SDK tools included in `tools/` belong to Garmin International, Inc.
