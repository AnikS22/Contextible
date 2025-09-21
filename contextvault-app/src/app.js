// Import Tauri API
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';

// App state
let appState = {
    serverRunning: false,
    ollamaRunning: false,
    contextEntries: [],
    currentSection: 'dashboard'
};

// DOM elements
const elements = {
    statusDot: document.getElementById('statusDot'),
    statusText: document.getElementById('statusText'),
    serverStatus: document.getElementById('serverStatus'),
    ollamaStatus: document.getElementById('ollamaStatus'),
    contextCount: document.getElementById('contextCount'),
    startServerBtn: document.getElementById('startServerBtn'),
    stopServerBtn: document.getElementById('stopServerBtn'),
    refreshStatusBtn: document.getElementById('refreshStatusBtn'),
    addContextBtn: document.getElementById('addContextBtn'),
    contextList: document.getElementById('contextList'),
    knowledgeSummary: document.getElementById('knowledgeSummary'),
    activityList: document.getElementById('activityList'),
    addContextModal: document.getElementById('addContextModal'),
    closeModalBtn: document.getElementById('closeModalBtn'),
    cancelAddBtn: document.getElementById('cancelAddBtn'),
    saveContextBtn: document.getElementById('saveContextBtn'),
    contextContent: document.getElementById('contextContent'),
    contextType: document.getElementById('contextType'),
    contextTags: document.getElementById('contextTags')
};

// Navigation
const navItems = document.querySelectorAll('.nav-item');
const sections = document.querySelectorAll('.section');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    startStatusUpdates();
});

async function initializeApp() {
    try {
        // Check initial status
        await updateServerStatus();
        await updateOllamaStatus();
        await loadContextEntries();
        await loadKnowledgeSummary();
        
        console.log('App initialized successfully');
    } catch (error) {
        console.error('Failed to initialize app:', error);
        showNotification('Failed to initialize app', 'error');
    }
}

function setupEventListeners() {
    // Navigation
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const section = item.dataset.section;
            switchSection(section);
        });
    });

    // Server controls
    elements.startServerBtn.addEventListener('click', startServer);
    elements.stopServerBtn.addEventListener('click', stopServer);
    elements.refreshStatusBtn.addEventListener('click', refreshStatus);

    // Context management
    elements.addContextBtn.addEventListener('click', showAddContextModal);
    elements.closeModalBtn.addEventListener('click', hideAddContextModal);
    elements.cancelAddBtn.addEventListener('click', hideAddContextModal);
    elements.saveContextBtn.addEventListener('click', saveContextEntry);

    // Modal backdrop click
    elements.addContextModal.addEventListener('click', (e) => {
        if (e.target === elements.addContextModal) {
            hideAddContextModal();
        }
    });

    // Listen for Tauri events
    listen('server-started', () => {
        updateServerStatus();
        showNotification('ContextVault server started successfully', 'success');
    });

    listen('server-error', (event) => {
        showNotification(`Server error: ${event.payload}`, 'error');
    });
}

async function startServer() {
    try {
        elements.startServerBtn.disabled = true;
        elements.startServerBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        
        const status = await invoke('start_contextvault_server');
        appState.serverRunning = status.running;
        updateStatusDisplay();
        
        if (status.running) {
            showNotification('Server started successfully', 'success');
        } else {
            showNotification('Failed to start server', 'error');
        }
    } catch (error) {
        console.error('Failed to start server:', error);
        showNotification(`Failed to start server: ${error}`, 'error');
    } finally {
        elements.startServerBtn.disabled = false;
        elements.startServerBtn.innerHTML = '<i class="fas fa-play"></i> Start Server';
    }
}

async function stopServer() {
    try {
        elements.stopServerBtn.disabled = true;
        elements.stopServerBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Stopping...';
        
        const status = await invoke('stop_contextvault_server');
        appState.serverRunning = status.running;
        updateStatusDisplay();
        
        showNotification('Server stopped', 'info');
    } catch (error) {
        console.error('Failed to stop server:', error);
        showNotification(`Failed to stop server: ${error}`, 'error');
    } finally {
        elements.stopServerBtn.disabled = false;
        elements.stopServerBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Server';
    }
}

