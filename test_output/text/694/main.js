// State Management
const state = {
    theme: localStorage.getItem('theme') || 'dark',
    animationsEnabled: localStorage.getItem('animations') !== 'false',
    animationIntensity: localStorage.getItem('animationIntensity') || 'high',
    currentModel: 'GPT-4o',
    chats: JSON.parse(localStorage.getItem('chats')) || [],
    currentChatId: null,
    isGenerating: false
};

// DOM Elements
const elements = {
    body: document.body,
    sidebar: document.getElementById('sidebar'),
    sidebarOverlay: document.getElementById('sidebarOverlay'),
    hamburgerBtn: document.getElementById('hamburgerBtn'),
    newChatBtn: document.getElementById('newChatBtn'),
    searchInput: document.getElementById('searchInput'),
    chatList: document.getElementById('chatList'),
    chatContent: document.getElementById('chatContent'),
    emptyState: document.getElementById('emptyState'),
    messagesContainer: document.getElementById('messagesContainer'),
    messageInput: document.getElementById('messageInput'),
    inputContainer: document.getElementById('inputContainer'),
    sendBtn: document.getElementById('sendBtn'),
    modelSelector: document.getElementById('modelSelector'),
    themeToggle: document.getElementById('themeToggle'),
    fxToggle: document.getElementById('fxToggle'),
    settingsBtn: document.getElementById('settingsBtn'),
    settingsModal: document.getElementById('settingsModal'),
    modalClose: document.getElementById('modalClose'),
    toast: document.getElementById('toast')
};

// Initialize App
function init() {
    applyTheme(state.theme);
    applyAnimations(state.animationsEnabled);
    setupEventListeners();
    loadChatHistory();
    updateFxToggleState();
}

// Theme Management
function applyTheme(theme) {
    if (theme === 'system') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        theme = prefersDark ? 'dark' : 'light';
    }
    
    elements.body.classList.remove('dark-mode', 'light-mode');
    elements.body.classList.add(`${theme}-mode`);
    state.theme = theme;
    localStorage.setItem('theme', theme);
    
    updateThemeButtons();
}

function updateThemeButtons() {
    document.querySelectorAll('.theme-option').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === state.theme);
    });
}

// Animation Management
function applyAnimations(enabled) {
    elements.body.classList.toggle('animations-on', enabled);
    elements.body.classList.toggle('animations-off', !enabled);
    state.animationsEnabled = enabled;
    localStorage.setItem('animations', enabled);
}

function updateFxToggleState() {
    elements.fxToggle.classList.toggle('active', state.animationsEnabled);
}

// Event Listeners
function setupEventListeners() {
    // Hamburger menu
    elements.hamburgerBtn.addEventListener('click', toggleSidebar);
    elements.sidebarOverlay.addEventListener('click', closeSidebar);
    
    // New chat
    elements.newChatBtn.addEventListener('click', startNewChat);
    
    // Search
    elements.searchInput.addEventListener('input', handleSearch);
    
    // Message input
    elements.messageInput.addEventListener('input', autoResizeTextarea);
    elements.messageInput.addEventListener('focus', () => {
        elements.inputContainer.classList.add('glowing');
    });
    elements.messageInput.addEventListener('blur', () => {
        elements.inputContainer.classList.remove('glowing');
    });
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Send button
    elements.sendBtn.addEventListener('click', () => {
        if (state.isGenerating) {
            stopGeneration();
        } else {
            sendMessage();
        }
    });
    
    // Model selector
    elements.modelSelector.querySelector('.model-selector-btn').addEventListener('click', toggleModelDropdown);
    document.querySelectorAll('.model-option').forEach(option => {
        option.addEventListener('click', () => selectModel(option.dataset.model));
    });
    
    // Theme toggle
    elements.themeToggle.addEventListener('click', () => {
        const newTheme = state.theme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    });
    
    // FX toggle
    elements.fxToggle.addEventListener('click', () => {
        const newState = !state.animationsEnabled;
        applyAnimations(newState);
        updateFxToggleState();
        showToast(newState ? 'Animations Enabled' : 'Animations Disabled');
    });
    
    // Settings
    elements.settingsBtn.addEventListener('click', openSettings);
    elements.modalClose.addEventListener('click', closeSettings);
    elements.settingsModal.addEventListener('click', (e) => {
        if (e.target === elements.settingsModal) closeSettings();
    });
    
    // Theme options in settings
    document.querySelectorAll('.theme-option').forEach(btn => {
        btn.addEventListener('click', () => applyTheme(btn.dataset.theme));
    });
    
    // Animation options in settings
    document.querySelectorAll('.animation-option').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.animation-option').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const intensity = btn.dataset.intensity;
            state.animationIntensity = intensity;
            localStorage.setItem('animationIntensity', intensity);
            
            applyAnimations(intensity !== 'off');
            updateFxToggleState();
        });
    });
    
    // Suggested prompts
    document.querySelectorAll('.prompt-card').forEach(card => {
        card.addEventListener('click', () => {
            elements.messageInput.value = card.dataset.prompt;
            elements.messageInput.focus();
            autoResizeTextarea();
        });
    });
    
    // Chat actions
    document.addEventListener('click', handleChatActions);
    
    // Close dropdowns on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.model-selector')) {
            document.querySelector('.model-dropdown').classList.remove('active');
        }
        if (!e.target.closest('.chat-actions-btn') && !e.target.closest('.chat-actions-menu')) {
            document.querySelectorAll('.chat-actions-menu').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });
}

