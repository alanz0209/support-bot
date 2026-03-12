# app.py - Version complète avec Auth + Email + WebSocket
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit
from backend.database import Database
from backend.bot_engine import SupportBot
from config import Config
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import threading

app = Flask(__name__, 
            template_folder='frontend/templates', 
            static_folder='frontend/static')
app.config.from_object(Config)

# Initialisation extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration upload
UPLOAD_FOLDER = 'frontend/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf', 'log'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialisation bot et database
db = Database()
bot = SupportBot()

# ==================== USER MODEL ====================
class Admin(UserMixin):
    def __init__(self, email, password_hash):
        self.id = email
        self.email = email
        self.password_hash = password_hash
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    if user_id == Config.ADMIN_EMAIL:
        return Admin(Config.ADMIN_EMAIL, generate_password_hash(Config.ADMIN_PASSWORD))
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== ROUTES AUTH ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == Config.ADMIN_EMAIL and check_password_hash(generate_password_hash(Config.ADMIN_PASSWORD), password):
            # Pour simplifier, on utilise session directement
            session['logged_in'] = True
            session['admin_email'] = email
            flash('✅ Connexion réussie !', 'success')
            return redirect(url_for('dashboard'))
        
        flash('❌ Email ou mot de passe incorrect', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('admin_email', None)
    flash('👋 Déconnecté', 'info')
    return redirect(url_for('index'))

def login_required(f):
    """Décorateur pour protéger les routes admin"""
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('🔐 Veuillez vous connecter', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ==================== ROUTES PRINCIPALES ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    tickets = db.get_all_tickets()
    stats = db.get_ticket_stats()
    return render_template('dashboard.html', tickets=tickets, stats=stats)

@app.route('/analytics')
@login_required
def analytics():
    stats = db.get_ticket_stats()
    analytics_data = db.get_analytics()
    return render_template('analytics.html', stats=stats, analytics=analytics_data)

# ==================== API CHAT ====================
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    file_url = data.get('file_url')
    
    if not user_message and not file_url:
        return jsonify({'reply': 'Veuillez entrer un message ou joindre un fichier.'}), 400
    
    result = bot.get_response(user_message, file_url)
    ticket_id = db.save_ticket(user_message, result['reply'], file_url, result['source'])
    
    # 🚨 Notification WebSocket si ticket urgent
    if 'urgent' in user_message.lower() or 'critique' in user_message.lower():
        socketio.emit('urgent_ticket', {
            'id': ticket_id,
            'message': user_message[:100],
            'priority': 'urgent',
            'timestamp': datetime.now().strftime('%H:%M')
        }, broadcast=True)
        
        # 📧 Envoyer email d'alerte
        send_urgent_email(ticket_id, user_message)
    
    return jsonify({
        'reply': result['reply'],
        'source': result['source'],
        'ticket_id': ticket_id
    })

# ==================== UPLOAD ====================
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/static/uploads/{filename}'
        })
    
    return jsonify({'error': 'Type de fichier non autorisé'}), 400

# ==================== FEEDBACK & TICKETS ====================
@app.route('/api/feedback', methods=['POST'])
def save_feedback():
    data = request.json
    db.save_feedback(data.get('positive', False))
    return jsonify({'success': True})

@app.route('/api/tickets/<int:ticket_id>/status', methods=['PUT'])
@login_required
def update_ticket_status(ticket_id):
    data = request.json
    old_status = db.get_ticket(ticket_id)[3] if db.get_ticket(ticket_id) else None
    db.update_ticket_status(ticket_id, data.get('status', 'open'))
    
    # Notification WebSocket
    socketio.emit('urgent_ticket', {
    'id': ticket_id,
    'message': user_message[:100],
    'priority': 'urgent',
    'timestamp': datetime.now().strftime('%H:%M')
}, broadcast_to=None)
    
    return jsonify({'success': True})

@app.route('/api/tickets/<int:ticket_id>/priority', methods=['PUT'])
@login_required
def update_ticket_priority(ticket_id):
    data = request.json
    db.update_ticket_priority(ticket_id, data.get('priority', 'normal'))
    
    socketio.emit('ticket_updated', {
        'id': ticket_id,
        'field': 'priority',
        'new': data.get('priority')
    }, broadcast=True)
    
    return jsonify({'success': True})

# ==================== EMAIL NOTIFICATIONS ====================
def send_urgent_email(ticket_id, message):
    """Envoie un email d'alerte pour ticket urgent"""
    try:
        msg = Message(
            subject=f'🔴 Ticket Urgent #{ticket_id}',
            recipients=[Config.ADMIN_EMAIL],
            body=f'''
Nouveau ticket urgent détecté !

🎫 ID: #{ticket_id}
📝 Message: {message}
🕐 Heure: {datetime.now().strftime('%d/%m/%Y %H:%M')}

👉 Voir le dashboard: http://localhost:5000/dashboard
            ''',
            sender=Config.MAIL_DEFAULT_SENDER
        )
        mail.send(msg)
        print(f"✅ Email d'alerte envoyé pour ticket #{ticket_id}")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

def send_ticket_notification(ticket_id, status):
    """Notification pour changement de statut"""
    try:
        msg = Message(
            subject=f'📋 Ticket #{ticket_id} → {status}',
            recipients=[Config.ADMIN_EMAIL],
            body=f'Le ticket #{ticket_id} a été marqué comme "{status}".\n\nVoir: http://localhost:5000/dashboard',
            sender=Config.MAIL_DEFAULT_SENDER
        )
        mail.send(msg)
    except Exception as e:
        print(f"❌ Erreur notification : {e}")

# ==================== WEBSOCKET EVENTS ====================
@socketio.on('connect')
def handle_connect():
    print(f"🔌 Client connecté: {request.sid}")
    emit('connected', {'message': 'Connecté au serveur temps réel'})

@socketio.on('admin_join')
def handle_admin_join():
    """Un admin rejoint le dashboard en temps réel"""
    if session.get('logged_in'):
        emit('admin_online', {'count': 1}, broadcast=True)

# ==================== LANCEMENT ====================
if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    # Pour le dev: debug=True, pour prod: use eventlet
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)