async function refreshStatus() {
    try {
        elements.refreshStatusBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        
        await updateServerStatus();
        await updateOllamaStatus();
        await loadContextEntries();
        
        showNotification('Status refreshed', 'success');
    } catch (error) {
        console.error('Failed to refresh status:', error);
        showNotification('Failed to refresh status', 'error');
    } finally {
        elements.refreshStatusBtn.innerHTML = '<i class="fas fa-sync"></i> Refresh Status';
    }
}

async function updateServerStatus() {
    try {
        const status = await invoke('get_server_status');
        appState.serverRunning = status.running;
        updateStatusDisplay();
        
        elements.serverStatus.textContent = status.running ? 'Running' : 'Stopped';
        elements.serverStatus.className = status.running ? 'value text-success' : 'value text-error';
    } catch (error) {
        console.error('Failed to get server status:', error);
        elements.serverStatus.textContent = 'Error';
        elements.serverStatus.className = 'value text-error';
    }
}

async function updateOllamaStatus() {
    try {
        const ollamaRunning = await invoke('check_ollama_status');
        appState.ollamaRunning = ollamaRunning;
        
        elements.ollamaStatus.textContent = ollamaRunning ? 'Connected' : 'Not Connected';
        elements.ollamaStatus.className = ollamaRunning ? 'value text-success' : 'value text-warning';
    } catch (error) {
        console.error('Failed to check Ollama status:', error);
        elements.ollamaStatus.textContent = 'Error';
        elements.ollamaStatus.className = 'value text-error';
    }
}

async function loadContextEntries() {
    try {
        elements.contextList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><span>Loading context entries...</span></div>';
        
        const entries = await invoke('get_context_entries');
        appState.contextEntries = entries;
        
        elements.contextCount.textContent = entries.length;
        
        if (entries.length === 0) {
            elements.contextList.innerHTML = `
                <div class="text-center" style="padding: 2rem; color: #64748b;">
                    <i class="fas fa-database" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <p>No context entries yet. Add your first entry to get started!</p>
                </div>
            `;
            return;
        }
        
        elements.contextList.innerHTML = entries.map(entry => createContextItemHTML(entry)).join('');
        
        // Add delete event listeners
        document.querySelectorAll('.delete-context-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const entryId = e.target.closest('.context-item').dataset.entryId;
                deleteContextEntry(entryId);
            });
        });
        
    } catch (error) {
        console.error('Failed to load context entries:', error);
        elements.contextList.innerHTML = `
            <div class="text-center text-error" style="padding: 2rem;">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>Failed to load context entries</p>
            </div>
        `;
    }
}

function createContextItemHTML(entry) {
    const tags = entry.tags || [];
    const tagsHTML = tags.map(tag => `<span class="tag">${tag}</span>`).join('');
    
    return `
        <div class="context-item" data-entry-id="${entry.id}">
            <div class="context-item-header">
                <span class="context-type">
                    <i class="fas fa-${getContextTypeIcon(entry.context_type)}"></i>
                    ${entry.context_type}
                </span>
                <div class="context-actions">
                    <button class="btn btn-danger btn-sm delete-context-btn" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="context-content">${entry.content}</div>
            <div class="context-meta">
                <span><i class="fas fa-calendar"></i> ${formatDate(entry.created_at)}</span>
                <span><i class="fas fa-eye"></i> ${entry.access_count || 0} views</span>
            </div>
            ${tags.length > 0 ? `<div class="context-tags">${tagsHTML}</div>` : ''}
        </div>
    `;
}