// Sidebar Functions
function toggleSidebar() {
    elements.sidebar.classList.toggle('active');
    elements.sidebarOverlay.classList.toggle('active');
}

function closeSidebar() {
    elements.sidebar.classList.remove('active');
    elements.sidebarOverlay.classList.remove('active');
}

// Chat Functions
function startNewChat() {
    state.currentChatId = null;
    elements.emptyState.classList.remove('hidden');
    elements.messagesContainer.innerHTML = '';
    elements.messagesContainer.classList.add('hidden');
    elements.messageInput.value = '';
    elements.messageInput.focus();
    
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });
    
    closeSidebar();
}

function loadChatHistory() {
    // Chat history is already rendered in HTML for demo
    // In production, this would load from localStorage/API
}

function handleSearch(e) {
    const query = e.target.value.toLowerCase();
    document.querySelectorAll('.chat-item').forEach(item => {
        const title = item.querySelector('.chat-title').textContent.toLowerCase();
        item.style.display = title.includes(query) ? 'flex' : 'none';
    });
}

function handleChatActions(e) {
    // Chat item click
    if (e.target.closest('.chat-item') && !e.target.closest('.chat-actions-btn') && !e.target.closest('.chat-actions-menu')) {
        const chatItem = e.target.closest('.chat-item');
        selectChat(chatItem.dataset.id);
    }
    
    // Actions button
    if (e.target.closest('.chat-actions-btn')) {
        e.stopPropagation();
        const menu = e.target.closest('.chat-item').querySelector('.chat-actions-menu');
        document.querySelectorAll('.chat-actions-menu').forEach(m => {
            if (m !== menu) m.classList.remove('active');
        });
        menu.classList.toggle('active');
    }
    
    // Delete action
    if (e.target.classList.contains('delete')) {
        const chatItem = e.target.closest('.chat-item');
        chatItem.remove();
        showToast('Chat deleted');
    }
    
    // Rename action
    if (e.target.classList.contains('rename')) {
        const chatItem = e.target.closest('.chat-item');
        const titleSpan = chatItem.querySelector('.chat-title');
        const newTitle = prompt('Enter new title:', titleSpan.textContent);
        if (newTitle) {
            titleSpan.textContent = newTitle;
            showToast('Chat renamed');
        }
        chatItem.querySelector('.chat-actions-menu').classList.remove('active');
    }
    
    // Archive action
    if (e.target.classList.contains('archive')) {
        const chatItem = e.target.closest('.chat-item');
        chatItem.remove();
        showToast('Chat archived');
    }
}

