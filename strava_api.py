import os
import json
import requests
import time

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "strava_config.json")
STRAVA_API_BASE = "https://www.strava.com/api/v3"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Konfigurasi Strava tidak ditemukan: {CONFIG_FILE}")
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def refresh_token(config):
    """Memperbarui access_token menggunakan refresh_token."""
    payload = {
        'client_id': config.get('client_id'),
        'client_secret': config.get('client_secret'),
        'refresh_token': config.get('refresh_token'),
        'grant_type': 'refresh_token',
    }
    
    if not payload['client_id'] or not payload['client_secret'] or not payload['refresh_token']:
        raise ValueError("Client ID, Client Secret, dan Refresh Token harus diisi di strava_config.json")

    response = requests.post("https://www.strava.com/api/v3/oauth/token", data=payload)
    if response.status_code == 200:
        data = response.json()
        config['access_token'] = data.get('access_token')
        config['refresh_token'] = data.get('refresh_token') # Refresh token juga bisa berubah
        config['expires_at'] = data.get('expires_at')
        save_config(config)
        return config['access_token']
    else:
        raise Exception(f"Gagal memperbarui token Strava: {response.text}")

def get_valid_token():
    """Mendapatkan access_token yang valid. Akan melakukan refresh jika kedaluwarsa."""
    config = load_config()
    
    # Cek apakah token sudah kedaluwarsa (berikan buffer 5 menit)
    expires_at = config.get('expires_at', 0)
    current_time = int(time.time())
    
    if not config.get('access_token') or current_time >= (expires_at - 300):
        return refresh_token(config)
    
    return config.get('access_token')

def upload_fit_file(filepath, activity_type="run", name=None, description="Uploaded via FIT Activity Modifier"):
    """Mengunggah file .fit ke Strava."""
    token = get_valid_token()
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    if not name:
        filename = os.path.basename(filepath)
        name = f"Activity {filename}"
        
    data = {
        'name': name,
        'description': description,
        'data_type': 'fit',
        'trainer': 0,
        'commute': 0
    }
    
    with open(filepath, 'rb') as f:
        files = {
            'file': (os.path.basename(filepath), f, 'application/vnd.ant.fit')
        }
        response = requests.post(f"{STRAVA_API_BASE}/uploads", headers=headers, data=data, files=files)
        
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Gagal mengunggah ke Strava: {response.text}")

def get_latest_activities(limit=5):
    """Mengambil daftar aktivitas terakhir dari Strava."""
    token = get_valid_token()
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    params = {
        'per_page': limit,
        'page': 1
    }
    
    response = requests.get(f"{STRAVA_API_BASE}/athlete/activities", headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Gagal mengambil aktivitas Strava: {response.text}")

def check_upload_status(upload_id):
    """Mengecek status proses upload di server Strava."""
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{STRAVA_API_BASE}/uploads/{upload_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Gagal mengecek status upload: {response.text}")

def delete_activity(activity_id):
    """Menghapus aktivitas dari Strava."""
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(f"{STRAVA_API_BASE}/activities/{activity_id}", headers=headers)
    if response.status_code == 204:
        return True
    else:
        raise Exception(f"Gagal menghapus aktivitas: {response.text}")

def update_activity(activity_id, name=None, description=None, type=None):
    """Mengubah metadata aktivitas di Strava."""
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {}
    if name: data['name'] = name
    if description: data['description'] = description
    if type: data['type'] = type
        
    response = requests.put(f"{STRAVA_API_BASE}/activities/{activity_id}", headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Gagal mengupdate aktivitas: {response.text}")
