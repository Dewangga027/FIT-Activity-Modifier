import csv
import tkinter as tk
from tkinter import messagebox, filedialog
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
    
    # Generate records
    current_distance = 0.0
    speed_ms = mode_info["speed_ms"]
    
    hr_pool = list(range(max(40, target_avg_hr - 5), min(220, target_avg_hr + 5)))
    
    for i in range(duration_sec):
        ts = start_garmin_ts + i
        hr = random.choice(hr_pool)
        
        # Simulate slight variation over time
        if i % 60 == 0:
            hr_pool = list(range(max(40, hr - 3), min(220, hr + 3)))
            # Keep it somewhat close to target
            if sum(hr_pool)/len(hr_pool) < target_avg_hr - 10:
                hr_pool = [x + 2 for x in hr_pool]
            elif sum(hr_pool)/len(hr_pool) > target_avg_hr + 10:
                hr_pool = [x - 2 for x in hr_pool]
                
        if mode_info["has_distance"]:
            current_distance += speed_ms
            # adding slight variation to speed
            actual_speed = speed_ms * random.uniform(0.95, 1.05)
            record = f"Data,4,record,timestamp,{ts},s,heart_rate,{hr},bpm,distance,{current_distance:.2f},m,speed,{actual_speed:.3f},m/s,,,,,,,,,,,,,,,,,,,,,,,,,,,"
        else:
            record = f"Data,4,record,timestamp,{ts},s,heart_rate,{hr},bpm,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"
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
        safe_mode = sport_mode.replace(" / ", "_").lower()
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

class CreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FIT File Creator (Generative Mode)")
        self.root.geometry("600x550")
        
        FONT_FAMILY = "Segoe UI"
        FONT_MAIN = (FONT_FAMILY, 10)
        FONT_BOLD = (FONT_FAMILY, 10, "bold")
        
        # Output Folder
        tk.Label(root, text="Output Folder:", font=FONT_BOLD).grid(row=0, column=0, sticky="w", padx=12, pady=10)
        self.output_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "fit_created"))
        tk.Entry(root, textvariable=self.output_dir_var, width=40, font=FONT_MAIN).grid(row=0, column=1, padx=5, pady=10, sticky="w")
        tk.Button(root, text="Browse...", command=self.browse_output_dir).grid(row=0, column=2, padx=5, pady=10)
        
        # Sport Mode
        tk.Label(root, text="Sport Mode:", font=FONT_BOLD).grid(row=1, column=0, sticky="w", padx=12, pady=10)
        self.sport_var = tk.StringVar(value="Running")
        sport_options = list(SPORT_MODES.keys())
        tk.OptionMenu(root, self.sport_var, *sport_options).grid(row=1, column=1, sticky="w", padx=5, pady=10)
        
        # Start Date
        tk.Label(root, text="Tanggal (YYYY-MM-DD):", font=FONT_BOLD).grid(row=2, column=0, sticky="w", padx=12, pady=10)
        now = datetime.datetime.now()
        self.date_var = tk.StringVar(value=now.strftime("%Y-%m-%d"))
        tk.Entry(root, textvariable=self.date_var, width=15, font=FONT_MAIN).grid(row=2, column=1, sticky="w", padx=5, pady=10)
        
        # Start Time
        tk.Label(root, text="Waktu Mulai (HH:MM:SS):", font=FONT_BOLD).grid(row=3, column=0, sticky="w", padx=12, pady=10)
        self.time_var = tk.StringVar(value=now.strftime("%H:%M:%S"))
        tk.Entry(root, textvariable=self.time_var, width=15, font=FONT_MAIN).grid(row=3, column=1, sticky="w", padx=5, pady=10)
        
        # Duration
        tk.Label(root, text="Durasi (Menit / HH:MM:SS):", font=FONT_BOLD).grid(row=4, column=0, sticky="w", padx=12, pady=10)
        self.duration_var = tk.StringVar(value="45")
        tk.Entry(root, textvariable=self.duration_var, width=15, font=FONT_MAIN).grid(row=4, column=1, sticky="w", padx=5, pady=10)
        
        # Target Avg HR
        tk.Label(root, text="Target Avg HR (bpm):", font=FONT_BOLD).grid(row=5, column=0, sticky="w", padx=12, pady=10)
        self.hr_var = tk.StringVar(value="145")
        tk.Entry(root, textvariable=self.hr_var, width=15, font=FONT_MAIN).grid(row=5, column=1, sticky="w", padx=5, pady=10)
        
        # Target Calories
        tk.Label(root, text="Target Calories (kcal):", font=FONT_BOLD).grid(row=6, column=0, sticky="w", padx=12, pady=10)
        self.cal_var = tk.StringVar(value="450")
        tk.Entry(root, textvariable=self.cal_var, width=15, font=FONT_MAIN).grid(row=6, column=1, sticky="w", padx=5, pady=10)
        
        # Process Button
        tk.Button(root, text="Generate FIT File", command=self.on_process, bg="#0275d8", fg="white", font=(FONT_FAMILY, 11, "bold"), padx=20, pady=5).grid(row=7, column=1, pady=20, sticky="w")
        
    def browse_output_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir_var.set(d)
            
    def on_process(self):
        process_creation(
            self.output_dir_var.get(),
            self.sport_var.get(),
            self.date_var.get(),
            self.time_var.get(),
            self.duration_var.get(),
            self.hr_var.get(),
            self.cal_var.get()
        )

def main():
    root = tk.Tk()
    app = CreatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