function selectChat(chatId) {
    state.currentChatId = chatId;
    
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.toggle('active', item.dataset.id === chatId);
    });
    
    // Load chat messages (demo data)
    elements.emptyState.classList.add('hidden');
    elements.messagesContainer.classList.remove('hidden');
    
    // Demo: show some messages
    elements.messagesContainer.innerHTML = `
        <div class="message user">
            <div class="message-content">
                <div class="message-text">Can you help me plan a marketing strategy for our new product launch?</div>
            </div>
        </div>
        <div class="message ai">
            <div class="message-avatar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
            </div>
            <div class="message-content">
                <div class="message-text">
                    <p>I'd be happy to help you plan a marketing strategy for your product launch! Here's a comprehensive approach:</p>
                    <p><strong>1. Define Your Target Audience</strong></p>
                    <p>First, we need to clearly identify who your ideal customers are. Consider demographics, psychographics, and behavioral patterns.</p>
                    <p><strong>2. Set Clear Goals</strong></p>
                    <p>What does success look like? Define measurable KPIs like:</p>
                    <ul>
                        <li>Brand awareness metrics</li>
                        <li>Lead generation targets</li>
                        <li>Sales conversion rates</li>
                    </ul>
                </div>
                <div class="message-actions">
                    <button class="action-btn" title="Copy">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                    </button>
                    <button class="action-btn" title="Regenerate">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="23 4 23 10 17 10"></polyline>
                            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                        </svg>
                    </button>
                    <button class="action-btn" title="Good response">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                        </svg>
                    </button>
                    <button class="action-btn" title="Bad response">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    closeSidebar();
}

// Message Functions
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || state.isGenerating) return;
    
    // Create new chat if needed
    if (!state.currentChatId) {
        state.currentChatId = Date.now().toString();
        addChatToSidebar(message);
    }
    
    // Hide empty state
    elements.emptyState.classList.add('hidden');
    elements.messagesContainer.classList.remove('hidden');
    
    // Add user message
    addMessage(message, 'user');
    
    // Clear input
    elements.messageInput.value = '';
    autoResizeTextarea();
    
    // Start generation
    state.isGenerating = true;
    elements.sendBtn.classList.add('generating');
    
    // Show thinking indicator
    const thinkingEl = addThinkingIndicator();
    
    // Simulate AI response
    await simulateResponse(thinkingEl);
}

function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">${escapeHtml(content)}</div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
            </div>
            <div class="message-content">
                <div class="message-text">${content}</div>
                <div class="message-actions">
                    <button class="action-btn" title="Copy" onclick="copyMessage(this)">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                    </button>
                    <button class="action-btn" title="Regenerate">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="23 4 23 10 17 10"></polyline>
                            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                        </svg>
                    </button>
                    <button class="action-btn" title="Good response">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                        </svg>
                    </button>
                    <button class="action-btn" title="Bad response">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }
    
    elements.messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function addThinkingIndicator() {
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message ai';
    thinkingDiv.innerHTML = `
        <div class="message-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
        </div>
        <div class="thinking-indicator">
            <div class="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    elements.messagesContainer.appendChild(thinkingDiv);
    scrollToBottom();
    return thinkingDiv;
}

