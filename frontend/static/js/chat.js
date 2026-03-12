// Attendre que le DOM soit complètement chargé
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.querySelector('button');

    // Vérifier que les éléments existent
    if (!userInput) {
        console.error("❌ Erreur: L'élément 'userInput' n'existe pas dans le HTML");
        return;
    }
    
    if (!chatMessages) {
        console.error("❌ Erreur: L'élément 'chatMessages' n'existe pas dans le HTML");
        return;
    }

    // Fonction pour envoyer un message
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Ajouter le message de l'utilisateur
        addMessage(message, 'user');
        userInput.value = '';

        // Afficher un indicateur de chargement
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot';
        loadingDiv.id = 'loading-msg';
        loadingDiv.innerHTML = '<em>Bot est en train d\'écrire...</em>';
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            // Supprimer le message de chargement
            const loadingMsg = document.getElementById('loading-msg');
            if (loadingMsg) {
                loadingMsg.remove();
            }
            
            // Ajouter la réponse du bot
            addMessage(data.reply, 'bot');
        } catch (error) {
            console.error('Erreur:', error);
            const loadingMsg = document.getElementById('loading-msg');
            if (loadingMsg) {
                loadingMsg.remove();
            }
            addMessage('❌ Erreur de connexion au serveur', 'bot');
        }
    }

    // Fonction pour ajouter un message à l'écran
    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        const strong = document.createElement('strong');
        strong.textContent = sender === 'user' ? 'Vous: ' : 'Bot: ';
        const textNode = document.createTextNode(text);
        div.appendChild(strong);
        div.appendChild(textNode);
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Ajouter l'événement clic sur le bouton
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }

    // Ajouter l'événement touche Entrée
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Focus sur le champ de saisie au chargement
    userInput.focus();
});