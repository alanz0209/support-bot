document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const fileInput = document.getElementById('fileInput');
    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileName = document.getElementById('fileName');
    
    let selectedFile = null;

    // Gestion sélection de fichier
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            fileName.textContent = `📎 ${selectedFile.name}`;
            fileUploadArea.style.display = 'flex';
        }
    });

    // Supprimer fichier
    window.removeFile = function() {
        selectedFile = null;
        fileInput.value = '';
        fileUploadArea.style.display = 'none';
    };

    // Envoyer message
    window.sendMessage = async function() {
        const message = userInput.value.trim();
        if (!message && !selectedFile) return;

        // Message utilisateur
        let displayMessage = message;
        if (selectedFile) {
            displayMessage += message ? `\n📎 Fichier : ${selectedFile.name}` : `📎 Fichier : ${selectedFile.name}`;
        }
        addMessage(displayMessage, 'user');
        
        userInput.value = '';
        const fileToSend = selectedFile;
        removeFile();

        // Indicateur de frappe
        const typingDiv = showTypingIndicator();

        try {
            // Upload fichier si présent
            let fileUrl = null;
            if (fileToSend) {
                const formData = new FormData();
                formData.append('file', fileToSend);
                
                const uploadResponse = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const uploadData = await uploadResponse.json();
                if (uploadData.success) {
                    fileUrl = uploadData.url;
                }
            }

            // Appel API chat
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message,
                    file_url: fileUrl
                })
            });
            
            const data = await response.json();
            typingDiv.remove();
            addMessage(data.reply, 'bot', data.source);
            
            // Feedback buttons
            if (data.source !== 'FAQ') {
                addFeedbackButtons(chatMessages.lastElementChild);
            }
            
        } catch (error) {
            console.error('Erreur:', error);
            typingDiv.remove();
            addMessage('❌ Erreur de connexion. Veuillez réessayer.', 'bot');
        }
    };

    // Ajouter message à l'écran
    function addMessage(text, sender, source = null) {
        const div = document.createElement('div');
        div.className = `message ${sender}${source === 'FAQ' ? ' faq' : ''}`;
        
        const strong = document.createElement('strong');
        strong.textContent = sender === 'user' ? 'Vous' : '🤖 Bot';
        if (source === 'FAQ') {
            strong.textContent += ' (Réponse rapide)';
        }
        
        const textNode = document.createElement('div');
        textNode.textContent = text;
        
        div.appendChild(strong);
        div.appendChild(textNode);
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return div;
    }

    // Indicateur de frappe
    function showTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'typing-indicator';
        div.id = 'typingIndicator';
        div.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return div;
    }

    // Boutons de feedback
    function addFeedbackButtons(messageDiv) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback';
        feedbackDiv.innerHTML = `
            <button onclick="sendFeedback(true, this)">👍 Utile</button>
            <button onclick="sendFeedback(false, this)">👎 Pas utile</button>
        `;
        messageDiv.appendChild(feedbackDiv);
    }

    // Envoyer feedback
    window.sendFeedback = async function(isPositive, button) {
        const feedbackDiv = button.parentElement;
        feedbackDiv.innerHTML = isPositive ? '✅ Merci pour votre feedback !' : '❌ Merci, nous améliorerons cette réponse';
        
        await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ positive: isPositive })
        });
    };

    // Touche Entrée
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    userInput.focus();
});