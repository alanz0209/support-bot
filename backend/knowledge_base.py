# Réponses pré-définies pour les questions fréquentes
FAQ = {
    "mot de passe": "Pour réinitialiser votre mot de passe : 1) Allez dans Paramètres 2) Cliquez sur 'Mot de passe oublié' 3) Suivez le lien envoyé par email",
    "facturation": "Vos factures sont disponibles dans : Compte → Facturation → Historique. Format PDF téléchargeable.",
    "horaires": "Notre support est disponible du lundi au vendredi, 9h-18h (heure de l'Est).",
    "remboursement": "Nous offrons un remboursement sous 14 jours. Contactez billing@company.com avec votre numéro de commande."
}

def get_faq_response(message):
    message_lower = message.lower()
    for key, answer in FAQ.items():
        if key in message_lower:
            return answer
    return None