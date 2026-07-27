# FIT Activity Modifier

A lightweight utility script to modify workout parameters (Heart Rate, Calories, Timestamp, and Duration) in `.fit` and `.csv` activity files before uploading to platforms like Strava. Built on top of Garmin's **FitCSVTool**.

## Workflow

```
[ FIT File ] ──► [ Decode to CSV ] ──► [ Modify Data (Python) ] ──► [ Encode to FIT ] ──► [ Output FIT File ]
```

1. **Decode:** Converts `.fit` binary files to `.csv` via `FitCSVTool.jar`.
2. **Modify:** Adjusts target metrics (HR, duration, calories, start time) across records and summary messages.
3. **Encode:** Re-encodes modified `.csv` back into a valid `.fit` binary ready for Strava upload.

## Features

- **GUI & CLI Modes:** Launch an interactive GUI (`tkinter`) or run CLI commands for automated scripts.
- **Heart Rate Scaling:** Scales average heart rate (bpm) proportionally across all recorded data points.
- **Duration & Calorie Adjustment:** Modifies total calories burned and total elapsed/active workout duration.
- **Flexible Timestamping:** Set explicit start dates/times or shift existing timestamps relatively by hours/days.
- **Batch Processing:** Supports processing individual files or entire folders.

## Prerequisites & Requirements

- **Python 3.x** (Uses Python Standard Libraries: `csv`, `tkinter`, `argparse`, `datetime`)
- **Java (JRE/JDK 8+)**: Required to execute `FitCSVTool.jar`.

### System Dependencies
No external `pip` packages are required. If using GUI on Linux or Termux:
```bash
# Ubuntu / Debian
sudo apt install python3-tk default-jre

# Termux (Android)
pkg install python-tkinter openjdk-17
```


## Usage

### 1. GUI Mode
Run without arguments to launch the graphical interface:
```bash
python modifier.py
```

### 2. CLI Mode
Ideal for automation and background tasks:
```bash
python modifier.py <input_path> -o <output_directory> [options]
```

#### CLI Options
| Flag | Description | Example |
| :--- | :--- | :--- |
| `-hr, --hr` | Target Average Heart Rate (bpm) | `-hr 150` |
| `-c, --cal` | Target Total Calories (kcal) | `-c 450` |
| `-d, --date` | Target Start Date (`YYYY-MM-DD`) | `-d 2026-07-27` |
| `-t, --time` | Target Start Time (`HH:MM:SS`) | `-t 08:30:00` |
| `--dur` | Target Workout Duration | `--dur 45m` or `--dur 00:45:00` |
| `--now` | Set timestamp to current local time | `--now` |
| `--shift-days` | Shift start date by N days | `--shift-days 1` |
| `--shift-hours` | Shift start time by N hours | `--shift-hours -2` |

#### Examples
```bash
# Modify average HR to 150 bpm & duration to 45 mins
python modifier.py fit/activity.fit -o output/ -hr 150 --dur 45m

# Shift all activities in a directory forward by 1 day
python modifier.py fit/ -o output/ --shift-days 1
```

## Directory Structure
- `modifier.py` : Main application script (GUI + CLI).
- `FitCSVTool/` : Garmin FIT SDK CSV tool components.
- `fit/` : Ignored working folder for input/output `.fit` files.
- `plan/` : Ignored folder for project planning docs.
