"""
Perfect UI Dashboard - Main dashboard interface optimized for daily productivity
"""

import logging
from typing import Dict, Any, List
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn
import asyncio
from datetime import datetime

from .task_manager import TaskManager
from .status_display import StatusDisplay


class UIDashboard:
    """
    Perfect UI Dashboard optimized for daily productivity
    Requirements 1.4, 1.5: Perfect UI with task management and real-time status
    """
    
    def __init__(self, config_manager, ai_agent):
        self.config_manager = config_manager
        self.ai_agent = ai_agent
        self.task_manager = TaskManager(ai_agent)
        self.status_display = StatusDisplay(config_manager)
        self.logger = logging.getLogger(__name__)
        
        # FastAPI app setup
        self.app = FastAPI(title="Sphero AI Assistant Dashboard")
        self.templates = Jinja2Templates(directory="sphero_ai_assistant/ui/templates")
        
        # Setup static files
        static_path = Path("sphero_ai_assistant/ui/static")
        static_path.mkdir(parents=True, exist_ok=True)
        self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        self.is_running = False
        self.server_task = None
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes for the dashboard"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            try:
                # Get current tasks with fallback
                try:
                    tasks = await self.task_manager.get_daily_tasks()
                except Exception as e:
                    self.logger.warning(f"Failed to load tasks, using empty list: {e}")
                    tasks = []
                
                # Get system status with fallback
                try:
                    status = await self.status_display.get_system_status()
                except Exception as e:
                    self.logger.warning(f"Failed to load system status, using default: {e}")
                    status = {
                        'overall_status': 'unknown',
                        'components': {
                            'ai_agent': False,
                            'config_manager': True,
                            'ollama': False,
                            'sphero': False,
                            'ui_dashboard': True,
                            'memory_system': False
                        },
                        'last_updated': datetime.now().isoformat()
                    }
                
                # Get progress tracking data with fallback
                try:
                    progress_data = await self.status_display.get_progress_tracking()
                except Exception as e:
                    self.logger.warning(f"Failed to load progress data, using empty list: {e}")
                    progress_data = []
                
                return self.templates.TemplateResponse("dashboard.html", {
                    "request": request,
                    "tasks": tasks,
                    "system_status": status,
                    "progress_data": progress_data,
                    "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                self.logger.error(f"Critical error loading dashboard: {e}")
                # Return a simple error page instead of raising HTTPException
                error_html = f"""
                <!DOCTYPE html>
                <html>
                <head><title>Dashboard Error</title></head>
                <body>
                    <h1>Dashboard Loading Error</h1>
                    <p>The dashboard encountered an error while loading. Please check the logs for details.</p>
                    <p>Error: {str(e)}</p>
                    <p><a href="/">Try Again</a></p>
                </body>
                </html>
                """
                return HTMLResponse(content=error_html, status_code=500)
        
        @self.app.get("/api/tasks", response_class=JSONResponse)
        async def get_tasks():
            """API endpoint to get current tasks"""
            try:
                tasks = await self.task_manager.get_daily_tasks()
                return {"tasks": tasks}
            except Exception as e:
                self.logger.error(f"Error getting tasks: {e}")
                raise HTTPException(status_code=500, detail="Failed to get tasks")
        
        @self.app.post("/api/tasks", response_class=JSONResponse)
        async def add_task(
            title: str = Form(...),
            description: str = Form(""),
            priority: str = Form("medium")
        ):
            """API endpoint to add a new task"""
            try:
                task = await self.task_manager.add_task(title, description, priority)
                return {"success": True, "task": task}
            except Exception as e:
                self.logger.error(f"Error adding task: {e}")
                raise HTTPException(status_code=500, detail="Failed to add task")
        
        @self.app.put("/api/tasks/{task_id}", response_class=JSONResponse)
        async def update_task(
            task_id: str,
            title: str = Form(None),
            description: str = Form(None),
            priority: str = Form(None),
            completed: bool = Form(None)
        ):
            """API endpoint to update a task"""
            try:
                updates = {}
                if title is not None:
                    updates["title"] = title
                if description is not None:
                    updates["description"] = description
                if priority is not None:
                    updates["priority"] = priority
                if completed is not None:
                    updates["completed"] = completed
                
                task = await self.task_manager.update_task(task_id, updates)
                return {"success": True, "task": task}
            except Exception as e:
                self.logger.error(f"Error updating task: {e}")
                raise HTTPException(status_code=500, detail="Failed to update task")
        
        @self.app.delete("/api/tasks/{task_id}", response_class=JSONResponse)
        async def delete_task(task_id: str):
            """API endpoint to delete a task"""
            try:
                success = await self.task_manager.delete_task(task_id)
                return {"success": success}
            except Exception as e:
                self.logger.error(f"Error deleting task: {e}")
                raise HTTPException(status_code=500, detail="Failed to delete task")
        
        @self.app.get("/api/status", response_class=JSONResponse)
        async def get_system_status():
            """API endpoint to get real-time system status"""
            try:
                status = await self.status_display.get_system_status()
                return status
            except Exception as e:
                self.logger.error(f"Error getting system status: {e}")
                raise HTTPException(status_code=500, detail="Failed to get system status")
        
        @self.app.get("/api/progress", response_class=JSONResponse)
        async def get_progress_tracking():
            """API endpoint to get progress tracking data"""
            try:
                progress = await self.status_display.get_progress_tracking()
                return progress
            except Exception as e:
                self.logger.error(f"Error getting progress data: {e}")
                raise HTTPException(status_code=500, detail="Failed to get progress data")
        
        @self.app.post("/api/ai-analyze-task", response_class=JSONResponse)
        async def analyze_task_for_ai_help(task_id: str = Form(...)):
            """API endpoint to analyze if AI can help with a task"""
            try:
                can_help = await self.task_manager.analyze_task_for_ai_help(task_id)
                return {"can_help": can_help}
            except Exception as e:
                self.logger.error(f"Error analyzing task: {e}")
                raise HTTPException(status_code=500, detail="Failed to analyze task")
        
        @self.app.get("/api/sphero/scan", response_class=JSONResponse)
        async def scan_spheros():
            """API endpoint to scan for available Spheros"""
            try:
                if hasattr(self.ai_agent, 'sphero_controller') and self.ai_agent.sphero_controller:
                    spheros = await self.ai_agent.sphero_controller.scan_for_spheros()
                    return {"success": True, "spheros": spheros}
                else:
                    return {"success": False, "error": "Sphero controller not available"}
            except Exception as e:
                self.logger.error(f"Error scanning for Spheros: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/sphero/connect", response_class=JSONResponse)
        async def connect_sphero(sphero_name: str = Form(None)):
            """API endpoint to connect to Sphero"""
            try:
                if hasattr(self.ai_agent, 'sphero_controller') and self.ai_agent.sphero_controller:
                    if sphero_name:
                        success = await self.ai_agent.sphero_controller.connect_to_specific_sphero(sphero_name)
                    else:
                        success = await self.ai_agent.sphero_controller._connect_to_sphero()
                    return {"success": success}
                else:
                    return {"success": False, "error": "Sphero controller not available"}
            except Exception as e:
                self.logger.error(f"Error connecting to Sphero: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/sphero/disconnect", response_class=JSONResponse)
        async def disconnect_sphero():
            """API endpoint to disconnect from Sphero"""
            try:
                if hasattr(self.ai_agent, 'sphero_controller') and self.ai_agent.sphero_controller:
                    await self.ai_agent.sphero_controller.shutdown()
                return {"success": True}
            except Exception as e:
                self.logger.error(f"Error disconnecting from Sphero: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/sphero/test-led", response_class=JSONResponse)
        async def test_sphero_led():
            """API endpoint to test Sphero LED"""
            try:
                if hasattr(self.ai_agent, 'led_expression_manager') and self.ai_agent.led_expression_manager:
                    from ..sphero import EmotionType
                    await self.ai_agent.led_expression_manager.express_emotion(
                        EmotionType.HAPPY, intensity=1.0, duration=2.0
                    )
                    return {"success": True}
                else:
                    return {"success": False, "error": "LED expression manager not available"}
            except Exception as e:
                self.logger.error(f"Error testing Sphero LED: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/sphero/status", response_class=JSONResponse)
        async def get_sphero_status():
            """API endpoint to get Sphero status"""
            try:
                if hasattr(self.ai_agent, 'get_sphero_status'):
                    status = await self.ai_agent.get_sphero_status()
                    return status
                else:
                    return {"available": False, "error": "Sphero not available"}
            except Exception as e:
                self.logger.error(f"Error getting Sphero status: {e}")
                return {"available": False, "error": str(e)}
    
    async def start_dashboard(self, host: str = "127.0.0.1", port: int = 8000):
        """
        Start the UI dashboard server with port conflict handling
        Requirement 1.2: Perfect UI with auto-startup
        """
        if self.is_running:
            self.logger.warning("Dashboard is already running")
            return
        
        # Try multiple ports if the default is in use
        max_attempts = 5
        original_port = port
        
        for attempt in range(max_attempts):
            current_port = original_port + attempt
            
            try:
                self.logger.info(f"Attempting to start UI Dashboard on {host}:{current_port}")
                
                # Create templates and static directories if they don't exist
                await self._ensure_ui_assets()
                
                # Configure uvicorn with proper error handling
                config = uvicorn.Config(
                    app=self.app,
                    host=host,
                    port=current_port,
                    log_level="error",  # Reduce log noise
                    access_log=False
                )
                
                server = uvicorn.Server(config)
                
                # Test if port is available before starting
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, current_port))
                sock.close()
                
                if result == 0:  # Port is in use
                    self.logger.warning(f"Port {current_port} is already in use, trying next port...")
                    continue
                
                # Start server in background task
                self.server_task = asyncio.create_task(server.serve())
                self.is_running = True
                
                # Give the server a moment to start
                await asyncio.sleep(0.5)
                
                self.logger.info(f"UI Dashboard started successfully on port {current_port}")
                if current_port != original_port:
                    self.logger.info(f"Note: Using port {current_port} instead of {original_port}")
                
                return
                
            except Exception as e:
                self.logger.error(f"Failed to start UI Dashboard on port {current_port}: {e}")
                self.is_running = False
                
                if attempt == max_attempts - 1:  # Last attempt
                    raise RuntimeError(f"Could not start dashboard after {max_attempts} attempts. Last error: {e}")
                
                continue
        
        # If we get here, all ports failed
        raise RuntimeError(f"Could not start dashboard on any port from {original_port} to {original_port + max_attempts - 1}")
    
    async def stop_dashboard(self):
        """Stop the UI dashboard server"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("Stopping UI Dashboard...")
            
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass
            
            self.is_running = False
            self.logger.info("UI Dashboard stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping UI Dashboard: {e}")
    
    async def _ensure_ui_assets(self):
        """Ensure UI templates and static assets exist"""
        templates_dir = Path("sphero_ai_assistant/ui/templates")
        static_dir = Path("sphero_ai_assistant/ui/static")
        
        templates_dir.mkdir(parents=True, exist_ok=True)
        static_dir.mkdir(parents=True, exist_ok=True)
        
        # Create main dashboard template if it doesn't exist
        dashboard_template = templates_dir / "dashboard.html"
        if not dashboard_template.exists():
            await self._create_dashboard_template(dashboard_template)
        
        # Create CSS file if it doesn't exist
        css_file = static_dir / "dashboard.css"
        if not css_file.exists():
            await self._create_dashboard_css(css_file)
        
        # Create JavaScript file if it doesn't exist
        js_file = static_dir / "dashboard.js"
        if not js_file.exists():
            await self._create_dashboard_js(js_file)
    
    async def _create_dashboard_template(self, template_path: Path):
        """Create a simple, clean dashboard HTML template"""
        template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sphero AI Assistant Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: white;
            min-height: 100vh;
            color: #2d3748;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
        }
        .header { 
            background: #f8f9fa; 
            padding: 20px; 
            border: 1px solid #e2e8f0;
            margin-bottom: 20px; 
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 2rem; font-weight: 600; }
        .status-badge { 
            background: #48bb78; 
            color: white; 
            padding: 8px 16px; 
            font-size: 0.75rem; 
            font-weight: 600;
        }
        .grid { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
            margin-bottom: 20px;
        }
        .panel { 
            background: #f8f9fa; 
            padding: 20px; 
            border: 1px solid #e2e8f0;
        }
        .panel h2 { margin-bottom: 16px; font-size: 1.25rem; }
        .status-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 12px;
        }
        .status-item { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 12px; 
            background: white; 
            border: 1px solid #e2e8f0;
            border-left: 4px solid #e2e8f0;
        }
        .status-item.online { border-left-color: #48bb78; }
        .status-item.offline { border-left-color: #f56565; }
        .status-indicator { 
            width: 8px; 
            height: 8px; 
            border-radius: 50%; 
            background: #e2e8f0;
        }
        .status-item.online .status-indicator { background: #48bb78; }
        .status-item.offline .status-indicator { background: #f56565; }
        .progress-item { 
            display: flex; 
            align-items: center; 
            gap: 12px; 
            margin-bottom: 12px;
        }
        .progress-label { min-width: 100px; font-weight: 500; }
        .progress-bar { 
            flex: 1; 
            height: 6px; 
            background: #e2e8f0; 
            overflow: hidden;
        }
        .progress-fill { 
            height: 100%; 
            background: #48bb78; 
            transition: width 0.3s ease;
        }
        .progress-text { font-size: 0.75rem; color: #718096; }
        .task-panel { grid-column: 1 / -1; }
        .add-task-form { 
            display: flex; 
            gap: 8px; 
            margin-bottom: 20px; 
            background: white; 
            padding: 12px; 
            border: 1px solid #e2e8f0;
        }
        .add-task-form input, .add-task-form select { 
            padding: 8px 12px; 
            border: 1px solid #e2e8f0; 
            font-size: 14px;
        }
        .add-task-form input[type="text"] { flex: 1; }
        .add-task-form button { 
            background: #48bb78; 
            color: white; 
            border: none; 
            padding: 8px 16px; 
            cursor: pointer; 
            font-weight: 500;
        }
        .add-task-form button:hover { background: #38a169; }
        .task-item { 
            display: flex; 
            align-items: flex-start; 
            gap: 12px; 
            padding: 12px; 
            border: 1px solid #e2e8f0; 
            margin-bottom: 8px;
            background: white;
        }
        .task-item.ai-assistable { border-left: 4px solid #48bb78; }
        .task-item.completed { opacity: 0.6; }
        .task-item.completed .task-title { text-decoration: line-through; }
        .task-content { flex: 1; }
        .task-title { font-weight: 500; margin-bottom: 4px; }
        .task-description { font-size: 0.875rem; color: #718096; margin-bottom: 8px; }
        .task-meta { display: flex; gap: 8px; }
        .task-priority { 
            font-size: 0.75rem; 
            padding: 2px 8px; 
            background: #e2e8f0; 
            color: #4a5568;
        }
        .task-priority.priority-high { background: #fed7d7; color: #c53030; }
        .task-priority.priority-medium { background: #feebc8; color: #dd6b20; }
        .task-priority.priority-low { background: #c6f6d5; color: #2f855a; }
        .ai-help-indicator { 
            font-size: 0.75rem; 
            background: #c6f6d5; 
            color: #2f855a; 
            padding: 2px 8px;
        }
        .task-actions { display: flex; gap: 4px; }
        .task-actions button { 
            background: #f7fafc; 
            border: 1px solid #e2e8f0; 
            padding: 4px 8px; 
            cursor: pointer; 
            font-size: 0.75rem;
        }
        .task-actions button:hover { background: #edf2f7; }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div>
                <h1>Sphero AI Assistant</h1>
                <div>{{ current_time }}</div>
            </div>
            <div class="status-badge">System Ready</div>
        </header>
        
        <div class="grid">
            <div class="panel">
                <h2>System Status</h2>
                <div class="status-grid">
                    {% for component, status in system_status.components.items() %}
                    <div class="status-item {{ 'online' if status else 'offline' }}">
                        <span>{{ component.replace('_', ' ').title() }}</span>
                        <span class="status-indicator"></span>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="panel">
                <h2>Progress Tracking</h2>
                {% for item in progress_data %}
                <div class="progress-item">
                    <div class="progress-label">{{ item.name }}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ item.percentage }}%"></div>
                    </div>
                    <div class="progress-text">{{ item.current }}/{{ item.total }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="panel task-panel">
            <h2>Daily Tasks</h2>
            
            <div class="add-task-form">
                <input type="text" id="task-title" placeholder="What needs to be done?" />
                <input type="text" id="task-description" placeholder="Add details..." />
                <select id="task-priority">
                    <option value="low">Low</option>
                    <option value="medium" selected>Medium</option>
                    <option value="high">High</option>
                </select>
                <button onclick="addTask()">Add Task</button>
            </div>
            
            <div id="tasks-list">
                {% for task in tasks %}
                <div class="task-item {{ 'ai-assistable' if task.ai_can_help else '' }} {{ 'completed' if task.completed else '' }}" data-task-id="{{ task.id }}">
                    <input type="checkbox" {{ 'checked' if task.completed else '' }} onchange="toggleTask('{{ task.id }}')">
                    <div class="task-content">
                        <div class="task-title">{{ task.title }}</div>
                        {% if task.description %}
                        <div class="task-description">{{ task.description }}</div>
                        {% endif %}
                        <div class="task-meta">
                            <span class="task-priority priority-{{ task.priority }}">{{ task.priority }}</span>
                            {% if task.ai_can_help %}
                            <span class="ai-help-indicator">🤖 AI can help</span>
                            {% endif %}
                        </div>
                    </div>
                    <div class="task-actions">
                        <button onclick="editTask('{{ task.id }}')">Edit</button>
                        <button onclick="deleteTask('{{ task.id }}')">Delete</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <script>
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
                    document.getElementById('task-title').value = '';
                    document.getElementById('task-description').value = '';
                    document.getElementById('task-priority').value = 'medium';
                    window.location.reload();
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
                    if (checkbox.checked) {
                        taskItem.classList.add('completed');
                    } else {
                        taskItem.classList.remove('completed');
                    }
                } else {
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
            if (newTitle === null) return;
            
            const newDescription = prompt('Edit task description:', currentDescription);
            if (newDescription === null) return;
            
            try {
                const formData = new FormData();
                formData.append('title', newTitle);
                formData.append('description', newDescription);
                
                const response = await fetch(`/api/tasks/${taskId}`, {
                    method: 'PUT',
                    body: formData
                });
                
                if (response.ok) {
                    window.location.reload();
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
                    window.location.reload();
                } else {
                    alert('Failed to delete task');
                }
            } catch (error) {
                console.error('Failed to delete task:', error);
                alert('Failed to delete task');
            }
        }
    </script>
</body>
</html>'''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    async def _create_dashboard_css(self, css_path: Path):
        """Create the dashboard CSS file"""
        css_content = '''/* Sphero AI Assistant Dashboard - Super Productivity Inspired */

/* ===============================
   CSS VARIABLES - DESIGN SYSTEM
   =============================== */
:root {
  /* Spacing System (8px base) */
  --s: 8px;
  --s-half: 4px;
  --s2: 16px;
  --s3: 24px;
  --s4: 32px;
  --s5: 40px;
  --s6: 48px;
  
  /* Layout */
  --component-max-width: 1200px;
  --card-border-radius: 8px;
  --bar-height: 56px;
  
  /* Shadows (Material Design inspired) */
  --shadow-1: 0 2px 8px rgba(0, 0, 0, 0.12), 0 1px 3px -2px rgba(0, 0, 0, 0.16);
  --shadow-2: 0 4px 12px rgba(0, 0, 0, 0.14), 0 6px 16px -4px rgba(0, 0, 0, 0.12);
  --shadow-3: 0 8px 24px rgba(0, 0, 0, 0.14), 0 12px 28px -6px rgba(0, 0, 0, 0.12);
  
  /* Transitions */
  --transition-fast: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-standard: all 225ms cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Colors - Light Theme */
  --bg: #f8f9fa;
  --bg-card: #ffffff;
  --bg-elevated: #ffffff;
  --text-primary: #2d3748;
  --text-secondary: #718096;
  --text-muted: rgba(45, 55, 72, 0.6);
  --border-color: rgba(0, 0, 0, 0.12);
  --divider-color: #e2e8f0;
  
  /* Brand Colors */
  --primary: #667eea;
  --primary-light: #8b9cf7;
  --primary-dark: #4c63d2;
  --accent: #764ba2;
  --success: #48bb78;
  --warning: #ed8936;
  --danger: #f56565;
  
  /* Task Colors */
  --task-bg: var(--bg-card);
  --task-bg-hover: #f7fafc;
  --task-bg-selected: #edf2f7;
  --task-shadow: var(--shadow-1);
  --task-shadow-hover: var(--shadow-2);
}

/* Dark Theme */
body.dark-theme {
  --bg: #1a202c;
  --bg-card: #2d3748;
  --bg-elevated: #4a5568;
  --text-primary: #f7fafc;
  --text-secondary: #cbd5e0;
  --text-muted: rgba(247, 250, 252, 0.6);
  --border-color: rgba(255, 255, 255, 0.12);
  --divider-color: #4a5568;
  
  --task-bg: var(--bg-card);
  --task-bg-hover: #4a5568;
  --task-bg-selected: #718096;
}

/* ===============================
   BASE STYLES
   =============================== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  min-height: 100vh;
  color: var(--text-primary);
  line-height: 1.6;
  font-optical-sizing: auto;
  position: relative;
}

/* Beautiful gradient backgrounds - Super Productivity Style */
body.light-theme {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

body.dark-theme {
  /* Super Productivity dark gradient - black to blue */
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #533483 100%);
}

/* Animated gradient overlay for extra beauty */
body::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, 
    rgba(102, 126, 234, 0.1) 0%, 
    rgba(118, 75, 162, 0.1) 25%,
    rgba(56, 178, 172, 0.1) 50%,
    rgba(129, 230, 217, 0.1) 75%,
    rgba(102, 126, 234, 0.1) 100%);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
  pointer-events: none;
  z-index: -1;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* ===============================
   LAYOUT COMPONENTS
   =============================== */
.dashboard-container {
  max-width: var(--component-max-width);
  margin: 0 auto;
  padding: var(--s3);
  min-height: 100vh;
}

.dashboard-header {
  background: var(--bg-card);
  padding: var(--s3);
  border-radius: var(--card-border-radius);
  margin-bottom: var(--s3);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--shadow-1);
  border: 1px solid var(--border-color);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--s2);
}

.status-badge {
  padding: var(--s-half) var(--s2);
  background: var(--success);
  color: white;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dashboard-header h1 {
  color: var(--text-primary);
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
}

.current-time {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto 1fr;
  gap: var(--s3);
  min-height: calc(100vh - 200px);
}

/* Card Base Styles */
.panel-card {
  background: var(--bg-card);
  padding: var(--s3);
  border-radius: var(--card-border-radius);
  box-shadow: var(--shadow-1);
  border: 1px solid var(--border-color);
  transition: var(--transition-standard);
}

.panel-card:hover {
  box-shadow: var(--shadow-2);
}

.status-panel {
  @extend .panel-card;
}

.progress-panel {
  @extend .panel-card;
}

.task-panel {
  @extend .panel-card;
  grid-column: 1 / -1;
  overflow-y: auto;
  max-height: 600px;
}

h2 {
  color: var(--text-primary);
  margin-bottom: var(--s3);
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.025em;
}

/* ===============================
   STATUS & PROGRESS COMPONENTS
   =============================== */

/* Status Grid */
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--s2);
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--s2);
  border-radius: var(--card-border-radius);
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  transition: var(--transition-fast);
}

.status-item:hover {
  box-shadow: var(--shadow-1);
}

.status-item.online {
  border-left: 4px solid var(--success);
  background: linear-gradient(135deg, var(--bg-elevated) 0%, rgba(72, 187, 120, 0.05) 100%);
}

.status-item.offline {
  border-left: 4px solid var(--danger);
  background: linear-gradient(135deg, var(--bg-elevated) 0%, rgba(245, 101, 101, 0.05) 100%);
}

.status-name {
    font-weight: 500;
    text-transform: capitalize;
}

.status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #e2e8f0;
}

.status-item.online .status-indicator {
    background: #48bb78;
    box-shadow: 0 0 10px rgba(72, 187, 120, 0.5);
}

.status-item.offline .status-indicator {
    background: #f56565;
    box-shadow: 0 0 10px rgba(245, 101, 101, 0.5);
}

/* Progress Tracking - Material Design Style */
.progress-items {
  display: flex;
  flex-direction: column;
  gap: var(--s3);
}

.progress-item {
  display: flex;
  align-items: center;
  gap: var(--s2);
  padding: var(--s2);
  background: var(--bg-elevated);
  border-radius: var(--card-border-radius);
  border: 1px solid var(--border-color);
  transition: var(--transition-fast);
}

.progress-item:hover {
  box-shadow: var(--shadow-1);
}

.progress-label {
  min-width: 100px;
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-primary);
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: var(--divider-color);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: 3px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-text {
  min-width: 60px;
  text-align: right;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

/* ===============================
   TASK MANAGEMENT COMPONENTS
   =============================== */

/* Add Task Form - Super Productivity Style */
.add-task-form {
  display: flex;
  gap: var(--s);
  margin-bottom: var(--s3);
  background: var(--bg-card);
  border-radius: var(--card-border-radius);
  box-shadow: var(--shadow-1);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.add-task-form input,
.add-task-form select {
  padding: var(--s2);
  border: none;
  background: transparent;
  font-size: 1rem;
  color: var(--text-primary);
  font-family: inherit;
  transition: var(--transition-fast);
}

.add-task-form input:focus,
.add-task-form select:focus {
  outline: none;
  background: var(--task-bg-hover);
}

.add-task-form input[type="text"] {
  flex: 1;
  min-width: 200px;
  font-weight: 500;
}

.add-task-form input::placeholder {
  color: var(--text-muted);
  opacity: 1;
}

.add-task-form select {
  min-width: 120px;
  cursor: pointer;
  border-left: 1px solid var(--divider-color);
}

.add-task-form button {
  padding: 0 var(--s3);
  background: var(--primary);
  color: white;
  border: none;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--s-half);
}

.add-task-form button:hover {
  background: var(--primary-dark);
  transform: translateY(-1px);
}

.add-task-form button:active {
  transform: translateY(0);
}

/* ===============================
   SUPER PRODUCTIVITY TASK SYSTEM
   =============================== */

/* Task Panel Header */
.task-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--s3);
}

.current-task-badge {
  background: var(--primary);
  color: white;
  padding: var(--s-half) var(--s2);
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* Super Productivity Add Task Bar */
.add-task-bar {
  display: flex;
  background: var(--bg-card);
  border-radius: var(--card-border-radius);
  box-shadow: var(--shadow-2);
  border: 1px solid var(--border-color);
  margin-bottom: var(--s3);
  overflow: hidden;
}

.main-input {
  flex: 1;
  padding: var(--s2);
  border: none;
  background: transparent;
  font-size: 1rem;
  color: var(--text-primary);
  font-family: inherit;
  outline: none;
}

.main-input::placeholder {
  color: var(--text-muted);
  font-style: italic;
}

.task-controls {
  display: flex;
  border-left: 1px solid var(--divider-color);
}

.add-btn, .view-toggle-btn {
  padding: var(--s2);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
}

.add-btn:hover, .view-toggle-btn:hover {
  background: var(--primary);
  color: white;
}

/* Task Tabs */
.task-tabs {
  display: flex;
  margin-bottom: var(--s3);
  border-bottom: 1px solid var(--divider-color);
}

.tab-btn {
  padding: var(--s2) var(--s3);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  transition: var(--transition-fast);
}

.tab-btn.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}

.tab-btn:hover {
  color: var(--text-primary);
  background: var(--task-bg-hover);
}

/* Task Views */
.task-view {
  display: none;
}

.task-view.active {
  display: block;
}

/* Super Productivity Task Items */
.tasks-list {
  display: flex;
  flex-direction: column;
  gap: var(--s);
  max-height: 600px;
  overflow-y: auto;
  padding-right: var(--s-half);
}

.super-task-item {
  display: flex;
  align-items: flex-start;
  gap: var(--s2);
  padding: var(--s2);
  background: var(--task-bg);
  border-radius: var(--card-border-radius);
  border: 1px solid var(--border-color);
  box-shadow: var(--task-shadow);
  transition: var(--transition-standard);
  position: relative;
}

.super-task-item:hover {
  box-shadow: var(--task-shadow-hover);
  border-color: var(--primary-light);
  transform: translateY(-1px);
}

.super-task-item.ai-assistable {
  border-left: 4px solid var(--success);
  background: linear-gradient(135deg, var(--task-bg) 0%, rgba(72, 187, 120, 0.02) 100%);
}

.super-task-item.completed {
  opacity: 0.6;
  background: var(--task-bg-hover);
}

.super-task-item.completed .task-title {
  text-decoration: line-through;
  color: var(--text-muted);
}

/* Task Drag Handle */
.task-drag-handle {
  color: var(--text-muted);
  cursor: grab;
  font-size: 0.75rem;
  line-height: 1;
  padding: var(--s-half) 0;
  user-select: none;
}

.task-drag-handle:active {
  cursor: grabbing;
}

/* Task Content */
.task-content {
  flex: 1;
  min-width: 0;
}

.task-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--s-half);
  cursor: pointer;
  word-wrap: break-word;
}

.task-title:hover {
  color: var(--primary);
}

.task-notes {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: var(--s);
  line-height: 1.4;
}

.task-meta {
  display: flex;
  gap: var(--s);
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: var(--s);
}

.time-estimate {
  background: var(--bg-elevated);
  color: var(--text-secondary);
  padding: 2px var(--s);
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.ai-help-indicator {
  background: var(--success);
  color: white;
  padding: 2px var(--s);
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.sphero-indicator {
  background: var(--primary);
  color: white;
  padding: 2px var(--s);
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Sub-tasks */
.sub-tasks {
  margin-top: var(--s2);
  padding-left: var(--s3);
  border-left: 2px solid var(--divider-color);
}

.sub-task-item {
  display: flex;
  align-items: center;
  gap: var(--s);
  padding: var(--s-half) 0;
  font-size: 0.875rem;
}

.sub-task-item.completed .sub-task-title {
  text-decoration: line-through;
  color: var(--text-muted);
}

/* Task Actions */
.task-actions {
  display: flex;
  gap: var(--s-half);
  opacity: 0;
  transition: var(--transition-fast);
}

.super-task-item:hover .task-actions {
  opacity: 1;
}

.task-actions button {
  padding: var(--s-half);
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 4px;
  transition: var(--transition-fast);
  font-size: 0.875rem;
}

.play-btn:hover { background: var(--success); color: white; }
.edit-btn:hover { background: var(--warning); color: white; }
.subtask-btn:hover { background: var(--primary); color: white; }
.delete-btn:hover { background: var(--danger); color: white; }

/* Today and Overdue Task Styles */
.today-task {
  border-left: 4px solid var(--warning);
}

.overdue-task {
  border-left: 4px solid var(--danger);
  background: linear-gradient(135deg, var(--task-bg) 0%, rgba(245, 101, 101, 0.05) 100%);
}

.overdue-indicator {
  color: var(--danger);
  font-weight: 600;
  font-size: 0.75rem;
}

/* ===============================
   CALENDAR INTEGRATION
   =============================== */

.calendar-panel {
  @extend .panel-card;
  grid-column: 1 / -1;
  max-height: 300px;
  overflow-y: auto;
}

.calendar-events {
  display: flex;
  flex-direction: column;
  gap: var(--s2);
}

.calendar-event {
  display: flex;
  align-items: center;
  gap: var(--s2);
  padding: var(--s2);
  background: var(--bg-elevated);
  border-radius: var(--card-border-radius);
  border: 1px solid var(--border-color);
  transition: var(--transition-fast);
}

.calendar-event:hover {
  box-shadow: var(--shadow-1);
}

.calendar-event.due-now {
  border-left: 4px solid var(--warning);
  background: linear-gradient(135deg, var(--bg-elevated) 0%, rgba(237, 137, 54, 0.1) 100%);
  animation: pulse 2s infinite;
}

.event-time {
  min-width: 60px;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-variant-numeric: tabular-nums;
}

.event-content {
  flex: 1;
}

.event-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.event-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.event-actions {
  opacity: 0;
  transition: var(--transition-fast);
}

.calendar-event:hover .event-actions {
  opacity: 1;
}

.create-task-btn {
  padding: var(--s-half);
  border: none;
  background: var(--primary);
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.create-task-btn:hover {
  background: var(--primary-dark);
}

/* Custom Scrollbar */
.tasks-list::-webkit-scrollbar {
  width: 4px;
}

.tasks-list::-webkit-scrollbar-track {
  background: transparent;
}

.tasks-list::-webkit-scrollbar-thumb {
  background: var(--text-muted);
  border-radius: 2px;
}

.tasks-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}

/* Task Item - Material Design Card Style */
.task-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: var(--s2);
  padding: var(--s2);
  background: var(--task-bg);
  border-radius: var(--card-border-radius);
  border: 1px solid var(--border-color);
  box-shadow: var(--task-shadow);
  transition: var(--transition-standard);
  cursor: pointer;
}

.task-item:hover {
  box-shadow: var(--task-shadow-hover);
  border-color: var(--primary-light);
  transform: translateY(-1px);
}

.task-item.ai-assistable {
  border-left: 4px solid var(--success);
  background: linear-gradient(135deg, var(--task-bg) 0%, rgba(72, 187, 120, 0.02) 100%);
}

.task-item.ai-assistable::before {
  content: '';
  position: absolute;
  top: var(--s);
  right: var(--s);
  width: 8px;
  height: 8px;
  background: var(--success);
  border-radius: 50%;
  box-shadow: 0 0 0 2px var(--task-bg);
}

.task-item.completed {
  opacity: 0.5;
  background: var(--task-bg-hover);
}

.task-item.completed .task-title {
  text-decoration: line-through;
  color: var(--text-muted);
}

.task-checkbox input {
    width: 20px;
    height: 20px;
    cursor: pointer;
}

.task-content {
    flex: 1;
}

.task-title {
    font-size: 1.1em;
    font-weight: 600;
    color: #2d3748;
    margin-bottom: 5px;
}

.task-description {
    color: #718096;
    font-size: 0.9em;
    margin-bottom: 8px;
}

.task-meta {
    display: flex;
    gap: 10px;
    align-items: center;
}

.task-priority {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: 500;
    text-transform: uppercase;
}

.priority-low {
    background: #e6fffa;
    color: #319795;
}

.priority-medium {
    background: #fef5e7;
    color: #d69e2e;
}

.priority-high {
    background: #fed7d7;
    color: #e53e3e;
}

.ai-help-indicator {
    background: #48bb78;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: 500;
}

.task-actions {
    display: flex;
    gap: 8px;
}

.task-actions button {
    padding: 8px 12px;
    border: 1px solid #e2e8f0;
    background: white;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9em;
    transition: all 0.2s ease;
}

.task-actions button:hover {
    background: #f7fafc;
    border-color: #cbd5e0;
}

/* ===============================
   RESPONSIVE DESIGN
   =============================== */
@media (max-width: 768px) {
  .dashboard-container {
    padding: var(--s2);
  }
  
  .dashboard-content {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto 1fr;
    gap: var(--s2);
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: var(--s2);
    text-align: center;
    padding: var(--s2);
  }
  
  .dashboard-header h1 {
    font-size: 1.5rem;
  }
  
  .add-task-form {
    flex-direction: column;
  }
  
  .add-task-form input,
  .add-task-form select,
  .add-task-form button {
    width: 100%;
  }
  
  .status-grid {
    grid-template-columns: 1fr;
  }
  
  .task-item {
    padding: var(--s2);
  }
  
  .progress-item {
    flex-direction: column;
    align-items: stretch;
    gap: var(--s);
  }
  
  .progress-label {
    min-width: auto;
  }
}

@media (max-width: 480px) {
  .dashboard-container {
    padding: var(--s);
  }
  
  .task-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .task-actions {
    justify-content: flex-end;
    margin-top: var(--s);
  }
}

/* ===============================
   UTILITY CLASSES
   =============================== */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Dark theme toggle */
.theme-toggle {
  position: fixed;
  top: var(--s2);
  right: var(--s2);
  padding: var(--s);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: var(--shadow-1);
  transition: var(--transition-fast);
  z-index: 1000;
}

.theme-toggle:hover {
  box-shadow: var(--shadow-2);
}'''
        
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)
    
    async def _create_dashboard_js(self, js_path: Path):
        """Create the dashboard JavaScript file"""
        js_content = '''// Sphero AI Assistant Dashboard - Super Productivity Inspired

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
}'''
        
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(js_content)