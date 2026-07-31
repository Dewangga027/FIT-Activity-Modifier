import json
import requests
import os
import webbrowser

CONFIG_FILE = "strava_config.json"

def main():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} tidak ditemukan.")
        return
        
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    
    if not client_id or not client_secret:
        print("Client ID atau Client Secret kosong di strava_config.json!")
        return

    # 1. Buat URL Otorisasi dengan scope yang benar
    auth_url = (f"https://www.strava.com/oauth/authorize?"
                f"client_id={client_id}&response_type=code"
                f"&redirect_uri=http://localhost/exchange_token"
                f"&approval_prompt=force&scope=activity:write,activity:read_all")
                
    print("\n" + "="*60)
    print("MOHON BUKA URL BERIKUT DI BROWSER ANDA:")
    print(auth_url)
    print("="*60 + "\n")
    
    try:
        webbrowser.open(auth_url)
    except:
        pass
        
    print("Setelah Anda klik 'Authorize', browser akan beralih ke halaman error (localhost).")
    print("Lihat URL di address bar browser Anda, cari bagian 'code=....'")
    print("Contoh: http://localhost/exchange_token?state=&code=b50...&scope=...\n")
    
    # 2. Minta user memasukkan code
    code = input("Masukkan nilai CODE dari URL tersebut: ").strip()
    
    if not code:
        print("Code tidak boleh kosong.")
        return
        
    # 3. Tukar code dengan token baru
    print("\nMenukar code dengan token baru...")
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }
    
    res = requests.post("https://www.strava.com/api/v3/oauth/token", data=payload)
    
    if res.status_code == 200:
        data = res.json()
        config['access_token'] = data.get('access_token')
        config['refresh_token'] = data.get('refresh_token')
        config['expires_at'] = data.get('expires_at')
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
            
        print("✅ BERHASIL! Token baru dengan izin baca & tulis telah disimpan ke strava_config.json")
    else:
        print(f"❌ GAGAL: {res.text}")

if __name__ == "__main__":
    main()
