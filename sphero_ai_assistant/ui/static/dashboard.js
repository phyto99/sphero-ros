// Sphero AI Assistant Dashboard - Super Productivity Inspired

// Initialize theme
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeAnimations();
});

// Auto-refresh system status every 5 seconds
setInterval(updateSystemStatus, 5000);
setInterval(updateProgressTracking, 10000);

// Theme Management
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.className = savedTheme === 'dark' ? 'dark-theme fade-in' : 'fade-in';
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    const newTheme = isDark ? 'light' : 'dark';
    
    document.body.className = newTheme === 'dark' ? 'dark-theme fade-in' : 'fade-in';
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    icon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// Animation helpers
function initializeAnimations() {
    // Add stagger animation to task items
    const taskItems = document.querySelectorAll('.task-item');
    taskItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 50}ms`;
        item.classList.add('fade-in');
    });
}

async function updateSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        // Update status indicators
        const statusGrid = document.querySelector('.status-grid');
        if (statusGrid && status.components) {
            Object.entries(status.components).forEach(([component, isOnline]) => {
                const statusItem = statusGrid.querySelector(`[data-component="${component}"]`);
                if (statusItem) {
                    statusItem.className = `status-item ${isOnline ? 'online' : 'offline'}`;
                }
            });
        }
    } catch (error) {
        console.error('Failed to update system status:', error);
    }
}

async function updateProgressTracking() {
    try {
        const response = await fetch('/api/progress');
        const progressData = await response.json();
        
        // Update progress bars
        const progressItems = document.querySelectorAll('.progress-item');
        progressItems.forEach((item, index) => {
            if (progressData[index]) {
                const progressFill = item.querySelector('.progress-fill');
                const progressText = item.querySelector('.progress-text');
                
                if (progressFill) {
                    progressFill.style.width = `${progressData[index].percentage}%`;
                }
                if (progressText) {
                    progressText.textContent = `${progressData[index].current}/${progressData[index].total}`;
                }
            }
        });
    } catch (error) {
        console.error('Failed to update progress tracking:', error);
    }
}

async function addTask() {
    const title = document.getElementById('task-title').value.trim();
    const description = document.getElementById('task-description').value.trim();
    const priority = document.getElementById('task-priority').value;
    
    if (!title) {
        alert('Please enter a task title');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('title', title);
        formData.append('description', description);
        formData.append('priority', priority);
        
        const response = await fetch('/api/tasks', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            // Clear form
            document.getElementById('task-title').value = '';
            document.getElementById('task-description').value = '';
            document.getElementById('task-priority').value = 'medium';
            
            // Refresh tasks list
            await refreshTasksList();
        } else {
            alert('Failed to add task');
        }
    } catch (error) {
        console.error('Failed to add task:', error);
        alert('Failed to add task');
    }
}

async function toggleTask(taskId) {
    try {
        const taskItem = document.querySelector(`[data-task-id="${taskId}"]`);
        const checkbox = taskItem.querySelector('input[type="checkbox"]');
        
        const formData = new FormData();
        formData.append('completed', checkbox.checked);
        
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            body: formData
        });
        
        if (response.ok) {
            // Update task appearance
            if (checkbox.checked) {
                taskItem.classList.add('completed');
            } else {
                taskItem.classList.remove('completed');
            }
        } else {
            // Revert checkbox if update failed
            checkbox.checked = !checkbox.checked;
            alert('Failed to update task');
        }
    } catch (error) {
        console.error('Failed to toggle task:', error);
        alert('Failed to update task');
    }
}

async function editTask(taskId) {
    const taskItem = document.querySelector(`[data-task-id="${taskId}"]`);
    const titleElement = taskItem.querySelector('.task-title');
    const descriptionElement = taskItem.querySelector('.task-description');
    
    const currentTitle = titleElement.textContent;
    const currentDescription = descriptionElement ? descriptionElement.textContent : '';
    
    const newTitle = prompt('Edit task title:', currentTitle);
    if (newTitle === null) return; // User cancelled
    
    const newDescription = prompt('Edit task description:', currentDescription);
    if (newDescription === null) return; // User cancelled
    
    try {
        const formData = new FormData();
        formData.append('title', newTitle);
        formData.append('description', newDescription);
        
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            body: formData
        });
        
        if (response.ok) {
            await refreshTasksList();
        } else {
            alert('Failed to update task');
        }
    } catch (error) {
        console.error('Failed to edit task:', error);
        alert('Failed to update task');
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await refreshTasksList();
        } else {
            alert('Failed to delete task');
        }
    } catch (error) {
        console.error('Failed to delete task:', error);
        alert('Failed to delete task');
    }
}

async function refreshTasksList() {
    try {
        const response = await fetch('/api/tasks');
        const data = await response.json();
        
        // This would require more complex DOM manipulation
        // For now, just reload the page
        window.location.reload();
    } catch (error) {
        console.error('Failed to refresh tasks list:', error);
    }
}