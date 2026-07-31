import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import os
import sys
import datetime
import subprocess

GARMIN_EPOCH = datetime.datetime(1989, 12, 31)

SPORT_MODES = {
    "Running": {"sport": 1, "sub_sport": 0, "has_distance": True, "speed_ms": 2.7}, # ~6:10 min/km
    "Cycling": {"sport": 2, "sub_sport": 0, "has_distance": True, "speed_ms": 6.5}, # ~23.4 km/h
    "Swimming": {"sport": 5, "sub_sport": 0, "has_distance": True, "speed_ms": 1.0},
    "Walking": {"sport": 11, "sub_sport": 0, "has_distance": True, "speed_ms": 1.3}, # ~4.6 km/h
    "Hiking": {"sport": 17, "sub_sport": 0, "has_distance": True, "speed_ms": 1.1},
    "HIIT / Training": {"sport": 0, "sub_sport": 0, "has_distance": False, "speed_ms": 0.0},
}

TEMPLATE_CSV = """Type,Local Number,Message,Field 1,Value 1,Units 1,Field 2,Value 2,Units 2,Field 3,Value 3,Units 3,Field 4,Value 4,Units 4,Field 5,Value 5,Units 5,Field 6,Value 6,Units 6,Field 7,Value 7,Units 7,Field 8,Value 8,Units 8,Field 9,Value 9,Units 9,Field 10,Value 10,Units 10,Field 11,Value 11,Units 11,Field 12,Value 12,Units 12,Field 13,Value 13,Units 13,Field 14,Value 14,Units 14
Definition,0,file_id,serial_number,1,,time_created,1,,manufacturer,1,,product,1,,number,1,,type,1,,,,,,,,,,,,,,,,,,,,,,,,,,,,
Data,0,file_id,serial_number,12345,,time_created,{START_TIME},,manufacturer,1,,product,1,,number,0,,type,4,,,,,,,,,,,,,,,,,,,,,,,,,,,,
Definition,1,activity,timestamp,1,,local_timestamp,1,,num_sessions,1,,type,1,,event,1,,event_type,1,,,,,,,,,,,,,,,,,,,,,,,,,,
Data,1,activity,timestamp,{END_TIME},,local_timestamp,{END_TIME},,num_sessions,1,,type,0,,event,26,,event_type,1,,,,,,,,,,,,,,,,,,,,,,,,,,
Definition,2,session,timestamp,1,,start_time,1,,total_elapsed_time,1,,total_timer_time,1,,total_calories,1,,avg_heart_rate,1,,first_lap_index,1,,num_laps,1,,event,1,,event_type,1,,sport,1,,sub_sport,1,,,,,,,,
Data,2,session,timestamp,{END_TIME},,start_time,{START_TIME},,total_elapsed_time,{DURATION},,total_timer_time,{DURATION},,total_calories,{CALORIES},,avg_heart_rate,{AVG_HR},,first_lap_index,0,,num_laps,1,,event,9,,event_type,1,,sport,{SPORT},,sub_sport,{SUB_SPORT},,,,,,,,
Definition,3,lap,timestamp,1,,start_time,1,,total_elapsed_time,1,,total_timer_time,1,,total_calories,1,,avg_heart_rate,1,,event,1,,event_type,1,,,,,,,,,,,,
Data,3,lap,timestamp,{END_TIME},,start_time,{START_TIME},,total_elapsed_time,{DURATION},,total_timer_time,{DURATION},,total_calories,{CALORIES},,avg_heart_rate,{AVG_HR},,event,9,,event_type,1,,,,,,,,,,,,
Definition,4,record,timestamp,1,,heart_rate,1,,distance,1,,speed,1,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
"""

