import socketio
import time
import random
import threading
import requests

# Konfigurasi server
SERVER_URL = 'http://localhost:5000'
USERNAME = 'admin'
PASSWORD = '12345'

def get_jwt_token():
    """Mendapatkan token JWT untuk autentikasi"""
    try:
        response = requests.post(
            f'{SERVER_URL}/login',
            json={'username': USERNAME, 'password': PASSWORD}
        )
        data = response.json()
        if data.get('success'):
            print("✅ Login berhasil! Token diterima.")
            return data['token']
        else:
            print(f"❌ Login gagal: {data.get('message')}")
            return None
    except Exception as e:
        print(f"⚠️ Error saat login: {e}")
        return None

def send_activity():
    """Mengirim data aktivitas agent ke server setiap 1 detik"""
    while True:
        activity_value = round(random.uniform(0.1, 1.0), 2)  # Nilai acak 0.1-1.0
        sio.emit('agent_activity', {'value': activity_value})
        print(f"📊 Mengirim data aktivitas: {activity_value}")
        time.sleep(1)  # Interval pengiriman

# Inisialisasi Socket.IO Client
sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=5,
    reconnection_delay=1000
)
token = get_jwt_token()

# Handler event Socket.IO
@sio.event
def connect():
    print("🔌 Terhubung ke server.")
    # Kirim info migrasi HANYA SEKALI
    sio.emit('migrate_agent', {'host': '192.168.1.2', 'port': 8000})
    # Mulai kirim data aktivitas
    threading.Thread(target=send_activity, daemon=True).start()
    
@sio.event
def disconnect():
    print("❌ Terputus dari server.")

@sio.on('status')
def on_status(message):
    print(f"[STATUS] {message}")

@sio.on('agent_list')
def on_agent_list(agents):
    print(f"🌐 Daftar agent aktif: {agents}")

# Jalankan client jika token valid
if token:
    try:
        sio.connect(
            SERVER_URL,
            headers={'Authorization': f'Bearer {token}'}
        )
        sio.wait()  # Pertahankan koneksi
    except Exception as e:
        print(f"🚫 Gagal terhubung ke server: {e}")
else:
    print("⛔ Tidak ada token, agent tidak dijalankan.")