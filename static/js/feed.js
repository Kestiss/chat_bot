const chatFeed = document.getElementById('chat-feed');

async function refreshChat() {
    if (!chatFeed) {
        return;
    }
    try {
        const response = await fetch('/logs', { cache: 'no-store' });
        if (!response.ok) {
            return;
        }
        const data = await response.json();
        if (!Array.isArray(data.lines)) {
            return;
        }
        chatFeed.innerHTML = '';
        if (data.lines.length === 0) {
            const placeholder = document.createElement('div');
            placeholder.classList.add('chat-feed__placeholder');
            placeholder.textContent = 'Waiting for chat output...';
            chatFeed.appendChild(placeholder);
        } else {
            for (const line of data.lines) {
                const row = document.createElement('div');
                row.textContent = line;
                chatFeed.appendChild(row);
            }
            chatFeed.scrollTop = chatFeed.scrollHeight;
        }
    } catch (error) {
        // Ignore intermittent network issues; the next poll will retry.
    }
}

if (chatFeed) {
    refreshChat();
    setInterval(refreshChat, 3000);
}
