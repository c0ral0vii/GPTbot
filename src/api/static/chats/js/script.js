const API_URL = "/api/v1/dialogs/"

function get_messages() {
    // Получаем UUID диалога из URL
    const currentUrl = window.location.pathname;
    // Предполагаем, что URL имеет формат /chat/UUID/ или /chat/UUID
    const pathParts = currentUrl.split('/').filter(part => part !== '');
    
    // Ищем UUID диалога в URL (предположительно это последний элемент пути)
    let dialogUuid = pathParts[pathParts.length - 1];
    // Если последний элемент пустой (из-за конечного слеша), берем предпоследний
    if (!dialogUuid && pathParts.length > 1) {
        dialogUuid = pathParts[pathParts.length - 2];
    }
    
    if (!dialogUuid) {
        console.error('UUID диалога не найден в URL');
        return;
    }
    
    // Выполняем запрос к API для получения сообщений
    fetch(`${API_URL}chat/${dialogUuid}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка при получении сообщений');
            }
            return response.json();
        })
        .then(data => {
            // Очищаем текущие сообщения
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = '';
            
            const dialogNameElement = document.getElementById('dialog-name');
            if (dialogNameElement && data.title) {
                dialogNameElement.textContent = data.title;
            }
            
            const dialogDateElement = document.getElementById('dialog-date');
            if (dialogDateElement && data.created_at) {
                const dialogDate = new Date(data.created_at);
                dialogDateElement.textContent = dialogDate.toLocaleString();
            }
            
            if (data.messages && data.messages.length > 0) {
                data.messages.sort((a, b) => a.message_id - b.message_id);
                
                data.messages.forEach(msg => {
                    const isUser = msg.role === 'user';
                    const aiVersion = !isUser ? msg.role.toUpperCase() : null;
                    addMessage(msg.message, isUser, aiVersion);
                });
            } else {
                addMessage('Начните новый диалог', false, 'SYSTEM');
            }
        })
        .catch(error => {
            console.error('Ошибка при получении сообщений:', error);
            addMessage('Ошибка при загрузке сообщений', false, 'SYSTEM');
        });
}

function addMessage(message, isUser = false, aiVersion = null) {
    const messagesDiv = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Обрабатываем сообщение как Markdown только для сообщений от AI
    if (!isUser && message) {
        // Настройка marked для обработки Markdown
        marked.setOptions({
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(code, { language: lang }).value;
                    } catch (e) {
                        console.error('Error highlighting code:', e);
                    }
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true,         // Переносы строк как <br>
            gfm: true,            // GitHub Flavored Markdown
            headerIds: false,     // Без id для заголовков
            mangle: false,        // Без экранирования символов @ в email
            smartLists: true      // Улучшенные списки
        });
        
        // Обработка Markdown в сообщении
        messageContent.innerHTML = marked.parse(message);
        
        // Инициализация подсветки синтаксиса во всех блоках кода
        messageContent.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    } else {
        // Для сообщений пользователя просто используем текст
        messageContent.textContent = message;
    }
    
    const messageFooter = document.createElement('div');
    messageFooter.className = 'message-footer';
    
    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = new Date().toLocaleTimeString();
    
    messageFooter.appendChild(messageTime);
    
    if (!isUser) {
        const aiVersionSpan = document.createElement('span');
        aiVersionSpan.className = 'ai-version';
        aiVersionSpan.textContent = aiVersion || 'GPT-4';
        messageFooter.appendChild(aiVersionSpan);
        
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.textContent = 'Копировать';
        copyButton.onclick = () => copyToClipboard(message);
        messageFooter.appendChild(copyButton);
    }
    
    messageElement.appendChild(messageContent);
    messageElement.appendChild(messageFooter);
    messagesDiv.appendChild(messageElement);
    
    // Прокрутка к последнему сообщению
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Функция для копирования текста в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Можно добавить уведомление об успешном копировании
        alert('Текст скопирован в буфер обмена');
    }).catch(err => {
        console.error('Ошибка при копировании: ', err);
    });
}

// Загрузка сообщений при открытии страницы
document.addEventListener('DOMContentLoaded', () => {
    get_messages();
});
