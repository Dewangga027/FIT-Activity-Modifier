# FIT Activity Modifier

Proyek ini adalah alat untuk memodifikasi file `.fit` atau `.csv` aktivitas olahraga (misalnya dari Huawei Health) sebelum diunggah ke platform seperti Strava. Alat ini memungkinkan modifikasi pada berbagai metrik seperti detak jantung (Heart Rate), kalori, tanggal, waktu, dan durasi latihan.

Alat ini menggunakan **FitCSVTool** dari Garmin FIT SDK untuk mengonversi file biner `.fit` menjadi `.csv` untuk dimodifikasi, dan mengonversinya kembali menjadi file `.fit` yang siap diunggah.

## Fitur Utama

- **GUI & CLI:** Tersedia antarmuka grafis (GUI) yang ramah pengguna dan antarmuka baris perintah (CLI) untuk otomatisasi.
- **Modifikasi Heart Rate:** Menaikkan atau menurunkan rata-rata Heart Rate secara proporsional.
- **Modifikasi Kalori:** Mengubah total kalori yang terbakar.
- **Modifikasi Waktu:** Mengubah tanggal dan waktu mulai aktivitas (mendukung pergeseran relatif dalam hari/jam atau pengaturan waktu absolut).
- **Modifikasi Durasi:** Memperpanjang atau memperpendek durasi aktivitas.
- **Batch Processing:** Mendukung pemrosesan satu file atau seluruh folder sekaligus.

## Kebutuhan Sistem

1. **Python 3.x**
2. **Java (JRE/JDK 8 atau lebih baru)**: Diperlukan untuk menjalankan `FitCSVTool.jar`.

## Cara Penggunaan

### Menggunakan GUI (Antarmuka Grafis)

Jalankan script tanpa argumen untuk membuka mode GUI:

```bash
python modifier.py
# atau
python modifier.py --gui
```

Di dalam aplikasi:
1. Pilih file (`.fit` / `.csv`) atau folder yang berisi file aktivitas.
2. Tentukan folder output untuk menyimpan hasil modifikasi.
3. Centang metrik yang ingin diubah dan masukkan nilai targetnya.
4. Klik **Proses File**.

### Menggunakan CLI (Command Line Interface)

Script ini dapat dijalankan langsung dari terminal/command prompt, yang sangat berguna untuk otomatisasi (misalnya via Termux atau cron job).

```bash
python modifier.py [input_path] -o [output_folder] [options]
```

**Opsi yang tersedia:**
- `-hr, --hr <nilai>`: Target Average Heart Rate (bpm).
- `-c, --cal <nilai>`: Target Kalori (kcal).
- `-d, --date <YYYY-MM-DD>`: Target Tanggal.
- `-t, --time <HH:MM:SS>`: Target Waktu.
- `--dur <durasi>`: Target Durasi (contoh: `01:00:00`, `45m`, `2700`).
- `--now`: Menggunakan tanggal & waktu saat ini.
- `--shift-days <angka>`: Geser tanggal (contoh: `+1` atau `-1`).
- `--shift-hours <angka>`: Geser waktu (contoh: `+2` atau `-2`).
- `--keep-temp`: Simpan file CSV sementara di folder output untuk debugging.

**Contoh:**
```bash
# Modifikasi satu file agar memiliki avg HR 150 bpm dan durasi 45 menit
python modifier.py fit/aktivitas.fit -o fit/output -hr 150 --dur 45m

# Modifikasi semua file di folder untuk digeser 1 hari ke depan
python modifier.py fit/ -o fit/output --shift-days 1
```

## Struktur Direktori
- `modifier.py`: Script utama untuk modifikasi.
- `FitCSVTool.jar`: Tool bawaan Garmin FIT SDK untuk konversi FIT <-> CSV.
- `fit/` & `plan/`: Folder yang direkomendasikan sebagai tempat penyimpanan file aktivitas dan dokumen rencana (diabaikan oleh git).
