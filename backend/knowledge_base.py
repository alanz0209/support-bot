# Base de connaissances pour les questions fréquentes
FAQ = {
    "mot de passe": {
        "question": "Comment réinitialiser mon mot de passe ?",
        "reponse": "Pour réinitialiser votre mot de passe :\n1. Allez dans Paramètres → Sécurité\n2. Cliquez sur 'Mot de passe oublié'\n3. Suivez le lien envoyé par email\n4. Créez un nouveau mot de passe sécurisé"
    },
    "facturation": {
        "question": "Où trouver mes factures ?",
        "reponse": "Vos factures sont disponibles dans : Compte → Facturation → Historique. Vous pouvez les télécharger en PDF."
    },
    "horaires": {
        "question": "Quels sont vos horaires de support ?",
        "reponse": "Notre support est disponible :\n📅 Lundi - Vendredi : 9h - 18h (EST)\n📅 Samedi : 10h - 14h (EST)\n📅 Dimanche : Fermé\n🚨 Urgences : support@company.com (24/7)"
    },
    "remboursement": {
        "question": "Politique de remboursement",
        "reponse": "Nous offrons un remboursement complet sous 14 jours après l'achat. Contactez billing@company.com avec votre numéro de commande."
    },
    "installation": {
        "question": "Comment installer votre logiciel ?",
        "reponse": "1. Téléchargez l'installateur depuis votre espace client\n2. Exécutez le fichier .exe (Windows) ou .dmg (Mac)\n3. Suivez les instructions à l'écran\n4. Connectez-vous avec vos identifiants"
    },
    "compatibilite": {
        "question": "Compatibilité système",
        "reponse": "Notre logiciel est compatible avec :\n💻 Windows 10/11 (64-bit)\n🍎 macOS 12+ (Monterey ou supérieur)\n🐧 Ubuntu 20.04+ (version Linux)"
    },
    "compte": {
        "question": "Gestion de compte",
        "reponse": "Pour gérer votre compte : Connectez-vous → Cliquez sur votre avatar → Paramètres du compte. Vous pouvez modifier email, mot de passe, et préférences."
    },
    "api": {
        "question": "Accès à l'API",
        "reponse": "L'API est disponible pour les plans Pro et Enterprise. Générez votre clé API dans : Paramètres → Développeurs → Clés API. Documentation : docs.company.com/api"
    }
}

def get_faq_response(message):
    """Recherche une correspondance dans la FAQ"""
    message_lower = message.lower()
    
    for key, faq_item in FAQ.items():
        if key in message_lower:
            return {
                "found": True,
                "question": faq_item["question"],
                "response": faq_item["reponse"],
                "source": "FAQ"
            }
    
    return {"found": False}

def get_all_faqs():
    """Retourne toute la FAQ pour le dashboard"""
    return FAQ