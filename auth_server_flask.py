from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Dummy user
users = { "admin": generate_password_hash("12345") }

# Konfigurasi JWT
JWT_SECRET = "super-secret"
JWT_EXPIRY = 60 * 60  # 1 jam

# Logging ke file
logging.basicConfig(filename='agent_activity.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Penyimpanan IP agent
connected_agents = []

def generate_token(username):
    payload = {
        'user': username,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=JWT_EXPIRY)
        }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return decoded['user']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ✅ Route tambahan supaya tidak error "Not Found"
@app.route('/')
def index():
    return jsonify({"message": "Server otentikasi Flask aktif."})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username in users and check_password_hash(users[username], password):
        token = generate_token(username)
        return jsonify({ "success": True, "token": token })
    else:
        return jsonify({ "success": False, "message": "Invalid credentials" }), 401

@app.route('/check-auth', methods=['GET'])
def check_auth():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    return jsonify({ "authenticated": bool(user), "user": user if user else None })

@socketio.on('connect')
def on_connect():
    agent_ip = request.remote_addr or 'unknown'
    if agent_ip not in connected_agents:
        connected_agents.append(agent_ip)
    print(f"🔌 Agent connected: {agent_ip}")
    emit('agent_list', connected_agents, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    agent_ip = request.remote_addr or 'unknown'
    if agent_ip in connected_agents:
        connected_agents.remove(agent_ip)
    print(f"❌ Agent disconnected: {agent_ip}")
    emit('agent_list', connected_agents, broadcast=True)

@socketio.on('migrate_agent')
def handle_migration(data):
    host = data.get('host')
    port = data.get('port')
    msg = f"Agent migrated to {host}:{port}"
    print(msg)
    logging.info(msg)
    emit('status', msg, broadcast=True)
    emit('agent_output', msg, broadcast=True)
    
@socketio.on('agent_activity')
def handle_activity(data):
    print(f"Received activity: {data}")  # Debug log
    emit('agent_output', data, broadcast=True) 
    

if __name__ == '__main__':
    print("🚀 Server berjalan di http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
