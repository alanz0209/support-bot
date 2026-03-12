# app.py
from flask import Flask, render_template, request, jsonify
from backend.database import Database
from backend.bot_engine import SupportBot
from config import Config
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__, 
            template_folder='frontend/templates', 
            static_folder='frontend/static')
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Configuration upload
UPLOAD_FOLDER = 'frontend/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf', 'log'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialisation bot et database
db = Database()
bot = SupportBot()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    tickets = db.get_all_tickets()
    stats = db.get_ticket_stats()
    return render_template('dashboard.html', tickets=tickets, stats=stats)

@app.route('/analytics')
def analytics():
    stats = db.get_ticket_stats()
    analytics_data = db.get_analytics()
    return render_template('analytics.html', stats=stats, analytics=analytics_data)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    file_url = data.get('file_url')
    
    if not user_message and not file_url:
        return jsonify({'reply': 'Veuillez entrer un message ou joindre un fichier.'}), 400
    
    result = bot.get_response(user_message, file_url)
    ticket_id = db.save_ticket(user_message, result['reply'], file_url, result['source'])
    
    return jsonify({
        'reply': result['reply'],
        'source': result['source'],
        'ticket_id': ticket_id
    })

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

@app.route('/api/feedback', methods=['POST'])
def save_feedback():
    data = request.json
    db.save_feedback(data.get('positive', False))
    return jsonify({'success': True})

@app.route('/api/tickets/<int:ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    data = request.json
    db.update_ticket_status(ticket_id, data.get('status', 'open'))
    return jsonify({'success': True})

@app.route('/api/tickets/<int:ticket_id>/priority', methods=['PUT'])
def update_ticket_priority(ticket_id):
    data = request.json
    db.update_ticket_priority(ticket_id, data.get('priority', 'normal'))
    return jsonify({'success': True})

# ==================== LANCEMENT ====================

if __name__ == '__main__':
    # S'assurer que le dossier data existe
    os.makedirs('data', exist_ok=True)
    app.run(debug=True, port=5000)