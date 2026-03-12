// frontend/static/js/chat.js
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const fileInput = document.getElementById('fileInput');
    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileName = document.getElementById('fileName');
    
    let selectedFile = null;
    let socket = null;

    // === WEBSOCKET: Initialisation ===
    function initWebSocket() {
        socket = io();
        
        socket.on('connect', () => {
            console.log('🔌 Connecté au serveur temps réel');
        });
        
        socket.on('disconnect', () => {
            console.log('🔌 Déconnecté du serveur temps réel');
        });
        
        socket.on('urgent_ticket', (data) => {
            console.log('🔴 Ticket urgent:', data);
            showBrowserNotification('🔴 Ticket Urgent', `#${data.id}: ${data.message}`);
            playAlertSound();
            if (window.location.pathname.startsWith('/admin')) {
                flashDashboardRow(data.id, 'urgent');
            }
            if (chatMessages) {
                showSystemNotification(`🔴 Nouveau ticket urgent #${data.id}`);
            }
        });
        
        socket.on('ticket_updated', (data) => {
            console.log('📋 Ticket mis à jour:', data);
            if (window.location.pathname.startsWith('/admin')) {
                flashDashboardRow(data.id, 'updated');
            }
        });
        
        socket.on('connected', (data) => {
            console.log('✅', data.message);
        });
    }

    // === NOTIFICATIONS: Navigateur ===
    function showBrowserNotification(title, body) {
        if ('Notification' in window) {
            if (Notification.permission === 'granted') {
                new Notification(title, {
                    body: body,
                    icon: '/static/images/bot-icon.png',
                    tag: 'support-bot-alert'
                });
            } else if (Notification.permission === 'default') {
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        new Notification(title, { body, tag: 'support-bot-alert' });
                    }
                });
            }
        }
    }

    // === NOTIFICATIONS: Son d'alerte ===
    function playAlertSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.2);
            
            setTimeout(() => {
                const osc2 = audioContext.createOscillator();
                const gain2 = audioContext.createGain();
                osc2.connect(gain2);
                gain2.connect(audioContext.destination);
                osc2.frequency.value = 1000;
                gain2.gain.value = 0.3;
                osc2.start();
                osc2.stop(audioContext.currentTime + 0.2);
            }, 250);
        } catch (e) {
            console.log('🔇 Son désactivé:', e);
        }
    }

    // === NOTIFICATIONS: Flash dashboard ===
    function flashDashboardRow(ticketId, type) {
        const row = document.querySelector(`tr[data-ticket-id="${ticketId}"]`);
        if (row) {
            const color = type === 'urgent' ? '#fee2e2' : '#dbeafe';
            row.style.transition = 'background-color 0.3s';
            row.style.backgroundColor = color;
            
            let flashes = 0;
            const flashInterval = setInterval(() => {
                row.style.backgroundColor = flashes % 2 === 0 ? color : 'transparent';
                flashes++;
                if (flashes >= 6) {
                    clearInterval(flashInterval);
                    row.style.backgroundColor = 'transparent';
                }
            }, 200);
        }
    }

    // === NOTIFICATIONS: Message système ===
    function showSystemNotification(text) {
        const div = document.createElement('div');
        div.className = 'message bot system-notification';
        div.style.borderLeft = '4px solid #ef4444';
        div.style.background = '#fef2f2';
        div.innerHTML = `<strong>🔔 Système</strong><div>${text}</div>`;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        setTimeout(() => {
            div.style.opacity = '0';
            div.style.transition = 'opacity 0.5s';
            setTimeout(() => div.remove(), 500);
        }, 10000);
    }

    // === FICHIERS: Gestion upload ===
    fileInput?.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            fileName.textContent = `📎 ${selectedFile.name}`;
            fileUploadArea.style.display = 'flex';
        }
    });

    window.removeFile = function() {
        selectedFile = null;
        fileInput.value = '';
        fileUploadArea.style.display = 'none';
    };

    // === CHAT: Envoyer message ===
    window.sendMessage = async function() {
        const message = userInput.value.trim();
        if (!message && !selectedFile) return;

        let displayMessage = message;
        if (selectedFile) {
            displayMessage += message ? `\n📎 Fichier : ${selectedFile.name}` : `📎 Fichier : ${selectedFile.name}`;
        }
        addMessage(displayMessage, 'user');
        
        userInput.value = '';
        const fileToSend = selectedFile;
        removeFile();

        const typingDiv = showTypingIndicator();

        try {
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
            
            if (data.source !== 'FAQ') {
                addFeedbackButtons(chatMessages.lastElementChild);
            }
            
        } catch (error) {
            console.error('Erreur:', error);
            typingDiv.remove();
            addMessage('❌ Erreur de connexion. Veuillez réessayer.', 'bot');
        }
    };

    // === CHAT: Ajouter message ===
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

    // === CHAT: Indicateur de frappe ===
    function showTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'typing-indicator';
        div.id = 'typingIndicator';
        div.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return div;
    }

    // === CHAT: Boutons de feedback ===
    function addFeedbackButtons(messageDiv) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback';
        feedbackDiv.innerHTML = `
            <button onclick="sendFeedback(true, this)">👍 Utile</button>
            <button onclick="sendFeedback(false, this)">👎 Pas utile</button>
        `;
        messageDiv.appendChild(feedbackDiv);
    }

    // === FEEDBACK: Envoyer ===
    window.sendFeedback = async function(isPositive, button) {
        const feedbackDiv = button.parentElement;
        feedbackDiv.innerHTML = isPositive ? '✅ Merci pour votre feedback !' : '❌ Merci, nous améliorerons cette réponse';
        
        await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ positive: isPositive })
        });
    };

    // === KEYBOARD: Touche Entrée ===
    userInput?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // === INITIALISATION ===
    if ('Notification' in window && Notification.permission === 'default') {
        document.body.addEventListener('click', function requestNotifPermission() {
            Notification.requestPermission();
            document.body.removeEventListener('click', requestNotifPermission);
        }, { once: true });
    }
    
    // Initialiser WebSocket si sur une page admin
    if (typeof io !== 'undefined' && 
        (window.location.pathname.startsWith('/admin'))) {
        initWebSocket();
    }
    
    userInput?.focus();
});