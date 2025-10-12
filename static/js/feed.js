const chatFeed = document.getElementById('chat-feed');
const topicRefreshButton = document.getElementById('topic-refresh');
const topicInput = document.getElementById('topic');
const defaultTopicPlaceholder = topicInput ? topicInput.getAttribute('placeholder') || '' : '';

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
        const previousScrollTop = chatFeed.scrollTop;
        const previousScrollHeight = chatFeed.scrollHeight;
        const isPinnedToBottom =
            Math.abs(previousScrollHeight - chatFeed.clientHeight - previousScrollTop) < 6;
        const fragment = document.createDocumentFragment();
        if (data.lines.length === 0) {
            const placeholder = document.createElement('div');
            placeholder.classList.add('chat-feed__placeholder');
            placeholder.textContent = 'Waiting for chat output...';
            fragment.appendChild(placeholder);
        } else {
            for (const line of data.lines) {
                const row = document.createElement('div');
                row.textContent = line;
                fragment.appendChild(row);
            }
        }
        chatFeed.replaceChildren(fragment);
        if (isPinnedToBottom) {
            chatFeed.scrollTop = chatFeed.scrollHeight;
        } else {
            const heightDelta = chatFeed.scrollHeight - previousScrollHeight;
            chatFeed.scrollTop = Math.max(0, previousScrollTop + heightDelta);
        }
    } catch (error) {
        // Ignore intermittent network issues; the next poll will retry.
    }
}

if (chatFeed) {
    refreshChat();
    setInterval(refreshChat, 3000);
}

async function populateRandomTopic() {
    if (!topicInput || !topicRefreshButton) {
        return;
    }
    const previousValue = topicInput.value;
    topicInput.disabled = true;
    topicRefreshButton.disabled = true;
    try {
        const response = await fetch('/topics', { cache: 'no-store' });
        let data = null;
        try {
            data = await response.json();
        } catch (parseError) {
            data = null;
        }
        if (!response.ok) {
            const errorMessage =
                data && typeof data.error === 'string' ? data.error : 'Unable to generate topic';
            if (!previousValue) {
                topicInput.placeholder = errorMessage;
            }
            return;
        }
        if (data && typeof data.topic === 'string') {
            const candidate = data.topic.trim();
            if (candidate) {
                topicInput.value = candidate;
                topicInput.placeholder = defaultTopicPlaceholder;
            }
        }
    } catch (error) {
        if (!previousValue) {
            topicInput.placeholder = 'Unable to generate topic';
        }
    } finally {
        topicInput.disabled = false;
        topicRefreshButton.disabled = false;
        topicInput.focus();
    }
}

if (topicRefreshButton) {
    topicRefreshButton.addEventListener('click', () => {
        populateRandomTopic();
    });
}
