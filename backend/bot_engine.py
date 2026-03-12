from backend.knowledge_base import get_faq_response
import ollama

class SupportBot:
    def __init__(self):
        self.model = "llama3.2"  # Doit correspondre au modèle téléchargé
        self.system_prompt = """Tu es un assistant support client EXPERT en informatique.
            Règles :
            - Réponds TOUJOURS dans la langue de l'utilisateur
            - Sois concis (max 3-4 phrases)
            - Utilise des exemples concrets quand c'est pertinent
            - Si la question est technique, donne un exemple de code
            - Reste toujours poli et professionnel
            - Pour les problèmes complexes, propose un contact humain : support@company.com"""
        print(f"✅ Bot Ollama prêt avec le modèle : {self.model}")
    
    def get_response(self, message):
        # D'abord vérifier la FAQ
        faq_answer = get_faq_response(message)
        if faq_answer:
            return faq_answer
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message}
                ],
                options={
                    "temperature": 0.7,      # Créativité modérée
                    "num_predict": 150       # Limite la longueur de réponse
                }
            )
            return response["message"]["content"].strip()
            
        except Exception as e:
            print(f"❌ Erreur Ollama : {type(e).__name__} - {e}")
            return "Désolé, un problème technique est survenu. Veuillez contacter support@company.com"