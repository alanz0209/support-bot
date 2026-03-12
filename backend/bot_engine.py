# backend/bot_engine.py
import ollama
import os
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
    
    def detect_urgency(self, message):
        """Détecte si un message est urgent via IA + mots-clés"""
        # Mots-clés urgents
        urgent_keywords = [
            'urgent', 'critique', 'bloqué', 'emergency', 'panne', 'down',
            'ne fonctionne plus', 'erreur critique', 'perte de données',
            'sécurité', 'piraté', 'vol', 'fraude', 'impossible de',
            'bloquant', 'production', 'clients impactés', 'serveur',
            'accès', 'connexion', 'mot de passe'
        ]
        
        # Détection par mots-clés
        if any(kw in message.lower() for kw in urgent_keywords):
            return True
        
        # Détection par IA (Ollama)
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": """Tu es un classificateur de tickets support.
                    Analyse ce message et réponds UNIQUEMENT par 'urgent' ou 'normal'.
                    Un message est 'urgent' si :
                    - L'utilisateur ne peut plus travailler
                    - Il y a une panne/erreur critique
                    - Problème de sécurité/paiement
                    - Clients impactés
                    Sinon réponds 'normal'."""},
                    {"role": "user", "content": message}
                ],
                options={"temperature": 0.3, "num_predict": 10}
            )
            return 'urgent' in response['message']['content'].lower()
        except Exception as e:
            print(f"⚠️ Erreur détection IA : {e}")
            return False  # En cas d'erreur, on retourne à la méthode mots-clés
    
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