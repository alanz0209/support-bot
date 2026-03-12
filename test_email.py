# test_email.py
from flask_mail import Mail, Message
from config import Config
from app import app

app.config.from_object(Config)
mail = Mail(app)

with app.app_context():
    try:
        msg = Message(
            subject='🧪 Test Email - Support Bot',
            recipients=[Config.ADMIN_EMAIL],
            body='Ceci est un test de configuration email. ✅',
            sender=Config.MAIL_DEFAULT_SENDER
        )
        mail.send(msg)
        print("✅ Email envoyé avec succès !")
    except Exception as e:
        print(f"❌ Erreur : {e}")