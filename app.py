# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit
from backend.database import Database
from backend.bot_engine import SupportBot
from config import Config
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__, 
            template_folder='frontend/templates', 
            static_folder='frontend/static')
app.config.from_object(Config)

# Initialisation extensions
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

# Hash du mot de passe admin (une seule fois au démarrage)
ADMIN_PASSWORD_HASH = generate_password_hash(Config.ADMIN_PASSWORD)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== ROUTES AUTH ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == Config.ADMIN_EMAIL and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            session['admin_email'] = email
            flash('✅ Connexion réussie !', 'success')
            return redirect(url_for('admin_dashboard'))
        
        flash('❌ Email ou mot de passe incorrect', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('admin_email', None)
    flash('👋 Déconnecté', 'info')
    return redirect(url_for('index'))

def login_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('🔐 Veuillez vous connecter', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ==================== ROUTES PUBLIQUES ====================
@app.route('/')
def index():
    return render_template('index.html')

# ==================== ROUTES ADMIN (CACHÉES) ====================
@app.route('/admin')
@login_required
def admin_dashboard():
    tickets = db.get_all_tickets()
    stats = db.get_ticket_stats()
    activity_log = db.get_activity_log(50)
    return render_template('dashboard.html', tickets=tickets, stats=stats, activity_log=activity_log)

@app.route('/admin/analytics')
@login_required
def admin_analytics():
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
    
    # Détection urgence : IA + Mots-clés
    is_urgent = bot.detect_urgency(user_message)
    priority = 'urgent' if is_urgent else 'normal'
    
    ticket_id = db.save_ticket(user_message, result['reply'], file_url, result['source'], priority)
    
    # 🚨 Si urgent → Email + WebSocket
    if is_urgent:
        send_urgent_email(ticket_id, user_message)
        socketio.emit('urgent_ticket', {
            'id': ticket_id,
            'message': user_message[:100],
            'priority': 'urgent',
            'timestamp': datetime.now().strftime('%H:%M')
        })
    
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
    ticket = db.get_ticket(ticket_id)
    old_status = ticket[3] if ticket else None
    
    db.update_ticket_status(ticket_id, data.get('status', 'open'))
    
    # Journal d'activité
    db.log_activity(
        session.get('admin_email'),
        'status_change',
        ticket_id,
        f"{old_status} → {data.get('status')}"
    )
    
    # Notification WebSocket
    socketio.emit('ticket_updated', {
        'id': ticket_id,
        'field': 'status',
        'old': old_status,
        'new': data.get('status')
    })
    
    return jsonify({'success': True})

@app.route('/api/tickets/<int:ticket_id>/priority', methods=['PUT'])
@login_required
def update_ticket_priority(ticket_id):
    data = request.json
    ticket = db.get_ticket(ticket_id)
    
    db.update_ticket_priority(ticket_id, data.get('priority', 'normal'))
    
    # Journal d'activité
    db.log_activity(
        session.get('admin_email'),
        'priority_change',
        ticket_id,
        f"→ {data.get('priority')}"
    )
    
    socketio.emit('ticket_updated', {
        'id': ticket_id,
        'field': 'priority',
        'new': data.get('priority')
    })
    
    return jsonify({'success': True})

@app.route('/api/tickets/<int:ticket_id>/notify', methods=['POST'])
@login_required
def notify_user(ticket_id):
    """Envoie un email à l'utilisateur quand le ticket est résolu"""
    data = request.json
    user_email = data.get('email')
    
    if not user_email:
        return jsonify({'error': 'Email requis'}), 400
    
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket non trouvé'}), 404
    
    try:
        msg = Message(
            subject=f'✅ Votre demande #{ticket_id} a été traitée',
            recipients=[user_email],
            body=f'''
Bonjour,

Votre ticket de support #{ticket_id} a été marqué comme résolu.

📝 Votre demande : {ticket[1]}

🤖 Réponse apportée :
{ticket[2]}

Si vous avez d'autres questions, répondez simplement à cet email
ou créez un nouveau ticket sur notre chat.

Cordialement,
L'équipe Support
            ''',
            sender=Config.MAIL_DEFAULT_SENDER
        )
        mail.send(msg)
        
        # Journal d'activité
        db.log_activity(
            session.get('admin_email'),
            'user_notified',
            ticket_id,
            f"Email envoyé à {user_email}"
        )
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")
        return jsonify({'error': str(e)}), 500

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

👉 Voir le dashboard: http://localhost:5000/admin
            ''',
            sender=Config.MAIL_DEFAULT_SENDER
        )
        mail.send(msg)
        print(f"✅ Email d'alerte envoyé pour ticket #{ticket_id}")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

# ==================== WEBSOCKET EVENTS ====================
@socketio.on('connect')
def handle_connect():
    print(f"🔌 Client connecté: {request.sid}")
    emit('connected', {'message': 'Connecté au serveur temps réel'})

@socketio.on('admin_join')
def handle_admin_join():
    if session.get('logged_in'):
        emit('admin_online', {'count': 1}, broadcast=True)

# ==================== LANCEMENT ====================
if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)