def find_fit_csv_tool():
    """Mencari lokasi FitCSVTool.jar"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cwd = os.getcwd()
    candidates = [
        os.path.join(base_dir, "tools", "FitCSVTool", "FitCSVTool.jar"),
        os.path.join(base_dir, "FitCSVTool", "FitCSVTool.jar"),
        os.path.join(base_dir, "FitCSVTool.jar"),
        os.path.join(cwd, "tools", "FitCSVTool", "FitCSVTool.jar"),
        os.path.join(cwd, "FitCSVTool", "FitCSVTool.jar"),
        os.path.join(cwd, "FitCSVTool.jar"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def format_seconds_to_hhmmss(seconds):
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_duration_to_seconds(val):
    if not val:
        return 0
    val_str = str(val).strip().lower()
    if ":" in val_str:
        parts = val_str.split(":")
        if len(parts) == 3:
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            return int(h * 3600 + m * 60 + s)
        elif len(parts) == 2:
            m, s = float(parts[0]), float(parts[1])
            return int(m * 60 + s)
    else:
        if val_str.endswith("m"):
            return int(float(val_str[:-1]) * 60)
        else:
            return int(float(val_str)) * 60

def generate_csv_content(start_dt, duration_sec, target_avg_hr, calories, sport_mode):
    start_garmin_ts = int((start_dt - GARMIN_EPOCH).total_seconds())
    end_garmin_ts = start_garmin_ts + duration_sec
    
    mode_info = SPORT_MODES.get(sport_mode, SPORT_MODES["HIIT / Training"])
    sport = mode_info["sport"]
    sub_sport = mode_info["sub_sport"]
    
    csv_str = TEMPLATE_CSV.format(
        START_TIME=start_garmin_ts,
        END_TIME=end_garmin_ts,
        DURATION=float(duration_sec),
        CALORIES=calories,
        AVG_HR=target_avg_hr,
        SPORT=sport,
        SUB_SPORT=sub_sport
    )
    
    lines = csv_str.strip().split("\n")
    
    current_distance = 0.0
    speed_ms = mode_info["speed_ms"]
    
    current_hr = target_avg_hr

    if sport_mode == "HIIT / Training":
        # HIIT Interval simulation: alternate between Work and Rest with exponential smoothing
        work_duration = random.randint(45, 90) # 45-90s work phase
        rest_duration = random.randint(60, 120) # 60-120s rest phase
        is_work = True
        phase_timer = 0
        
        base_work_hr = min(195, target_avg_hr + 25)
        base_rest_hr = max(65, target_avg_hr - 25)
        
        target_phase_hr = base_work_hr
        
        for i in range(duration_sec):
            ts = start_garmin_ts + i
            phase_timer += 1
            
            if is_work and phase_timer > work_duration:
                is_work = False
                phase_timer = 0
                work_duration = random.randint(45, 90)
                target_phase_hr = max(60, base_rest_hr + random.randint(-5, 10))
            elif not is_work and phase_timer > rest_duration:
                is_work = True
                phase_timer = 0
                rest_duration = random.randint(60, 120)
                target_phase_hr = min(200, base_work_hr + random.randint(-10, 15))
            
            # Smooth transition (Exponential smoothing)
            diff = target_phase_hr - current_hr
            smoothing_factor = 0.05 if is_work else 0.02 # HR rises faster than it recovers
            
            # Micro-fluctuations (Gaussian jitter)
            jitter = random.gauss(0, 1.5)
            
            current_hr = current_hr + (diff * smoothing_factor) + jitter
            
            # Cardiac drift in the second half
            drift = 0
            if i > duration_sec / 2:
                drift = (i / duration_sec) * 0.01 
            
            current_hr += drift
            hr_val = max(50, min(220, int(round(current_hr))))
            
            record = f"Data,4,record,timestamp,{ts},s,heart_rate,{hr_val},bpm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"
            lines.append(record)
            
    else:
        # Normal steady-state mode with smoothing, jitter, and drift
        target_phase_hr = target_avg_hr
        for i in range(duration_sec):
            ts = start_garmin_ts + i
            
            # Periodically shift the target slightly to create natural waves
            if i % 180 == 0:
                target_phase_hr = target_avg_hr + random.randint(-10, 10)
                
            diff = target_phase_hr - current_hr
            smoothing_factor = 0.02
            jitter = random.gauss(0, 1.0)
            
            current_hr = current_hr + (diff * smoothing_factor) + jitter
            
            # Cardiac drift
            drift = 0
            if i > duration_sec / 2:
                drift = (i / duration_sec) * 0.005
                
            current_hr += drift
            hr_val = max(40, min(220, int(round(current_hr))))
            
            if mode_info["has_distance"]:
                current_distance += speed_ms
                actual_speed = speed_ms * random.uniform(0.95, 1.05)
                record = f"Data,4,record,timestamp,{ts},s,heart_rate,{hr_val},bpm,distance,{current_distance:.2f},m,speed,{actual_speed:.3f},m/s,,,,,,,,,,,,,,,,,,,,,,,,,,,"
            else:
                record = f"Data,4,record,timestamp,{ts},s,heart_rate,{hr_val},bpm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"
            lines.append(record)
            
    return "\n".join(lines)

def process_creation(output_dir, sport_mode, start_date_str, start_time_str, duration_str, target_hr_str, calories_str, headless=False):
    try:
        dur_sec = parse_duration_to_seconds(duration_str)
        if dur_sec <= 0:
            raise ValueError("Durasi harus lebih dari 0")
            
        target_avg_hr = int(target_hr_str)
        calories = int(calories_str)
        
        start_dt = datetime.datetime.strptime(f"{start_date_str} {start_time_str}", "%Y-%m-%d %H:%M:%S")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp_str = start_dt.strftime("%Y%m%d_%H%M%S")
        safe_mode = sport_mode.replace(" / ", "_").replace(" ", "_").lower()
        base_filename = f"{timestamp_str}_{safe_mode}"
        
        temp_csv = os.path.join(output_dir, f"{base_filename}_temp.csv")
        output_fit = os.path.join(output_dir, f"{base_filename}.fit")
        
        csv_content = generate_csv_content(start_dt, dur_sec, target_avg_hr, calories, sport_mode)
        
        with open(temp_csv, "w", newline="") as f:
            f.write(csv_content)
            
        jar_path = find_fit_csv_tool()
        if not jar_path:
            raise FileNotFoundError("FitCSVTool.jar tidak ditemukan!")
            
        print(f"Mengonversi CSV ke FIT: {output_fit}")
        cmd = ["java", "-jar", jar_path, "-c", temp_csv, output_fit]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode != 0:
            raise RuntimeError(f"Gagal mengonversi ke FIT:\n{res.stderr or res.stdout}")
            
        # Clean temp
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
            
        if not headless:
            messagebox.showinfo("Sukses", f"Berhasil membuat file FIT:\n{output_fit}")
        return output_fit
        
    except Exception as e:
        if not headless:
            messagebox.showerror("Error", str(e))
        else:
            print(f"Error: {e}")
            raise

def batch_create_daily_workouts(
    output_dir,
    sport_mode="HIIT / Training",
    target_date_str=None,
    target_daily_calories=3000,
    calorie_tolerance=500,
    num_sessions=5,
    headless=False
):
    """
    Generate multiple synthetic workout FIT files for a single day based on daily calorie target.
    """
    if not target_date_str:
        target_date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    num_sessions = int(num_sessions)
    if num_sessions <= 0:
        raise ValueError("Jumlah sesi harus minimal 1")

    target_daily_calories = int(target_daily_calories)
    calorie_tolerance = int(calorie_tolerance)

    # Compute total target calories including tolerance bonus
    bonus_cal = random.randint(0, max(0, calorie_tolerance))
    total_target_calories = target_daily_calories + bonus_cal

    # Partition calories across sessions using Dirichlet-like random weights
    weights = [random.uniform(0.8, 1.2) for _ in range(num_sessions)]
    sum_w = sum(weights)
    session_calories = [int(round((w / sum_w) * total_target_calories)) for w in weights]
    
    # Adjust rounding discrepancy on the last session
    diff = total_target_calories - sum(session_calories)
    session_calories[-1] += diff

    # Distribute start times between 06:00 and 21:00 (15 hours = 900 minutes)
    day_start_minute = 6 * 60  # 06:00
    day_end_minute = 21 * 60   # 21:00
    available_range = day_end_minute - day_start_minute
    window_size = available_range // num_sessions

    generated_files = []
    
    for i in range(num_sessions):
        cal = session_calories[i]
        
        # Calculate start time within session window
        win_start = day_start_minute + i * window_size
        win_end = max(win_start + 10, win_start + window_size - 40)
        start_min = random.randint(win_start, win_end)
        
        h = start_min // 60
        m = start_min % 60
        s = random.randint(0, 59)
        time_str = f"{h:02d}:{m:02d}:{s:02d}"

        # Estimate duration based on calorie burn rate (~11-15 kcal/min for HIIT)
        burn_rate = random.uniform(11.0, 15.0)
        dur_minutes = max(15, min(90, int(round(cal / burn_rate))))
        dur_str = f"{dur_minutes}m"

        # Target Avg HR (135 - 165 bpm)
        target_hr = random.randint(135, 165)

        # Generate FIT file
        fit_path = process_creation(
            output_dir=output_dir,
            sport_mode=sport_mode,
            start_date_str=target_date_str,
            start_time_str=time_str,
            duration_str=dur_str,
            target_hr_str=str(target_hr),
            calories_str=str(cal),
            headless=True
        )
        generated_files.append(fit_path)

    if not headless:
        messagebox.showinfo(
            "Batch Complete",
            f"Berhasil membuat {len(generated_files)} file FIT (Total: {sum(session_calories)} kcal) di:\n{output_dir}"
        )

    return generated_files

class CreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FIT File Creator & Daily Batch Generator")
        self.root.geometry("640x600")
        
        FONT_FAMILY = "Segoe UI"
        FONT_MAIN = (FONT_FAMILY, 10)
        FONT_BOLD = (FONT_FAMILY, 10, "bold")
        
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Single Creator Mode
        tab_single = ttk.Frame(notebook)
        notebook.add(tab_single, text=" Single FIT Creator ")
        self._build_single_tab(tab_single, FONT_MAIN, FONT_BOLD, FONT_FAMILY)
        
        # Tab 2: Daily Batch Mode
        tab_batch = ttk.Frame(notebook)
        notebook.add(tab_batch, text=" Daily Batch Calorie Generator ")
        self._build_batch_tab(tab_batch, FONT_MAIN, FONT_BOLD, FONT_FAMILY)

    def _build_single_tab(self, parent, FONT_MAIN, FONT_BOLD, FONT_FAMILY):
        # Output Folder
        tk.Label(parent, text="Output Folder:", font=FONT_BOLD).grid(row=0, column=0, sticky="w", padx=12, pady=10)
        self.output_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "fit_created"))
        tk.Entry(parent, textvariable=self.output_dir_var, width=38, font=FONT_MAIN).grid(row=0, column=1, padx=5, pady=10, sticky="w")
        tk.Button(parent, text="Browse...", command=lambda: self.browse_output_dir(self.output_dir_var)).grid(row=0, column=2, padx=5, pady=10)
        
        # Sport Mode
        tk.Label(parent, text="Sport Mode:", font=FONT_BOLD).grid(row=1, column=0, sticky="w", padx=12, pady=10)
        self.sport_var = tk.StringVar(value="Running")
        sport_options = list(SPORT_MODES.keys())
        tk.OptionMenu(parent, self.sport_var, *sport_options).grid(row=1, column=1, sticky="w", padx=5, pady=10)
        
        # Start Date
        tk.Label(parent, text="Tanggal (YYYY-MM-DD):", font=FONT_BOLD).grid(row=2, column=0, sticky="w", padx=12, pady=10)
        now = datetime.datetime.now()
        self.date_var = tk.StringVar(value=now.strftime("%Y-%m-%d"))
        tk.Entry(parent, textvariable=self.date_var, width=15, font=FONT_MAIN).grid(row=2, column=1, sticky="w", padx=5, pady=10)
        
        # Start Time
        tk.Label(parent, text="Waktu Mulai (HH:MM:SS):", font=FONT_BOLD).grid(row=3, column=0, sticky="w", padx=12, pady=10)
        self.time_var = tk.StringVar(value=now.strftime("%H:%M:%S"))
        tk.Entry(parent, textvariable=self.time_var, width=15, font=FONT_MAIN).grid(row=3, column=1, sticky="w", padx=5, pady=10)
        
        # Duration
        tk.Label(parent, text="Durasi (Menit / HH:MM:SS):", font=FONT_BOLD).grid(row=4, column=0, sticky="w", padx=12, pady=10)
        self.duration_var = tk.StringVar(value="45")
        tk.Entry(parent, textvariable=self.duration_var, width=15, font=FONT_MAIN).grid(row=4, column=1, sticky="w", padx=5, pady=10)
        
        # Target Avg HR
        tk.Label(parent, text="Target Avg HR (bpm):", font=FONT_BOLD).grid(row=5, column=0, sticky="w", padx=12, pady=10)
        self.hr_var = tk.StringVar(value="145")
        tk.Entry(parent, textvariable=self.hr_var, width=15, font=FONT_MAIN).grid(row=5, column=1, sticky="w", padx=5, pady=10)
        
        # Target Calories
        tk.Label(parent, text="Target Calories (kcal):", font=FONT_BOLD).grid(row=6, column=0, sticky="w", padx=12, pady=10)
        self.cal_var = tk.StringVar(value="450")
        tk.Entry(parent, textvariable=self.cal_var, width=15, font=FONT_MAIN).grid(row=6, column=1, sticky="w", padx=5, pady=10)
        
        # Process Button
        tk.Button(parent, text="Generate FIT File", command=self.on_process_single, bg="#0275d8", fg="white", font=(FONT_FAMILY, 11, "bold"), padx=20, pady=5).grid(row=7, column=1, pady=20, sticky="w")

    def _build_batch_tab(self, parent, FONT_MAIN, FONT_BOLD, FONT_FAMILY):
        # Output Folder
        tk.Label(parent, text="Output Folder:", font=FONT_BOLD).grid(row=0, column=0, sticky="w", padx=12, pady=10)
        self.batch_output_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "fit_created", "daily_batch"))
        tk.Entry(parent, textvariable=self.batch_output_dir_var, width=38, font=FONT_MAIN).grid(row=0, column=1, padx=5, pady=10, sticky="w")
        tk.Button(parent, text="Browse...", command=lambda: self.browse_output_dir(self.batch_output_dir_var)).grid(row=0, column=2, padx=5, pady=10)
        
        # Sport Mode
        tk.Label(parent, text="Sport Mode:", font=FONT_BOLD).grid(row=1, column=0, sticky="w", padx=12, pady=10)
        self.batch_sport_var = tk.StringVar(value="HIIT / Training")
        sport_options = list(SPORT_MODES.keys())
        tk.OptionMenu(parent, self.batch_sport_var, *sport_options).grid(row=1, column=1, sticky="w", padx=5, pady=10)
        
        # Tanggal Target
        tk.Label(parent, text="Tanggal (YYYY-MM-DD):", font=FONT_BOLD).grid(row=2, column=0, sticky="w", padx=12, pady=10)
        now = datetime.datetime.now()
        self.batch_date_var = tk.StringVar(value=now.strftime("%Y-%m-%d"))
        tk.Entry(parent, textvariable=self.batch_date_var, width=15, font=FONT_MAIN).grid(row=2, column=1, sticky="w", padx=5, pady=10)
        
        # Target Daily Calories
        tk.Label(parent, text="Target Kalori Harian (kcal):", font=FONT_BOLD).grid(row=3, column=0, sticky="w", padx=12, pady=10)
        self.batch_daily_cal_var = tk.StringVar(value="3000")
        tk.Entry(parent, textvariable=self.batch_daily_cal_var, width=15, font=FONT_MAIN).grid(row=3, column=1, sticky="w", padx=5, pady=10)
        
        # Calorie Tolerance
        tk.Label(parent, text="Toleransi Kalori (+kcal):", font=FONT_BOLD).grid(row=4, column=0, sticky="w", padx=12, pady=10)
        self.batch_tolerance_var = tk.StringVar(value="500")
        tk.Entry(parent, textvariable=self.batch_tolerance_var, width=15, font=FONT_MAIN).grid(row=4, column=1, sticky="w", padx=5, pady=10)
        
        # Jumlah Sesi per Hari
        tk.Label(parent, text="Jumlah Sesi per Hari:", font=FONT_BOLD).grid(row=5, column=0, sticky="w", padx=12, pady=10)
        self.batch_sessions_var = tk.StringVar(value="5")
        tk.Entry(parent, textvariable=self.batch_sessions_var, width=15, font=FONT_MAIN).grid(row=5, column=1, sticky="w", padx=5, pady=10)
        
        # Process Button
        tk.Button(parent, text="Generate Daily Batch FIT Files", command=self.on_process_batch, bg="#2e7d32", fg="white", font=(FONT_FAMILY, 11, "bold"), padx=20, pady=5).grid(row=6, column=1, pady=20, sticky="w")

    def browse_output_dir(self, target_var):
        d = filedialog.askdirectory()
        if d:
            target_var.set(d)
            
    def on_process_single(self):
        process_creation(
            self.output_dir_var.get(),
            self.sport_var.get(),
            self.date_var.get(),
            self.time_var.get(),
            self.duration_var.get(),
            self.hr_var.get(),
            self.cal_var.get()
        )

    def on_process_batch(self):
        try:
            batch_create_daily_workouts(
                output_dir=self.batch_output_dir_var.get(),
                sport_mode=self.batch_sport_var.get(),
                target_date_str=self.batch_date_var.get(),
                target_daily_calories=int(self.batch_daily_cal_var.get()),
                calorie_tolerance=int(self.batch_tolerance_var.get()),
                num_sessions=int(self.batch_sessions_var.get()),
                headless=False
            )
        except Exception as e:
            messagebox.showerror("Error Batch Generator", str(e))

def main():
    import argparse
    parser = argparse.ArgumentParser(description="FIT File Creator & Batch Daily Workout Generator")
    parser.add_argument("--batch", action="store_true", help="Enable daily batch workout generator mode")
    parser.add_argument("--output", "-o", default=None, help="Output directory")
    parser.add_argument("--sport", default="HIIT / Training", help="Sport mode (Running, Cycling, HIIT / Training, etc.)")
    parser.add_argument("--date", default=None, help="Target date (YYYY-MM-DD)")
    parser.add_argument("--daily-calories", type=int, default=3000, help="Target daily calories (default: 3000)")
    parser.add_argument("--calorie-tolerance", type=int, default=500, help="Max calorie tolerance (default: 500)")
    parser.add_argument("--sessions", type=int, default=5, help="Number of workout sessions per day (default: 5)")
    parser.add_argument("--time", default="08:00:00", help="Start time for single mode (HH:MM:SS)")
    parser.add_argument("--duration", default="45", help="Duration for single mode (mins/HH:MM:SS)")
    parser.add_argument("--hr", default="145", help="Target avg HR for single mode")
    parser.add_argument("--calories", default="450", help="Target calories for single mode")
    parser.add_argument("--gui", action="store_true", help="Launch GUI mode")

    args, unknown = parser.parse_known_args()

    # Launch CLI mode if explicit CLI flags passed without --gui
    if len(sys.argv) > 1 and not args.gui:
        out_dir = args.output or os.path.join(os.getcwd(), "fit_created")
        if args.batch:
            print(f"Memulai Batch Daily Generator: Target {args.daily_calories} (+{args.calorie_tolerance}) kcal | {args.sessions} Sesi")
            batch_create_daily_workouts(
                output_dir=out_dir,
                sport_mode=args.sport,
                target_date_str=args.date,
                target_daily_calories=args.daily_calories,
                calorie_tolerance=args.calorie_tolerance,
                num_sessions=args.sessions,
                headless=True
            )
        else:
            date_str = args.date or datetime.datetime.now().strftime("%Y-%m-%d")
            process_creation(
                output_dir=out_dir,
                sport_mode=args.sport,
                start_date_str=date_str,
                start_time_str=args.time,
                duration_str=args.duration,
                target_hr_str=args.hr,
                calories_str=args.calories,
                headless=True
            )
    else:
        root = tk.Tk()
        app = CreatorApp(root)
        root.mainloop()

if __name__ == "__main__":
    main()
