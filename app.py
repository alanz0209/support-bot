from flask import Flask, render_template, request, jsonify
from backend.database import Database
from backend.bot_engine import SupportBot
from config import Config
from collections import Counter

app = Flask(__name__, 
            template_folder='frontend/templates', 
            static_folder='frontend/static')
app.config['SECRET_KEY'] = Config.SECRET_KEY

db = Database()
bot = SupportBot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'reply': 'Please enter a message.'}), 400
    
    bot_response = bot.get_response(user_message)
    db.save_ticket(user_message, bot_response)
    
    return jsonify({'reply': bot_response})

@app.route('/dashboard')
def dashboard():
    tickets = db.get_all_tickets()
    return render_template('dashboard.html', tickets=tickets)

@app.route('/dashboard')
def dashboard():
    tickets = db.get_all_tickets()
    
    # Stats
    total = len(tickets)
    unresolved = sum(1 for t in tickets if "support@company.com" in t[2])
    
    return render_template('dashboard.html', 
                         tickets=tickets,
                         total=total,
                         unresolved=unresolved)

if __name__ == '__main__':
    # Ensure data directory exists
    import os
    os.makedirs('data', exist_ok=True)
    app.run(debug=True, port=5000)