function getContextTypeIcon(type) {
    const icons = {
        preference: 'heart',
        note: 'sticky-note',
        event: 'calendar',
        file: 'file'
    };
    return icons[type] || 'tag';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

async function deleteContextEntry(entryId) {
    if (!confirm('Are you sure you want to delete this context entry?')) {
        return;
    }
    
    try {
        await invoke('delete_context_entry', { entryId });
        showNotification('Context entry deleted', 'success');
        await loadContextEntries();
    } catch (error) {
        console.error('Failed to delete context entry:', error);
        showNotification(`Failed to delete context entry: ${error}`, 'error');
    }
}

async function loadKnowledgeSummary() {
    try {
        if (appState.contextEntries.length === 0) {
            elements.knowledgeSummary.innerHTML = '<p>No context available yet. Add some context entries to see what AI knows about you!</p>';
            return;
        }
        
        // Create a summary of context entries
        const summary = appState.contextEntries.slice(0, 3).map(entry => {
            const preview = entry.content.length > 100 ? 
                entry.content.substring(0, 100) + '...' : 
                entry.content;
            return `<div><strong>${entry.context_type}:</strong> ${preview}</div>`;
        }).join('');
        
        elements.knowledgeSummary.innerHTML = `
            <div>${summary}</div>
            ${appState.contextEntries.length > 3 ? 
                `<div class="text-center mt-2"><small>...and ${appState.contextEntries.length - 3} more entries</small></div>` : 
                ''
            }
        `;
    } catch (error) {
        console.error('Failed to load knowledge summary:', error);
        elements.knowledgeSummary.innerHTML = '<p>Failed to load knowledge summary</p>';
    }
}

function switchSection(sectionName) {
    // Update navigation
    navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.section === sectionName);
    });
    
    // Update sections
    sections.forEach(section => {
        section.classList.toggle('active', section.id === sectionName);
    });
    
    appState.currentSection = sectionName;
    
    // Load section-specific data
    if (sectionName === 'context') {
        loadContextEntries();
    } else if (sectionName === 'permissions') {
        loadPermissions();
    }
}

async function loadPermissions() {
    const permissionsGrid = document.getElementById('permissionsGrid');
    permissionsGrid.innerHTML = `
        <div class="text-center" style="padding: 2rem; color: #64748b;">
            <i class="fas fa-shield-alt" style="font-size: 2rem; margin-bottom: 1rem;"></i>
            <p>Permission management coming soon!</p>
        </div>
    `;
}

function showAddContextModal() {
    elements.addContextModal.classList.add('active');
    elements.contextContent.focus();
}

function hideAddContextModal() {
    elements.addContextModal.classList.remove('active');
    elements.contextContent.value = '';
    elements.contextType.value = 'preference';
    elements.contextTags.value = '';
}

async function saveContextEntry() {
    const content = elements.contextContent.value.trim();
    const contextType = elements.contextType.value;
    const tags = elements.contextTags.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    
    if (!content) {
        showNotification('Please enter content', 'error');
        return;
    }
    
    try {
        elements.saveContextBtn.disabled = true;
        elements.saveContextBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        
        await invoke('add_context_entry', { 
            content, 
            contextType, 
            tags 
        });
        
        showNotification('Context entry saved successfully', 'success');
        hideAddContextModal();
        await loadContextEntries();
        await loadKnowledgeSummary();
        
    } catch (error) {
        console.error('Failed to save context entry:', error);
        showNotification(`Failed to save context entry: ${error}`, 'error');
    } finally {
        elements.saveContextBtn.disabled = false;
        elements.saveContextBtn.innerHTML = '<i class="fas fa-save"></i> Save Context';
    }
}

function updateStatusDisplay() {
    if (appState.serverRunning) {
        elements.statusDot.classList.add('running');
        elements.statusDot.classList.remove('warning');
        elements.statusText.textContent = 'ContextVault Running';
    } else {
        elements.statusDot.classList.remove('running');
        elements.statusDot.classList.add('warning');
        elements.statusText.textContent = 'ContextVault Stopped';
    }
}

function startStatusUpdates() {
    // Update status every 30 seconds
    setInterval(async () => {
        try {
            await updateServerStatus();
            await updateOllamaStatus();
        } catch (error) {
            console.error('Status update error:', error);
        }
    }, 30000);
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Hide and remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Add notification styles
const notificationStyles = `
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    padding: 1rem 1.5rem;
    z-index: 1001;
    transform: translateX(100%);
    transition: transform 0.3s ease;
    max-width: 400px;
    border-left: 4px solid #3b82f6;
}

.notification.show {
    transform: translateX(0);
}

.notification-success {
    border-left-color: #10b981;
}

.notification-error {
    border-left-color: #ef4444;
}

.notification-warning {
    border-left-color: #f59e0b;
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: #374151;
    font-weight: 500;
}

.notification-content i {
    font-size: 1.25rem;
}

.notification-success .notification-content i {
    color: #10b981;
}

.notification-error .notification-content i {
    color: #ef4444;
}

.notification-warning .notification-content i {
    color: #f59e0b;
}
`;

// Add styles to page
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);
