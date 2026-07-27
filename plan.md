# Rencana Implementasi: Huawei Health ke Strava Auto-Modifier

Berdasarkan informasi bahwa Anda menggunakan **Huawei Watch Fit 4** dan aplikasi **Huawei Health** yang sudah *auto-sync* ke Strava, ada tantangan khusus: **Ekosistem Huawei Health sangat tertutup**. 

Kita **tidak bisa** mencegat data secara langsung di tengah-tengah transmisi antara Server Huawei dan Server Strava selama fitur *Auto-Sync* di aplikasi Huawei Health diaktifkan. 

Namun, kita bisa mengakali hal ini. Berikut adalah opsi-opsi alur (workflow) beserta kebutuhan perangkat (hardware/software) yang bisa kita gunakan:

---

## Opsi Workflow (Alur Kerja)

### Opsi 1: "Replace" via Strava Webhook (Paling Disarankan & Otomatis)
Dalam opsi ini, Anda **tetap menyalakan** *auto-sync* dari Huawei Health ke Strava.
1. Huawei Health otomatis mengunggah aktivitas asli ke Strava (HR belum diubah).
2. Sistem kita menerima notifikasi kilat dari Strava (Webhook) bahwa ada aktivitas baru.
3. Sistem dengan sangat cepat mengunduh data aktivitas tersebut dari Strava, kemudian **menghapus aktivitas asli** dari akun Strava Anda.
4. Sistem menjalankan algoritma `modifier.py` untuk menaikkan Average HR (misal khusus untuk HIIT).
5. Sistem mengunggah kembali aktivitas yang sudah dimodifikasi ke Strava sebagai aktivitas baru.
*Proses ini memakan waktu kurang dari 5-10 detik setelah Huawei mengunggah ke Strava.*

### Opsi 2: Ekspor Lokal via Android + Termux (Lebih Manual tapi Presisi)
Dalam opsi ini, Anda **mematikan** *auto-sync* Strava di Huawei Health.
1. Anda menggunakan aplikasi pihak ketiga di HP Android (seperti **Health Sync**) untuk mengekspor aktivitas dari Huawei Health ke sebuah *folder lokal* di HP dalam format `.fit` atau `.tcx`.
2. Anda menginstal **Termux** (aplikasi Terminal Linux untuk Android) di HP Anda.
3. Skrip Python kita berjalan di latar belakang (background) pada Termux di HP Anda, memantau folder tersebut.
4. Saat skrip mendeteksi ada file baru, ia memodifikasinya dan langsung mengunggahnya ke Strava via API.

---

## Kebutuhan Hardware & Software

Tergantung dari opsi mana yang Anda pilih, berikut yang perlu disiapkan:

**Jika memilih Opsi 1 (Strava Webhook - Paling Otomatis):**
- **Hardware:** Anda butuh *server* atau alat yang menyala 24/7. Anda bisa menggunakan:
  - **Microcontroller/SBC:** Raspberry Pi (rekomendasi terbaik untuk di rumah, irit listrik).
  - **Cloud Server (VPS):** Layanan Cloud gratis/murah (Google Cloud Free Tier, AWS, DigitalOcean). Ini paling stabil.
- **Software:** Python, Script Webhook Listener (Flask/FastAPI), Strava API App.

**Jika memilih Opsi 2 (Lokal HP Android - Termux):**
- **Hardware:** Hanya HP Android Anda.
- **Software:** 
  - Aplikasi [Health Sync](https://play.google.com/store/apps/details?id=nl.appyhapps.healthsync) (untuk menarik data dari Huawei).
  - Aplikasi [Termux](https://f-droid.org/en/packages/com.termux/).
  - Python (diinstal di dalam Termux).

---

> [!IMPORTANT]
> ## Pertanyaan Terbuka untuk Anda (User Review Required)
> 
> 1. **Pilih Opsi:** Apakah Anda lebih memilih **Opsi 1** (menggunakan server/Raspberry Pi/Cloud agar 100% transparan dan tidak membebani HP) atau **Opsi 2** (semua diproses di HP Android Anda menggunakan Termux)?
> 2. **Jika Opsi 1:** Apakah Anda sudah memiliki Raspberry Pi atau familiar dengan penyewaan Cloud Server/VPS? Jika belum, saya bisa bantu memandunya.
> 3. **Format Data Opsi 1:** Opsi 1 akan menarik "Stream Data" (Titik GPS, Waktu, HR) dari Strava untuk dimodifikasi, bukan file FIT asli dari Huawei. Apakah tidak masalah jika beberapa metrik eksklusif Huawei (seperti Running Dynamics jika ada) tidak ikut terbawa? Jika HIIT, biasanya stream data standar (HR, Kalori, Waktu) sudah sangat cukup.
> 4. **Logika Modifikasi:** Untuk otomatisasi ini, bagaimana aturan modifikasinya? Apakah otomatis mencari rata-rata HR lalu menambahkannya misal +15 BPM, atau Anda ingin mendefinisikan target mutlak (misal selalu 150 BPM)?