async function simulateResponse(thinkingEl) {
    const responses = [
        "That's a great question! Let me break this down for you.",
        "I understand what you're looking for. Here's my analysis:",
        "Based on your request, I've put together a comprehensive response.",
        "Excellent topic! Here are my thoughts on this matter."
    ];
    
    const fullResponse = `<p>${responses[Math.floor(Math.random() * responses.length)]}</p>
<p>First, let's consider the key factors involved. This is an important aspect that many people overlook when approaching this type of problem.</p>
<p>Here's a code example that might help:</p>
<div class="code-block">
    <div class="code-header">
        <span>javascript</span>
        <button class="copy-code-btn" onclick="copyCode(this)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            Copy
        </button>
    </div>
    <pre><code>function solution(input) {
  const result = input.map(item => {
    return processItem(item);
  });
  return result;
}</code></pre>
</div>
<p>This approach ensures that you get the best possible outcome while maintaining clean, readable code.</p>
<p>Is there anything specific you'd like me to elaborate on?</p>`;
    
    // Simulate typing delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    if (!state.isGenerating) return;
    
    // Remove thinking indicator
    thinkingEl.remove();
    
    // Add AI message with typewriter effect
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
        </div>
        <div class="message-content">
            <div class="message-text"></div>
        </div>
    `;
    elements.messagesContainer.appendChild(messageDiv);
    
    const textContainer = messageDiv.querySelector('.message-text');
    
    // Typewriter effect
    if (state.animationsEnabled) {
        await typewriterEffect(textContainer, fullResponse);
    } else {
        textContainer.innerHTML = fullResponse;
    }
    
    // Add action buttons
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'message-actions';
    actionsDiv.innerHTML = `
        <button class="action-btn" title="Copy" onclick="copyMessage(this)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
        </button>
        <button class="action-btn" title="Regenerate">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
        </button>
        <button class="action-btn" title="Good response">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
            </svg>
        </button>
        <button class="action-btn" title="Bad response">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
            </svg>
        </button>
    `;
    messageDiv.querySelector('.message-content').appendChild(actionsDiv);
    
    state.isGenerating = false;
    elements.sendBtn.classList.remove('generating');
    scrollToBottom();
}

async function typewriterEffect(element, html) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    const chunks = html.split(/(<[^>]+>)/);
    let currentHtml = '';
    
    for (const chunk of chunks) {
        if (!state.isGenerating) break;
        
        if (chunk.startsWith('<')) {
            currentHtml += chunk;
            element.innerHTML = currentHtml;
        } else {
            for (const char of chunk) {
                if (!state.isGenerating) break;
                currentHtml += char;
                element.innerHTML = currentHtml;
                scrollToBottom();
                await new Promise(resolve => setTimeout(resolve, 10));
            }
        }
    }
}

function stopGeneration() {
    state.isGenerating = false;
    elements.sendBtn.classList.remove('generating');
    showToast('Generation stopped');
}

function addChatToSidebar(message) {
    const title = message.substring(0, 30) + (message.length > 30 ? '...' : '');
    const todayGroup = document.querySelector('.chat-group');
    
    const chatItem = document.createElement('div');
    chatItem.className = 'chat-item active';
    chatItem.dataset.id = state.currentChatId;
    chatItem.innerHTML = `
        <span class="chat-title">${escapeHtml(title)}</span>
        <span class="chat-time">Just now</span>
        <button class="chat-actions-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="5" r="2"></circle>
                <circle cx="12" cy="12" r="2"></circle>
                <circle cx="12" cy="19" r="2"></circle>
            </svg>
        </button>
        <div class="chat-actions-menu">
            <button class="action-item rename">Rename</button>
            <button class="action-item archive">Archive</button>
            <button class="action-item delete">Delete</button>
        </div>
    `;
    
    // Remove active from other items
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Insert after the group title
    const groupTitle = todayGroup.querySelector('.chat-group-title');
    groupTitle.insertAdjacentElement('afterend', chatItem);
}

// Model Selector
function toggleModelDropdown() {
    document.querySelector('.model-dropdown').classList.toggle('active');
}

function selectModel(model) {
    state.currentModel = model;
    document.querySelector('.model-name').textContent = model;
    document.querySelectorAll('.model-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.model === model);
    });
    document.querySelector('.model-dropdown').classList.remove('active');
    showToast(`Switched to ${model}`);
}

// Settings Modal
function openSettings() {
    elements.settingsModal.classList.add('active');
}

function closeSettings() {
    elements.settingsModal.classList.remove('active');
}

// Utility Functions
function autoResizeTextarea() {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 200) + 'px';
}

function scrollToBottom() {
    elements.chatContent.scrollTop = elements.chatContent.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message) {
    elements.toast.textContent = message;
    elements.toast.classList.add('active');
    setTimeout(() => {
        elements.toast.classList.remove('active');
    }, 3000);
}

// Global functions for onclick handlers
function copyMessage(btn) {
    const messageText = btn.closest('.message-content').querySelector('.message-text').textContent;
    navigator.clipboard.writeText(messageText).then(() => {
        showToast('Copied to clipboard');
    });
}

function copyCode(btn) {
    const code = btn.closest('.code-block').querySelector('code').textContent;
    navigator.clipboard.writeText(code).then(() => {
        showToast('Code copied to clipboard');
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', init);