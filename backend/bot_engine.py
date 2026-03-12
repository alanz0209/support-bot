# backend/bot_engine.py
import ollama
from backend.knowledge_base import get_faq_response

class SupportBot:
    def __init__(self):
        self.model = "llama3.2"
        self.system_prompt = """Tu es un assistant support client EXPERT en informatique.
Règles :
- Réponds TOUJOURS dans la langue de l'utilisateur
- Sois concis (max 3-4 phrases)
- Utilise des exemples concrets
- Reste poli et professionnel
- Pour les problèmes complexes, propose : support@company.com"""
        print(f"✅ Bot Ollama prêt : {self.model}")
    
    def get_response(self, message, file_url=None):
        # 1. Vérifier FAQ d'abord
        faq_result = get_faq_response(message)
        if faq_result["found"]:
            return {
                "reply": faq_result["response"],
                "source": "FAQ"
            }
        
        # 2. Sinon utiliser Ollama
        try:
            context = ""
            if file_url:
                context = f"[Fichier joint : {file_url}] "
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"{context}{message}"}
                ],
                options={"temperature": 0.7, "num_predict": 200}
            )
            
            return {
                "reply": response["message"]["content"].strip(),
                "source": "bot"
            }
            
        except Exception as e:
            print(f"❌ Erreur Ollama : {e}")
            return {
                "reply": "Désolé, problème technique. Contactez support@company.com",
                "source": "error"
            }