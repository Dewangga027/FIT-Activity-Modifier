import csv
import tkinter as tk
from tkinter import messagebox, filedialog
import random
import os
import sys
import datetime
import subprocess
import argparse

try:
    import strava_api
    STRAVA_AVAILABLE = True
except ImportError:
    STRAVA_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

GARMIN_EPOCH = datetime.datetime(1989, 12, 31)

def find_fit_csv_tool():
    """Mencari lokasi FitCSVTool.jar"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "FitCSVTool", "FitCSVTool.jar"),
        os.path.join(base_dir, "FitCSVTool.jar"),
        os.path.join(os.getcwd(), "FitCSVTool", "FitCSVTool.jar"),
        os.path.join(os.getcwd(), "FitCSVTool.jar"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def format_seconds_to_hhmmss(seconds):
    """Mengubah detik ke format HH:MM:SS"""
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_duration_to_seconds(val):
    """Mengubah input durasi (HH:MM:SS, MM:SS, 45m, 2700, dll) ke detik"""
    if val is None or str(val).strip() == "":
        return None
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
        if val_str.endswith("h"):
            return int(float(val_str[:-1]) * 3600)
        elif val_str.endswith("m"):
            return int(float(val_str[:-1]) * 60)
        elif val_str.endswith("s"):
            return int(float(val_str[:-1]))
        else:
            num = float(val_str)
            # Jika angka <= 180, berasumsi menit (misal: 45 = 45 menit). Jika > 180, dianggap detik (misal: 2700 detik).
            if num <= 180:
                return int(num * 60)
            else:
                return int(num)

def extract_metadata_from_file(filepath):
    """Mengekstrak start_time, total_elapsed_time, avg_heart_rate, dan total_calories dari file FIT atau CSV"""
    if not os.path.exists(filepath):
        return None, None, None, None
    
    in_base, in_ext = os.path.splitext(filepath)
    in_ext = in_ext.lower()
    
    temp_csv = None
    target_csv = filepath
    
    if in_ext == ".fit":
        jar_path = find_fit_csv_tool()
        if not jar_path:
            return None, None, None, None
        temp_csv = in_base + "_temp_meta.csv"
        cmd = ["java", "-jar", jar_path, "-b", filepath, temp_csv]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(temp_csv):
            target_csv = temp_csv
        else:
            return None, None, None, None
            
    dt_str = None
    dur_str = None
    avg_hr = None
    total_cal = None
    
    try:
        with open(target_csv, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) > 2 and row[0] == 'Data':
                    # Extract date
                    if dt_str is None:
                        for j in range(3, len(row)-1, 3):
                            if row[j] in ('timestamp', 'start_time'):
                                val = row[j+1]
                                if val.isdigit():
                                    garmin_ts = int(val)
                                    dt = GARMIN_EPOCH + datetime.timedelta(seconds=garmin_ts)
                                    dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                                    break
                    
                    # Extract session metadata
                    if row[2] in ('session', 'lap', 'activity'):
                        for j in range(3, len(row)-1, 3):
                            if row[j] in ('total_elapsed_time', 'total_timer_time') and dur_str is None:
                                val = row[j+1]
                                try:
                                    sec = float(val)
                                    if sec > 0:
                                        dur_str = format_seconds_to_hhmmss(sec)
                                except ValueError:
                                    pass
                            elif row[j] == 'avg_heart_rate' and avg_hr is None:
                                avg_hr = row[j+1]
                            elif row[j] == 'total_calories' and total_cal is None:
                                total_cal = row[j+1]
                                
                if dt_str and dur_str and avg_hr and total_cal:
                    break
    except Exception:
        pass
    finally:
        if temp_csv and os.path.exists(temp_csv):
            try:
                os.remove(temp_csv)
            except Exception:
                pass
                
    return dt_str, dur_str, avg_hr, total_cal

def extract_hr_timeseries(filepath):
    """
    Mengekstrak data time-series heart rate dari file FIT atau CSV.
    Return: list of dict [{
        'elapsed_sec': float,   # detik sejak aktivitas dimulai
        'timestamp_dt': datetime, # datetime object (UTC Garmin epoch)
        'heart_rate': int        # bpm
    }]
    """
    if not os.path.exists(filepath):
        return []
        
    in_base, in_ext = os.path.splitext(filepath)
    in_ext = in_ext.lower()
    
    temp_csv = None
    target_csv = filepath
    
    if in_ext == ".fit":
        jar_path = find_fit_csv_tool()
        if not jar_path:
            return []
        temp_csv = in_base + "_temp_hr_meta.csv"
        cmd = ["java", "-jar", jar_path, "-b", filepath, temp_csv]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(temp_csv):
            target_csv = temp_csv
        else:
            return []
            
    timeseries = []
    first_ts = None
    
    try:
        with open(target_csv, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) > 2 and row[0] == 'Data' and row[2] == 'record':
                    ts = None
                    hr = None
                    for j in range(3, len(row)-1, 3):
                        if row[j] == 'timestamp':
                            val = row[j+1]
                            if val.isdigit():
                                ts = int(val)
                        elif row[j] == 'heart_rate':
                            val = row[j+1]
                            if val.isdigit():
                                hr = int(val)
                                
                    if ts is not None and hr is not None:
                        if first_ts is None:
                            first_ts = ts
                            
                        elapsed_sec = float(ts - first_ts)
                        dt = GARMIN_EPOCH + datetime.timedelta(seconds=ts)
                        
                        timeseries.append({
                            'elapsed_sec': elapsed_sec,
                            'timestamp_dt': dt,
                            'heart_rate': hr
                        })
    except Exception:
        pass
    finally:
        if temp_csv and os.path.exists(temp_csv):
            try:
                os.remove(temp_csv)
            except Exception:
                pass
                
    return timeseries

def process_csv(input_file, output_file, target_avg_hr=None, target_calories=None, target_date_str=None, relative_shift_seconds=0, target_duration_seconds=None):
    time_shift = relative_shift_seconds
    target_dt = None
    
    if target_date_str and target_date_str.strip():
        s = target_date_str.strip()
        try:
            if " " in s:
                target_dt = datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            else:
                target_dt = datetime.datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Format tanggal/waktu salah. Gunakan format 'YYYY-MM-DD HH:MM:SS' atau 'YYYY-MM-DD'.")

    with open(input_file, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # 1. Cari timestamp pertama (first_ts), timestamp record terakhir, dan durasi original (orig_elapsed)
    first_ts = None
    first_local_ts = None
    last_record_ts = None
    orig_elapsed = None
    orig_avg_hr = None
    orig_total_cal = None

    for row in rows:
        if len(row) > 2 and row[0] == 'Data':
            for j in range(3, len(row)-1, 3):
                if row[j] in ('timestamp', 'start_time'):
                    val = row[j+1]
                    if val.isdigit():
                        ts_val = int(val)
                        if first_ts is None or ts_val < first_ts:
                            first_ts = ts_val
                elif row[j] == 'local_timestamp':
                    val = row[j+1]
                    if val.isdigit():
                        ts_val = int(val)
                        if first_local_ts is None or ts_val < first_local_ts:
                            first_local_ts = ts_val

            if row[2] == 'record':
                for j in range(3, len(row)-1, 3):
                    if row[j] == 'timestamp':
                        val = row[j+1]
                        if val.isdigit():
                            ts_val = int(val)
                            if last_record_ts is None or ts_val > last_record_ts:
                                last_record_ts = ts_val

            if row[2] == 'session':
                for j in range(3, len(row)-1, 3):
                    if row[j] == 'total_elapsed_time':
                        val = row[j+1]
                        try:
                            orig_elapsed = float(val)
                        except ValueError:
                            pass
                    elif row[j] == 'avg_heart_rate':
                        val = row[j+1]
                        if val.isdigit():
                            orig_avg_hr = int(val)
                    elif row[j] == 'total_calories':
                        val = row[j+1]
                        if val.isdigit():
                            orig_total_cal = int(val)

    if target_avg_hr is None:
        target_avg_hr = orig_avg_hr or 140
    if target_calories is None:
        target_calories = orig_total_cal or 500

    # Hitung pergeseran tanggal/waktu (time_shift)
    if target_dt is not None and first_ts is not None:
        original_dt = GARMIN_EPOCH + datetime.timedelta(seconds=first_ts)
        time_shift = int((target_dt - original_dt).total_seconds())

    # Hitung skala durasi (scale_factor) untuk memenskala timestamp record agar Elapsed Time di Strava / Garmin berubah
    scale_factor = 1.0
    if target_duration_seconds is not None and target_duration_seconds > 0:
        orig_dur = None
        if orig_elapsed and orig_elapsed > 0:
            orig_dur = orig_elapsed
        elif first_ts is not None and last_record_ts is not None and last_record_ts > first_ts:
            orig_dur = float(last_record_ts - first_ts)
            
        if orig_dur and orig_dur > 0:
            scale_factor = float(target_duration_seconds) / orig_dur

    # 2. Cari data heart rate di record
    record_hr_indices = []
    current_hrs = []
    
    for i, row in enumerate(rows):
        if len(row) > 2 and row[0] == 'Data' and row[2] == 'record':
            for j in range(3, len(row) - 1, 3):
                if row[j] == 'heart_rate':
                    val = row[j+1]
                    if val.isdigit():
                        current_hrs.append(int(val))
                        record_hr_indices.append((i, j+1))
                    break
                    
    if not current_hrs:
        raise ValueError("Tidak ditemukan data heart rate pada baris record.")
        
    current_avg = sum(current_hrs) / len(current_hrs)
    shift = target_avg_hr - current_avg
    
    # 3. Generate HR baru
    new_hrs = []
    for hr in current_hrs:
        new_hr = int(round(hr + shift))
        if new_hr < 40: new_hr = 40
        if new_hr > 220: new_hr = 220
        new_hrs.append(new_hr)
        
    diff = (target_avg_hr * len(new_hrs)) - sum(new_hrs)
    diff = int(round(diff))
    
    indices_to_adjust = list(range(len(new_hrs)))
    random.shuffle(indices_to_adjust)
    
    step = 1 if diff > 0 else -1
    for _ in range(abs(diff)):
        if not indices_to_adjust:
            indices_to_adjust = list(range(len(new_hrs)))
            random.shuffle(indices_to_adjust)
        idx = indices_to_adjust.pop()
        new_hrs[idx] += step

    # 4. Update data HR ke rows
    for (row_idx, col_idx), new_hr in zip(record_hr_indices, new_hrs):
        rows[row_idx][col_idx] = str(new_hr)
        
    # 5. Update data Session, Durasi, dan Timestamp Scaling
    new_rows = []
    last_record_ts_emitted = None
    
    for i, row in enumerate(rows):
        if len(row) > 2 and row[0] == 'Data':
            # Update values di row session
            if row[2] == 'session':
                for j in range(3, len(row) - 1, 3):
                    if row[j] == 'total_calories':
                        row[j+1] = str(target_calories)
                    elif row[j] == 'avg_heart_rate':
                        row[j+1] = str(target_avg_hr)
                        
            # Update total waktu latihan (durasi) jika scale_factor berubah
            if scale_factor != 1.0:
                if row[2] in ('session', 'lap', 'activity'):
                    for j in range(3, len(row) - 1, 3):
                        if row[j] in ('total_elapsed_time', 'total_timer_time'):
                            val = row[j+1]
                            try:
                                old_dur = float(val)
                                new_dur = old_dur * scale_factor
                                row[j+1] = f"{new_dur:.1f}"
                            except ValueError:
                                pass

            # Update timestamps jika ada time_shift ATAU scaling durasi
            skip_row = False
            if time_shift != 0 or scale_factor != 1.0:
                for j in range(3, len(row) - 1, 3):
                    key = row[j]
                    if key in ('timestamp', 'start_time', 'time_created'):
                        val = row[j+1]
                        if val.isdigit():
                            ts = int(val)
                            if first_ts is not None and ts >= first_ts and scale_factor != 1.0:
                                offset = ts - first_ts
                                scaled_offset = int(round(offset * scale_factor))
                                new_ts = (first_ts + time_shift) + scaled_offset
                            else:
                                new_ts = ts + time_shift
                                
                            # Hindari duplicate timestamp pada record (karena kompresi durasi)
                            if row[2] == 'record' and key == 'timestamp':
                                if last_record_ts_emitted is not None and new_ts <= last_record_ts_emitted:
                                    skip_row = True
                                else:
                                    last_record_ts_emitted = new_ts
                                    
                            row[j+1] = str(new_ts)
                            
                    elif key == 'local_timestamp':
                        val = row[j+1]
                        if val.isdigit():
                            ts = int(val)
                            if first_local_ts is not None and ts >= first_local_ts and scale_factor != 1.0:
                                offset = ts - first_local_ts
                                scaled_offset = int(round(offset * scale_factor))
                                new_ts = (first_local_ts + time_shift) + scaled_offset
                            else:
                                new_ts = ts + time_shift
                            row[j+1] = str(new_ts)
                            
            if not skip_row:
                new_rows.append(row)
        else:
            new_rows.append(row)

    # Tulis ke file output
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

def process_single_file(input_path, output_dir, target_avg_hr=None, target_calories=None, target_date_str=None, relative_shift_seconds=0, target_duration_seconds=None, keep_temp=False):
    """
    Memproses 1 file (.fit atau .csv) dan menyimpan hasil .fit ke dalam folder output_dir.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File input '{input_path}' tidak ditemukan!")

    os.makedirs(output_dir, exist_ok=True)

    in_base_name = os.path.basename(input_path)
    name_without_ext, in_ext = os.path.splitext(in_base_name)
    in_ext = in_ext.lower()

    if in_ext not in ('.fit', '.csv'):
        raise ValueError(f"File '{input_path}' harus ber-ekstensi .fit atau .csv")

    output_filename = f"{name_without_ext}_modified.fit"
    output_fit_path = os.path.join(output_dir, output_filename)

    jar_path = find_fit_csv_tool()
    if not jar_path:
        raise FileNotFoundError("FitCSVTool.jar tidak ditemukan! Pastikan folder FitCSVTool ada.")

    temp_files_to_clean = []

    # Step 1: Decode FIT ke CSV jika input berupa FIT
    if in_ext == ".fit":
        temp_input_csv = os.path.join(output_dir, f"{name_without_ext}_temp_decode.csv")
        temp_files_to_clean.append(temp_input_csv)
        print(f"[1/3] Mengonversi FIT ke CSV: {input_path} -> {temp_input_csv}")
        cmd_decode = ["java", "-jar", jar_path, "-b", input_path, temp_input_csv]
        res = subprocess.run(cmd_decode, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Gagal mengonversi FIT ke CSV:\n{res.stderr or res.stdout}")
        csv_in = temp_input_csv
    else:
        csv_in = input_path

    # Step 2: Path CSV modifikasi sementara di dalam output_dir
    temp_output_csv = os.path.join(output_dir, f"{name_without_ext}_modified.csv")
    if not keep_temp:
        temp_files_to_clean.append(temp_output_csv)

    # Step 3: Modifikasi data CSV
    dur_info = f", Durasi: {format_seconds_to_hhmmss(target_duration_seconds)}" if target_duration_seconds else ""
    print(f"[2/3] Memproses data CSV (Target HR: {target_avg_hr} bpm, Kalori: {target_calories} kcal{dur_info})...")
    process_csv(csv_in, temp_output_csv, target_avg_hr, target_calories, target_date_str, relative_shift_seconds, target_duration_seconds)

    # Step 4: Encode CSV ke FIT
    print(f"[3/3] Mengonversi CSV ke FIT: {temp_output_csv} -> {output_fit_path}")
    cmd_encode = ["java", "-jar", jar_path, "-c", temp_output_csv, output_fit_path]
    res = subprocess.run(cmd_encode, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Gagal mengonversi CSV ke FIT:\n{res.stderr or res.stdout}")

    # Bersihkan file CSV temporary
    if not keep_temp:
        for f in temp_files_to_clean:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    return output_fit_path

def process_target(input_path, output_dir=None, target_avg_hr=None, target_calories=None, target_date_str=None, relative_shift_seconds=0, target_duration_seconds=None, keep_temp=False):
    """
    Memproses file tunggal ATAU seluruh folder ber-ekstensi .fit / .csv, 
    dan menyimpan hasilnya ke dalam folder output.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input '{input_path}' tidak ditemukan!")

    # Kasus A: Input berupa folder / direktori
    if os.path.isdir(input_path):
        if not output_dir:
            output_dir = input_path.rstrip(os.sep + "/") + "_modified"
        
        files_to_process = [
            os.path.join(input_path, f) for f in os.listdir(input_path)
            if f.lower().endswith(('.fit', '.csv')) 
            and not f.lower().endswith(('_modified.csv', '_modified.fit'))
            and 'temp' not in f.lower()
        ]
        
        if not files_to_process:
            raise ValueError(f"Tidak ada file .fit atau .csv yang valid ditemukan di dalam folder '{input_path}'")
        
        results = []
        print(f"Menemukan {len(files_to_process)} file di folder '{input_path}'. Menyimpan hasil ke folder: '{output_dir}'")
        for file_item in files_to_process:
            print(f"\n--- Memproses: {os.path.basename(file_item)} ---")
            res = process_single_file(file_item, output_dir, target_avg_hr, target_calories, target_date_str, relative_shift_seconds, target_duration_seconds, keep_temp)
            results.append(res)
            
        print(f"\n[SELESAI] Total {len(results)} file berhasil diproses ke dalam folder: {output_dir}")
        return output_dir, results

    # Kasus B: Input berupa file tunggal
    else:
        if not output_dir:
            base_dir = os.path.dirname(input_path) or "."
            name_without_ext = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = os.path.join(base_dir, f"{name_without_ext}_modified")
        
        res = process_single_file(input_path, output_dir, target_avg_hr, target_calories, target_date_str, relative_shift_seconds, target_duration_seconds, keep_temp)
        print(f"\n[SELESAI] File modified berhasil disimpan di folder: {output_dir}")
        return output_dir, [res]

class App:
    def __init__(self, root):
        self.root = root
        self.last_files = []
        self.root.title("FIT / CSV Modifier Workflow (HR, Kalori, Tanggal & Durasi)")
        self.root.geometry("1150x760")
        self.root.grid_rowconfigure(11, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Global Font Styling
        FONT_FAMILY = "Segoe UI"
        FONT_MAIN = (FONT_FAMILY, 10)
        FONT_BOLD = (FONT_FAMILY, 10, "bold")
        
        self.root.option_add("*Font", FONT_MAIN)
        
        # Row 0: Input File / Folder
        tk.Label(root, text="Input File / Folder:", font=FONT_BOLD).grid(row=0, column=0, sticky="w", padx=12, pady=6)
        self.input_var = tk.StringVar(value=r"g:\Download\fit-sdk-tools-21.205.0\fit-sdk-tools-21.205.0\fit")
        tk.Entry(root, textvariable=self.input_var, width=58, font=FONT_MAIN).grid(row=0, column=1, padx=5, pady=6, sticky="w")
        
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=0, column=2, padx=12, pady=6, sticky="w")
        tk.Button(btn_frame, text="File...", command=self.browse_file, font=FONT_MAIN).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Folder...", command=self.browse_folder, font=FONT_MAIN).pack(side="left", padx=2)
        
        # Row 1: Output Folder
        tk.Label(root, text="Output Folder:", font=FONT_BOLD).grid(row=1, column=0, sticky="w", padx=12, pady=6)
        self.output_dir_var = tk.StringVar(value=r"g:\Download\fit-sdk-tools-21.205.0\fit-sdk-tools-21.205.0\fit_modified")
        tk.Entry(root, textvariable=self.output_dir_var, width=58, font=FONT_MAIN).grid(row=1, column=1, padx=5, pady=6, sticky="w")
        tk.Button(root, text="Browse Folder...", command=self.browse_output_dir, font=FONT_MAIN).grid(row=1, column=2, padx=12, pady=6, sticky="w")
        
        # Row 2: Date & Time Input (Start & End)
        tk.Label(root, text="Tanggal (YYYY-MM-DD):", font=FONT_BOLD).grid(row=2, column=0, sticky="w", padx=12, pady=6)
        dt_frame = tk.Frame(root)
        dt_frame.grid(row=2, column=1, sticky="w", padx=5, pady=6)
        
        self.date_var = tk.StringVar(value="")
        tk.Entry(dt_frame, textvariable=self.date_var, width=14, font=FONT_MAIN).pack(side="left", padx=2)
        
        tk.Label(dt_frame, text="Start (HH:MM:SS):", font=FONT_BOLD).pack(side="left", padx=(12, 2))
        self.time_var = tk.StringVar(value="")
        entry_start = tk.Entry(dt_frame, textvariable=self.time_var, width=12, font=FONT_MAIN)
        entry_start.pack(side="left", padx=2)

        tk.Label(dt_frame, text="End (HH:MM:SS):", font=FONT_BOLD).pack(side="left", padx=(12, 2))
        self.time_end_var = tk.StringVar(value="")
        entry_end = tk.Entry(dt_frame, textvariable=self.time_end_var, width=12, font=FONT_MAIN)
        entry_end.pack(side="left", padx=2)

        self._updating_time = False
        self.time_end_var.trace_add("write", lambda *args: self._on_end_time_changed())
        self.time_var.trace_add("write", lambda *args: self._on_start_time_changed())
        self.date_var.trace_add("write", lambda *args: self._on_start_time_changed())
        self.duration_var = tk.StringVar(value="")
        self.duration_var.trace_add("write", lambda *args: self._on_duration_changed())

        # Row 4: Total Workout Duration (Durasi Waktu Latihan)
        tk.Label(root, text="Total Waktu Latihan (HH:MM:SS):", font=FONT_BOLD).grid(row=4, column=0, sticky="w", padx=12, pady=6)
        dur_frame = tk.Frame(root)
        dur_frame.grid(row=4, column=1, sticky="w", padx=5, pady=6)
        
        self.duration_var_entry = tk.Entry(dur_frame, textvariable=self.duration_var, width=16, font=FONT_MAIN)
        self.duration_var_entry.pack(side="left", padx=2)
        tk.Label(dur_frame, text="(Atau ketik total menit / detik)", fg="#555555", font=(FONT_FAMILY, 9, "italic")).pack(side="left", padx=6)

        # Row 5: Preset Buttons for Duration
        dur_preset_frame = tk.Frame(root)
        dur_preset_frame.grid(row=5, column=1, sticky="w", padx=5, pady=2)
        
        preset_font = (FONT_FAMILY, 9)
        tk.Button(dur_preset_frame, text="-5 Min", command=lambda: self.adjust_duration_minutes(-5), font=preset_font).pack(side="left", padx=2)
        tk.Button(dur_preset_frame, text="+5 Min", command=lambda: self.adjust_duration_minutes(5), font=preset_font).pack(side="left", padx=2)
        tk.Button(dur_preset_frame, text="-15 Min", command=lambda: self.adjust_duration_minutes(-15), font=preset_font).pack(side="left", padx=2)
        tk.Button(dur_preset_frame, text="+15 Min", command=lambda: self.adjust_duration_minutes(15), font=preset_font).pack(side="left", padx=2)
        tk.Button(dur_preset_frame, text="30 Min", command=lambda: self.set_duration_minutes(30), font=preset_font).pack(side="left", padx=2)
        tk.Button(dur_preset_frame, text="45 Min", command=lambda: self.set_duration_minutes(45), font=preset_font).pack(side="left", padx=2)
        tk.Button(dur_preset_frame, text="60 Min", command=lambda: self.set_duration_minutes(60), font=preset_font).pack(side="left", padx=2)

        # Row 6: Target Avg Heart Rate
        tk.Label(root, text="Target Avg Heart Rate (bpm):", font=FONT_BOLD).grid(row=6, column=0, sticky="w", padx=12, pady=6)
        self.hr_var = tk.StringVar(value="")
        tk.Entry(root, textvariable=self.hr_var, width=28, font=FONT_MAIN).grid(row=6, column=1, sticky="w", padx=5, pady=6)
        
        # Row 7: Target Calories
        tk.Label(root, text="Target Calories (kcal):", font=FONT_BOLD).grid(row=7, column=0, sticky="w", padx=12, pady=6)
        self.cal_var = tk.StringVar(value="")
        tk.Entry(root, textvariable=self.cal_var, width=28, font=FONT_MAIN).grid(row=7, column=1, sticky="w", padx=5, pady=6)
        
        # Row 8: Checkbox Keep Temp
        self.keep_temp_var = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text="Simpan file CSV sementara di folder output", variable=self.keep_temp_var, font=FONT_MAIN).grid(row=8, column=1, sticky="w", padx=5, pady=6)

        # Row 10: Buttons (Process, Strava Upload, List Activities)
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=10, column=1, pady=12, sticky="w")
        
        tk.Button(btn_frame, text=" Modify ", command=self.process, bg="#2e7d32", fg="white", font=(FONT_FAMILY, 11, "bold"), padx=15, pady=4).pack(side="left", padx=5)
        
        self.btn_upload = tk.Button(btn_frame, text="Upload to Strava", command=self.upload_to_strava, bg="#fc4c02", fg="white", font=(FONT_FAMILY, 10, "bold"), padx=10, pady=4, state=tk.DISABLED)
        self.btn_upload.pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Lihat Aktivitas Strava", command=self.list_strava_activities, font=(FONT_FAMILY, 10), padx=10, pady=4).pack(side="left", padx=5)
        
        # Row 11: Embedded Charts (Side by Side)
        self.chart_frame = tk.Frame(root)
        self.chart_frame.grid(row=11, column=0, columnspan=3, pady=10, padx=12, sticky="nsew")
        if MATPLOTLIB_AVAILABLE:
            plt.rcParams.update({
                'font.size': 10,
                'axes.titlesize': 12,
                'axes.labelsize': 10,
                'xtick.labelsize': 9,
                'ytick.labelsize': 9
            })
            self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(11, 4))
            self.fig.tight_layout(pad=3.0)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(fill=tk.BOTH, expand=True)
            self.ax1.set_title("Original HR")
            self.ax1.set_xlabel("Time (s)")
            self.ax1.set_ylabel("BPM")
            self.ax1.grid(True, linestyle='--', alpha=0.6)
            
            self.ax2.set_title("Modified HR")
            self.ax2.set_xlabel("Time (s)")
            self.ax2.set_ylabel("BPM")
            self.ax2.grid(True, linestyle='--', alpha=0.6)
            self.canvas.draw()
        else:
            tk.Label(self.chart_frame, text="Matplotlib tidak terinstall. Chart tidak ditampilkan.", fg="gray", font=FONT_MAIN).pack()

        if os.path.exists(self.input_var.get()):
            self.auto_set_paths(self.input_var.get())

    def _on_start_time_changed(self):
        if self._updating_time: return
        self._updating_time = True
        try:
            start_dt = self.get_current_datetime()
            dur_sec = self.parse_gui_duration()
            if start_dt and dur_sec is not None and dur_sec >= 0:
                end_dt = start_dt + datetime.timedelta(seconds=dur_sec)
                self.time_end_var.set(end_dt.strftime("%H:%M:%S"))
        except Exception:
            pass
        finally:
            self._updating_time = False

    def _on_end_time_changed(self):
        if self._updating_time: return
        self._updating_time = True
        try:
            t_start_str = self.time_var.get().strip()
            t_end_str = self.time_end_var.get().strip()
            if t_start_str and t_end_str:
                s_sec = parse_duration_to_seconds(t_start_str)
                e_sec = parse_duration_to_seconds(t_end_str)
                if s_sec is not None and e_sec is not None:
                    if e_sec < s_sec:
                        e_sec += 86400
                    dur_sec = e_sec - s_sec
                    self.duration_var.set(format_seconds_to_hhmmss(dur_sec))
        except Exception:
            pass
        finally:
            self._updating_time = False

    def _on_duration_changed(self):
        if self._updating_time: return
        self._updating_time = True
        try:
            dur_sec = self.parse_gui_duration()
            if dur_sec is None or dur_sec < 0:
                return

            # Otomatis isi Tanggal jika belum terisi
            if not self.date_var.get().strip():
                self.date_var.set(datetime.datetime.now().strftime("%Y-%m-%d"))

            # Otomatis isi Start Time jika belum terisi
            if not self.time_var.get().strip():
                t_end_str = self.time_end_var.get().strip()
                if t_end_str:
                    t_end_sec = parse_duration_to_seconds(t_end_str)
                    if t_end_sec is not None:
                        t_start_sec = (t_end_sec - dur_sec) % 86400
                        self.time_var.set(format_seconds_to_hhmmss(t_start_sec))
                else:
                    self.time_var.set(datetime.datetime.now().strftime("%H:%M:%S"))

            start_dt = self.get_current_datetime()
            if start_dt:
                end_dt = start_dt + datetime.timedelta(seconds=dur_sec)
                self.time_end_var.set(end_dt.strftime("%H:%M:%S"))
        except Exception:
            pass
        finally:
            self._updating_time = False

    def set_datetime_now(self):
        now = datetime.datetime.now()
        self.date_var.set(now.strftime("%Y-%m-%d"))
        self.time_var.set(now.strftime("%H:%M:%S"))
        self._on_start_time_changed()

    def get_current_datetime(self):
        d_str = self.date_var.get().strip()
        t_str = self.time_var.get().strip()
        if not d_str:
            return None
        if not t_str:
            t_str = "00:00:00"
        try:
            return datetime.datetime.strptime(f"{d_str} {t_str}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    def adjust_days(self, days):
        dt = self.get_current_datetime()
        if dt:
            dt += datetime.timedelta(days=days)
            self.date_var.set(dt.strftime("%Y-%m-%d"))
            self.time_var.set(dt.strftime("%H:%M:%S"))

    def adjust_hours(self, hours):
        dt = self.get_current_datetime()
        if dt:
            dt += datetime.timedelta(hours=hours)
            self.date_var.set(dt.strftime("%Y-%m-%d"))
            self.time_var.set(dt.strftime("%H:%M:%S"))

    def parse_gui_duration(self):
        val = self.duration_var.get().strip()
        if not val:
            return None
        return parse_duration_to_seconds(val)

    def adjust_duration_minutes(self, mins):
        current_sec = self.parse_gui_duration() or 0
        new_sec = max(0, current_sec + (mins * 60))
        self.duration_var.set(format_seconds_to_hhmmss(new_sec))

    def set_duration_minutes(self, mins):
        new_sec = mins * 60
        self.duration_var.set(format_seconds_to_hhmmss(new_sec))

    def auto_set_paths(self, path):
        if os.path.isdir(path):
            self.output_dir_var.set(path.rstrip(os.sep + "/") + "_modified")
        elif os.path.isfile(path):
            base_dir = os.path.dirname(path) or "."
            name = os.path.splitext(os.path.basename(path))[0]
            self.output_dir_var.set(os.path.join(base_dir, f"{name}_modified"))
            extracted_dt, extracted_dur, ext_hr, ext_cal = extract_metadata_from_file(path)
            if extracted_dt:
                parts = extracted_dt.split(" ")
                if len(parts) == 2:
                    self.date_var.set(parts[0])
                    self.time_var.set(parts[1])
                else:
                    self.date_var.set(extracted_dt)
            
            if extracted_dur:
                self.duration_var.set(extracted_dur)
            else:
                self._on_start_time_changed()
                
            if ext_hr:
                self.hr_var.set(ext_hr)
                
            if ext_cal:
                self.cal_var.set(ext_cal)
                
            self.plot_original(path)

    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("FIT / CSV files", "*.fit;*.csv"), ("FIT files", "*.fit"), ("CSV files", "*.csv")])
        if f:
            self.input_var.set(f)
            self.auto_set_paths(f)

    def browse_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.input_var.set(d)
            self.auto_set_paths(d)
            
    def browse_output_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir_var.set(d)
            
    def plot_original(self, file_path):
        if not MATPLOTLIB_AVAILABLE: return
        data = extract_hr_timeseries(file_path)
        self.ax1.clear()
        self.ax1.set_title("Original HR")
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("BPM")
        self.ax1.grid(True, linestyle='--', alpha=0.6)
        if data:
            x = [d['elapsed_sec'] for d in data]
            y = [d['heart_rate'] for d in data]
            self.ax1.plot(x, y, color='blue', alpha=0.7)
            avg_hr = sum(y)/len(y)
            self.ax1.set_title(f"Original HR (Avg: {avg_hr:.1f})")
        self.canvas.draw()
        
    def plot_modified(self, file_path):
        if not MATPLOTLIB_AVAILABLE: return
        data = extract_hr_timeseries(file_path)
        self.ax2.clear()
        self.ax2.set_title("Modified HR")
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("BPM")
        self.ax2.grid(True, linestyle='--', alpha=0.6)
        if data:
            x = [d['elapsed_sec'] for d in data]
            y = [d['heart_rate'] for d in data]
            self.ax2.plot(x, y, color='orange', alpha=0.7)
            avg_hr = sum(y)/len(y)
            self.ax2.set_title(f"Modified HR (Avg: {avg_hr:.1f})")
        self.canvas.draw()
        
    def process(self):
        try:
            hr_val = self.hr_var.get().strip()
            cal_val = self.cal_var.get().strip()
            
            hr = int(hr_val) if hr_val else None
            cal = int(cal_val) if cal_val else None
            
            d_str = self.date_var.get().strip()
            t_str = self.time_var.get().strip()
            
            if d_str:
                if t_str:
                    date_str = f"{d_str} {t_str}"
                else:
                    date_str = f"{d_str} 00:00:00"
            else:
                date_str = None

            dur_sec = self.parse_gui_duration()

            out_dir, files = process_target(
                input_path=self.input_var.get(),
                output_dir=self.output_dir_var.get(),
                target_avg_hr=hr,
                target_calories=cal,
                target_date_str=date_str,
                target_duration_seconds=dur_sec,
                keep_temp=self.keep_temp_var.get()
            )
            
            # Update modified chart
            input_path = self.input_var.get().strip()
            if os.path.isfile(input_path) and len(files) > 0:
                self.plot_modified(files[0])
            
            self.last_files = files
            if len(files) > 0 and STRAVA_AVAILABLE:
                self.btn_upload.config(state=tk.NORMAL)
            
            file_names = "\n".join([os.path.basename(f) for f in files])
            messagebox.showinfo("Success", f"Berhasil memproses {len(files)} file ke folder:\n{out_dir}\n\nFile:\n{file_names}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def upload_to_strava(self):
        if not STRAVA_AVAILABLE:
            messagebox.showerror("Error", "Modul Strava tidak tersedia. Pastikan 'requests' terinstall.")
            return
            
        if not self.last_files:
            messagebox.showwarning("Warning", "Tidak ada file yang baru diproses untuk di-upload.")
            return
            
        self.show_upload_dialog()

    def show_upload_dialog(self):
        top = tk.Toplevel(self.root)
        top.title("Detail Upload Strava")
        top.geometry("450x240")
        top.grab_set()
        
        default_name = os.path.splitext(os.path.basename(self.last_files[0]))[0] if self.last_files else "Activity"
        default_name = default_name.replace("_modified", "").replace("_", " ").title()
        
        tk.Label(top, text="Nama Aktivitas di Strava:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        name_var = tk.StringVar(value=default_name)
        tk.Entry(top, textvariable=name_var, width=45, font=("Segoe UI", 10)).pack(padx=20, pady=2)
        
        tk.Label(top, text="Deskripsi Aktivitas:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(10, 2))
        desc_var = tk.StringVar(value="Uploaded via FIT Activity Modifier")
        tk.Entry(top, textvariable=desc_var, width=45, font=("Segoe UI", 10)).pack(padx=20, pady=2)
        
        def do_upload():
            act_name = name_var.get().strip() or None
            act_desc = desc_var.get().strip() or "Uploaded via FIT Activity Modifier"
            top.destroy()
            
            try:
                results = []
                for f in self.last_files:
                    if f.lower().endswith('.fit'):
                        res = strava_api.upload_fit_file(f, name=act_name, description=act_desc)
                        results.append(f"Upload ID: {res.get('id')} - Status: {res.get('status')}")
                
                if results:
                    messagebox.showinfo("Strava Upload", "Berhasil mengunggah file ke Strava!\n" + "\n".join(results))
                else:
                    messagebox.showwarning("Warning", "Tidak ada file .fit yang ditemukan dari hasil proses.")
            except Exception as e:
                messagebox.showerror("Strava Upload Error", str(e))
                
        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Unggah Sekarang", command=do_upload, bg="#fc4c02", fg="white", font=("Segoe UI", 10, "bold"), padx=10, pady=4).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Batal", command=top.destroy, font=("Segoe UI", 10), padx=10, pady=4).pack(side="left", padx=5)

    def list_strava_activities(self):
        if not STRAVA_AVAILABLE:
            messagebox.showerror("Error", "Modul Strava tidak tersedia.")
            return
            
        try:
            activities = strava_api.get_latest_activities(15)
            if not activities:
                messagebox.showinfo("Aktivitas Strava", "Tidak ada aktivitas ditemukan.")
                return
                
            self.show_activity_manager(activities)
        except Exception as e:
            messagebox.showerror("Strava API Error", str(e))

    def show_activity_manager(self, activities):
        import tkinter.simpledialog
        
        top = tk.Toplevel(self.root)
        top.title("Strava Activity Manager")
        top.geometry("600x400")
        
        tk.Label(top, text="Aktivitas Terbaru di Strava", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        listbox_frame = tk.Frame(top)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        act_map = {}
        for idx, act in enumerate(activities):
            label = f"{act.get('start_date_local')[:10]} | {act.get('name')} (ID: {act.get('id')})"
            listbox.insert(tk.END, label)
            act_map[idx] = act
            
        def on_delete():
            sel = listbox.curselection()
            if not sel: return
            act = act_map[sel[0]]
            act_id = act.get('id')
            if messagebox.askyesno("Konfirmasi", f"Yakin ingin menghapus '{act.get('name')}' dari Strava?\nIni tidak bisa dibatalkan!", parent=top):
                try:
                    strava_api.delete_activity(act_id)
                    messagebox.showinfo("Sukses", "Aktivitas berhasil dihapus.", parent=top)
                    top.destroy()
                    self.list_strava_activities()
                except Exception as e:
                    messagebox.showerror("Error", str(e), parent=top)
                    
        def on_edit():
            sel = listbox.curselection()
            if not sel: return
            act = act_map[sel[0]]
            act_id = act.get('id')
            new_name = tk.simpledialog.askstring("Ganti Nama", "Masukkan nama aktivitas baru:", initialvalue=act.get('name'), parent=top)
            if new_name and new_name != act.get('name'):
                try:
                    strava_api.update_activity(act_id, name=new_name)
                    messagebox.showinfo("Sukses", "Nama berhasil diubah.", parent=top)
                    top.destroy()
                    self.list_strava_activities()
                except Exception as e:
                    messagebox.showerror("Error", str(e), parent=top)
                    
        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Ganti Nama", command=on_edit, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Hapus Aktivitas", command=on_delete, width=15, bg="#d32f2f", fg="white").pack(side=tk.LEFT, padx=5)

def main():
    parser = argparse.ArgumentParser(description="Workflow otomatis modifikasi file FIT / CSV (HR, Kalori, Tanggal, Waktu & Durasi)")
    parser.add_argument("input", nargs="?", help="Path ke file tunggal (.fit/.csv) atau folder berisikan file .fit")
    parser.add_argument("-o", "--output-dir", help="Path folder output hasil modifikasi")
    parser.add_argument("-hr", "--hr", type=int, default=None, help="Target Average Heart Rate (bpm). Default: auto (dari file)")
    parser.add_argument("-c", "--cal", "--calories", type=int, default=None, help="Target Calories (kcal). Default: auto (dari file)")
    parser.add_argument("-d", "--date", help="Target Tanggal ('YYYY-MM-DD' atau 'YYYY-MM-DD HH:MM:SS')")
    parser.add_argument("-t", "--time", help="Target Waktu ('HH:MM:SS')")
    parser.add_argument("--dur", "--duration", help="Target Durasi Latihan ('HH:MM:SS', '45m', '2700', dll)")
    parser.add_argument("--now", action="store_true", help="Gunakan tanggal & waktu saat ini")
    parser.add_argument("--shift-days", type=int, default=0, help="Geser tanggal dalam satuan hari (+1, -1, dst)")
    parser.add_argument("--shift-hours", type=int, default=0, help="Geser waktu dalam satuan jam (+2, -2, dst)")
    parser.add_argument("--keep-temp", action="store_true", help="Simpan file CSV sementara di folder output")
    parser.add_argument("--gui", action="store_true", help="Jalankan antarmuka grafis (GUI)")
    parser.add_argument("--upload", action="store_true", help="Otomatis unggah hasil modifikasi ke Strava")
    parser.add_argument("--list-strava", action="store_true", help="Tampilkan daftar aktivitas terbaru di Strava")
    parser.add_argument("--delete-strava", type=int, help="Hapus aktivitas Strava berdasarkan ID")
    parser.add_argument("--edit-strava", type=int, help="Edit aktivitas Strava berdasarkan ID")
    parser.add_argument("--name", type=str, help="Nama aktivitas baru (digunakan dengan --upload atau --edit-strava)")
    parser.add_argument("--desc", "--description", type=str, help="Deskripsi aktivitas (digunakan dengan --upload)")

    args = parser.parse_args()

    if args.delete_strava:
        if not STRAVA_AVAILABLE:
            print("Error: Modul Strava tidak tersedia.", file=sys.stderr)
            sys.exit(1)
        try:
            print(f"Menghapus aktivitas {args.delete_strava} dari Strava...")
            strava_api.delete_activity(args.delete_strava)
            print("Berhasil dihapus.")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        return

    if args.edit_strava and args.name:
        if not STRAVA_AVAILABLE:
            print("Error: Modul Strava tidak tersedia.", file=sys.stderr)
            sys.exit(1)
        try:
            print(f"Mengubah nama aktivitas {args.edit_strava} menjadi '{args.name}'...")
            strava_api.update_activity(args.edit_strava, name=args.name)
            print("Berhasil diubah.")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        return

    if args.list_strava:
        if not STRAVA_AVAILABLE:
            print("Error: Modul Strava tidak tersedia. Pastikan 'requests' terinstall.", file=sys.stderr)
            sys.exit(1)
        try:
            activities = strava_api.get_latest_activities(5)
            print("=== 5 Aktivitas Terakhir di Strava ===")
            for act in activities:
                print(f"- {act.get('name')} ({act.get('start_date_local')}) - ID: {act.get('id')}")
        except Exception as e:
            print(f"Error fetching Strava activities: {e}", file=sys.stderr)
            sys.exit(1)
        if not args.input and not args.gui:
            return  # Exit jika hanya ingin menampilkan list

    if not args.input or args.gui:
        root = tk.Tk()
        app = App(root)
        root.mainloop()
    else:
        try:
            target_date_str = None
            if args.now:
                target_date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif args.date:
                d = args.date.strip()
                if " " in d:
                    target_date_str = d
                elif args.time:
                    target_date_str = f"{d} {args.time.strip()}"
                else:
                    target_date_str = f"{d} 00:00:00"
            elif args.time:
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                target_date_str = f"{today} {args.time.strip()}"

            relative_shift = (args.shift_days * 86400) + (args.shift_hours * 3600)
            target_dur_sec = parse_duration_to_seconds(args.dur) if args.dur else None

            out_dir, files = process_target(
                input_path=args.input,
                output_dir=args.output_dir,
                target_avg_hr=args.hr,
                target_calories=args.cal,
                target_date_str=target_date_str,
                relative_shift_seconds=relative_shift,
                target_duration_seconds=target_dur_sec,
                keep_temp=args.keep_temp
            )
            
            if args.upload and STRAVA_AVAILABLE:
                for f in files:
                    if f.lower().endswith('.fit'):
                        try:
                            print(f"Mengunggah {os.path.basename(f)} ke Strava...")
                            res = strava_api.upload_fit_file(f, name=args.name, description=args.desc or "Uploaded via FIT Activity Modifier")
                            print(f"Berhasil! Upload ID: {res.get('id')} - Status: {res.get('status')}")
                        except Exception as e:
                            print(f"Gagal mengunggah {os.path.basename(f)}: {e}", file=sys.stderr)
                            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
