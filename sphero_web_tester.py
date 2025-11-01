"""
Sphero Bolt Web UI Tester
A localhost web interface to test all available Sphero commands
"""

import asyncio
import json
import time
import logging
import concurrent.futures
from typing import Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.types import Color
import uvicorn
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpheroWebTester:
    def __init__(self):
        self.toy = None
        self.connected = False
        self.websocket = None
        self.commands_cache = []
        
    def connect_sphero_sync(self, robot_id="SB-5925", max_attempts=3):
        """Connect to Sphero using the WORKING api.py approach"""
        
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            
            try:
                # Step 1: Scan for toys (same as api.py)
                toys = scanner.find_toys(timeout=8)
                
                if not toys:
                    if attempt < max_attempts:
                        time.sleep(5)
                        continue
                    return False, "❌ No Sphero found"
                
                matching_toys = [t for t in toys if robot_id.upper() in t.name.upper()]
                
                if not matching_toys:
                    if attempt < max_attempts:
                        time.sleep(5)
                        continue
                    return False, f"❌ No Sphero matching '{robot_id}' found"
                
                found_toy = matching_toys[0]
                
                # Step 2: Wait for initialization (same as api.py)
                time.sleep(3)  # Wait for full wake
                
                # Step 3: Connect using SpheroEduAPI wrapper (same as api.py)
                self.api = SpheroEduAPI(found_toy)
                self.api.__enter__()
                
                # Test connection
                heading = self.api.get_heading()
                
                # Step 4: Get the underlying toy object for low-level access
                if hasattr(self.api, '_toy'):
                    self.toy = self.api._toy
                else:
                    # Fallback - use the original toy
                    self.toy = found_toy
                
                self.connected = True
                
                # Cache all available commands from the low-level toy
                self.cache_commands_sync()
                
                return True, f"✅ Connected to {found_toy.name}! (Heading: {heading}°)"
                
            except Exception as e:
                if self.api:
                    try:
                        self.api.__exit__(None, None, None)
                    except:
                        pass
                    self.api = None
                
                if attempt < max_attempts:
                    time.sleep(5)
                    continue
                return False, f"❌ Connection failed: {e}"
        
        return False, "❌ Failed after all attempts"
    
    async def connect_sphero(self, robot_id="SB-5925"):
        """Async wrapper for connection"""
        await self.send_message("info", "🔍 Scanning for Sphero...")
        
        # Run the sync connection in a thread to avoid blocking
        import concurrent.futures
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            success, message = await loop.run_in_executor(executor, self.connect_sphero_sync, robot_id)
        
        if success:
            await self.send_message("success", message)
            return True
        else:
            await self.send_message("error", message)
            return False
    
    def cache_commands_sync(self):
        """Cache all available commands with their info (sync version)"""
        attrs = [a for a in dir(self.toy) if not a.startswith('_')]
        
        commands = []
        for attr in attrs:
            try:
                obj = getattr(self.toy, attr)
                cmd_info = {
                    'name': attr,
                    'type': 'method' if callable(obj) else 'property',
                    'doc': getattr(obj, '__doc__', None) or 'No documentation',
                    'category': self.categorize_command(attr)
                }
                commands.append(cmd_info)
            except:
                pass
        
        self.commands_cache = sorted(commands, key=lambda x: (x['category'], x['name']))
    
    async def cache_commands(self):
        """Async wrapper for caching commands"""
        await self.send_message("info", "📋 Analyzing available commands...")
        
        # Commands are already cached by connect_sphero_sync
        await self.send_message("commands_loaded", {
            'commands': self.commands_cache,
            'total': len(self.commands_cache)
        })
    
    def categorize_command(self, name: str) -> str:
        """Categorize commands for better organization"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['led', 'light', 'color']):
            return 'LEDs'
        elif any(word in name_lower for word in ['matrix', 'frame', 'pixel', 'animation', 'compressed']):
            return 'Matrix/Animation'
        elif any(word in name_lower for word in ['drive', 'roll', 'spin', 'move', 'heading']):
            return 'Movement'
        elif any(word in name_lower for word in ['sensor', 'gyro', 'accel', 'magnet', 'stream']):
            return 'Sensors'
        elif any(word in name_lower for word in ['collision', 'notify', 'listener', 'event']):
            return 'Events'
        elif any(word in name_lower for word in ['config', 'set', 'get', 'enable', 'disable']):
            return 'Configuration'
        elif any(word in name_lower for word in ['sound', 'audio', 'speaker']):
            return 'Audio'
        elif any(word in name_lower for word in ['power', 'battery', 'sleep', 'wake']):
            return 'Power'
        else:
            return 'Other'
    
    async def execute_command(self, command_name: str, params: List[Any] = None):
        """Execute a command on the Sphero (low-level toy object)"""
        if not self.connected or not self.toy:
            await self.send_message("error", "❌ Not connected to Sphero")
            return
        
        try:
            await self.send_message("info", f"🚀 Executing: {command_name}")
            
            # Try to get the command from the low-level toy object
            obj = getattr(self.toy, command_name)
            
            if callable(obj):
                if params:
                    # Convert string params to appropriate types
                    converted_params = []
                    for param in params:
                        if isinstance(param, str) and param.strip():
                            # Try to convert to number
                            try:
                                if '.' in param:
                                    converted_params.append(float(param))
                                else:
                                    converted_params.append(int(param))
                            except ValueError:
                                # Try to convert to Color if it looks like RGB
                                if ',' in param:
                                    try:
                                        rgb_values = [int(x.strip()) for x in param.split(',')]
                                        if len(rgb_values) == 3:
                                            converted_params.append(Color(*rgb_values))
                                            continue
                                    except:
                                        pass
                                # Keep as string
                                converted_params.append(param)
                        else:
                            converted_params.append(param)
                    
                    await self.send_message("info", f"   Parameters: {converted_params}")
                    result = obj(*converted_params)
                else:
                    result = obj()
                
                await self.send_message("success", f"✅ {command_name}() executed successfully")
                if result is not None:
                    await self.send_message("result", f"Result: {result}")
            else:
                # It's a property
                await self.send_message("result", f"{command_name} = {obj}")
                
        except Exception as e:
            await self.send_message("error", f"❌ Error executing {command_name}: {e}")
            
            # If low-level command fails, suggest trying high-level API
            if self.api and hasattr(self.api, command_name):
                await self.send_message("info", f"💡 Trying high-level API version...")
                try:
                    api_obj = getattr(self.api, command_name)
                    if callable(api_obj):
                        if params:
                            result = api_obj(*converted_params)
                        else:
                            result = api_obj()
                        await self.send_message("success", f"✅ High-level {command_name}() worked!")
                        if result is not None:
                            await self.send_message("result", f"Result: {result}")
                    else:
                        await self.send_message("result", f"High-level {command_name} = {api_obj}")
                except Exception as e2:
                    await self.send_message("error", f"❌ High-level API also failed: {e2}")
    
    async def send_message(self, msg_type: str, data: Any):
        """Send message to websocket"""
        if self.websocket:
            try:
                await self.websocket.send_json({
                    'type': msg_type,
                    'data': data,
                    'timestamp': time.time()
                })
            except:
                pass
    
    def disconnect(self):
        """Disconnect from Sphero"""
        if self.connected:
            try:
                if self.api:
                    self.api.__exit__(None, None, None)
                    self.api = None
                self.toy = None
                self.connected = False
            except Exception as e:
                pass

# Global tester instance
tester = SpheroWebTester()

# FastAPI app
app = FastAPI(title="Sphero Web Tester")

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Sphero Bolt Web Tester</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .status-panel {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .connection-controls {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            font-size: 14px;
        }
        
        .btn-primary {
            background: #4CAF50;
            color: white;
        }
        
        .btn-primary:hover {
            background: #45a049;
            transform: translateY(-2px);
        }
        
        .btn-danger {
            background: #f44336;
            color: white;
        }
        
        .btn-danger:hover {
            background: #da190b;
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #2196F3;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #1976D2;
            transform: translateY(-2px);
        }
        
        .status {
            padding: 10px 15px;
            border-radius: 8px;
            font-weight: 600;
            margin-left: auto;
        }
        
        .status.disconnected {
            background: #ffebee;
            color: #c62828;
        }
        
        .status.connected {
            background: #e8f5e8;
            color: #2e7d32;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .commands-panel, .console-panel {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .panel-title {
            font-size: 1.4em;
            font-weight: 700;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .category-filter {
            margin-bottom: 20px;
        }
        
        .category-filter select {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .commands-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            max-height: 600px;
            overflow-y: auto;
        }
        
        .command-card {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .command-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .command-name {
            font-weight: 700;
            color: #333;
            margin-bottom: 5px;
        }
        
        .command-type {
            font-size: 12px;
            padding: 3px 8px;
            border-radius: 12px;
            margin-bottom: 8px;
            display: inline-block;
        }
        
        .command-type.method {
            background: #e3f2fd;
            color: #1976d2;
        }
        
        .command-type.property {
            background: #f3e5f5;
            color: #7b1fa2;
        }
        
        .command-doc {
            font-size: 12px;
            color: #666;
            line-height: 1.4;
        }
        
        .console {
            background: #1e1e1e;
            color: #fff;
            border-radius: 8px;
            padding: 15px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.4;
        }
        
        .console-message {
            margin-bottom: 8px;
            padding: 5px 0;
        }
        
        .console-message.info {
            color: #81c784;
        }
        
        .console-message.success {
            color: #4caf50;
            font-weight: 600;
        }
        
        .console-message.error {
            color: #f44336;
            font-weight: 600;
        }
        
        .console-message.result {
            color: #ffeb3b;
            background: rgba(255, 235, 59, 0.1);
            padding: 8px;
            border-radius: 4px;
        }
        
        .quick-tests {
            margin-top: 20px;
        }
        
        .quick-test-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .param-input {
            margin-top: 10px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 100%;
            font-size: 12px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .commands-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Sphero Bolt Web Tester</h1>
            <p>Test all 100+ Sphero commands with a beautiful web interface</p>
        </div>
        
        <div class="status-panel">
            <div class="connection-controls">
                <button id="connectBtn" class="btn btn-primary">🔌 Connect to Sphero</button>
                <button id="disconnectBtn" class="btn btn-danger" disabled>🔌 Disconnect</button>
                <button id="clearConsoleBtn" class="btn btn-secondary">🗑️ Clear Console</button>
                <div id="connectionStatus" class="status disconnected">❌ Disconnected</div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="commands-panel">
                <h2 class="panel-title">🎮 Commands</h2>
                
                <div class="category-filter">
                    <select id="categoryFilter">
                        <option value="">All Categories</option>
                    </select>
                </div>
                
                <div id="commandsContainer" class="loading">
                    <div class="spinner"></div>
                    <p>Connect to Sphero to load commands...</p>
                </div>
                
                <div class="quick-tests">
                    <h3>⚡ Quick Tests</h3>
                    <div class="quick-test-grid">
                        <button class="btn btn-secondary" onclick="quickTest('LEDs', 'set_main_led', [255, 0, 0])">🔴 Red LED</button>
                        <button class="btn btn-secondary" onclick="quickTest('LEDs', 'set_back_led', [0, 255, 0])">🟢 Green Back</button>
                        <button class="btn btn-secondary" onclick="quickTest('Matrix/Animation', 'set_matrix_character', ['A'])">🅰️ Show 'A'</button>
                        <button class="btn btn-secondary" onclick="quickTest('Movement', 'spin', [360, 1])">🌀 Spin 360°</button>
                    </div>
                </div>
            </div>
            
            <div class="console-panel">
                <h2 class="panel-title">📟 Console</h2>
                <div id="console" class="console">
                    <div class="console-message info">🚀 Sphero Web Tester Ready</div>
                    <div class="console-message info">💡 Click 'Connect to Sphero' to start</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let commands = [];
        let connected = false;
        
        // Initialize WebSocket
        function initWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = function() {
                addConsoleMessage('info', '🔗 WebSocket connected');
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            };
            
            ws.onclose = function() {
                addConsoleMessage('error', '❌ WebSocket disconnected');
                setTimeout(initWebSocket, 3000);
            };
        }
        
        function handleWebSocketMessage(message) {
            const { type, data } = message;
            
            switch(type) {
                case 'info':
                    addConsoleMessage('info', data);
                    break;
                case 'success':
                    addConsoleMessage('success', data);
                    if (data.includes('Connected!')) {
                        connected = true;
                        updateConnectionStatus(true);
                    }
                    break;
                case 'error':
                    addConsoleMessage('error', data);
                    break;
                case 'result':
                    addConsoleMessage('result', data);
                    break;
                case 'commands_loaded':
                    commands = data.commands;
                    loadCommands();
                    addConsoleMessage('success', `✅ Loaded ${data.total} commands`);
                    break;
            }
        }
        
        function addConsoleMessage(type, message) {
            const console = document.getElementById('console');
            const div = document.createElement('div');
            div.className = `console-message ${type}`;
            div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            console.appendChild(div);
            console.scrollTop = console.scrollHeight;
        }
        
        function updateConnectionStatus(isConnected) {
            const status = document.getElementById('connectionStatus');
            const connectBtn = document.getElementById('connectBtn');
            const disconnectBtn = document.getElementById('disconnectBtn');
            
            if (isConnected) {
                status.className = 'status connected';
                status.textContent = '✅ Connected';
                connectBtn.disabled = true;
                disconnectBtn.disabled = false;
            } else {
                status.className = 'status disconnected';
                status.textContent = '❌ Disconnected';
                connectBtn.disabled = false;
                disconnectBtn.disabled = true;
            }
        }
        
        function loadCommands() {
            const container = document.getElementById('commandsContainer');
            const categoryFilter = document.getElementById('categoryFilter');
            
            // Load categories
            const categories = [...new Set(commands.map(cmd => cmd.category))].sort();
            categoryFilter.innerHTML = '<option value="">All Categories</option>';
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat;
                option.textContent = cat;
                categoryFilter.appendChild(option);
            });
            
            // Load commands
            renderCommands();
        }
        
        function renderCommands(filterCategory = '') {
            const container = document.getElementById('commandsContainer');
            const filteredCommands = filterCategory ? 
                commands.filter(cmd => cmd.category === filterCategory) : 
                commands;
            
            container.innerHTML = '';
            container.className = 'commands-grid';
            
            filteredCommands.forEach(cmd => {
                const card = document.createElement('div');
                card.className = 'command-card';
                card.onclick = () => executeCommand(cmd.name);
                
                card.innerHTML = `
                    <div class="command-name">${cmd.name}</div>
                    <div class="command-type ${cmd.type}">${cmd.type}</div>
                    <div class="command-doc">${cmd.doc.substring(0, 100)}${cmd.doc.length > 100 ? '...' : ''}</div>
                    ${cmd.type === 'method' ? '<input type="text" class="param-input" placeholder="Parameters (comma-separated)" onclick="event.stopPropagation()">' : ''}
                `;
                
                container.appendChild(card);
            });
        }
        
        function executeCommand(commandName, params = null) {
            if (!connected) {
                addConsoleMessage('error', '❌ Not connected to Sphero');
                return;
            }
            
            // Get parameters from input if not provided
            if (!params) {
                const card = event.target.closest('.command-card');
                const paramInput = card.querySelector('.param-input');
                if (paramInput && paramInput.value.trim()) {
                    params = paramInput.value.split(',').map(p => p.trim());
                }
            }
            
            ws.send(JSON.stringify({
                action: 'execute_command',
                command: commandName,
                params: params
            }));
        }
        
        function quickTest(category, command, params) {
            if (!connected) {
                addConsoleMessage('error', '❌ Not connected to Sphero');
                return;
            }
            
            ws.send(JSON.stringify({
                action: 'execute_command',
                command: command,
                params: params
            }));
        }
        
        // Event listeners
        document.getElementById('connectBtn').onclick = function() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'connect' }));
            }
        };
        
        document.getElementById('disconnectBtn').onclick = function() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'disconnect' }));
            }
            connected = false;
            updateConnectionStatus(false);
        };
        
        document.getElementById('clearConsoleBtn').onclick = function() {
            document.getElementById('console').innerHTML = '';
        };
        
        document.getElementById('categoryFilter').onchange = function() {
            renderCommands(this.value);
        };
        
        // Initialize
        initWebSocket();
    </script>
</body>
</html>
"""

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    tester.websocket = websocket
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get('action')
            
            if action == 'connect':
                success = await tester.connect_sphero()
                if success:
                    await tester.cache_commands()
            elif action == 'disconnect':
                tester.disconnect()
                await tester.send_message("info", "👋 Disconnected from Sphero")
            elif action == 'execute_command':
                command = data.get('command')
                params = data.get('params')
                await tester.execute_command(command, params)
                
    except WebSocketDisconnect:
        tester.websocket = None

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 SPHERO WEB TESTER STARTING")
    print("="*60)
    print("\n🌐 Open your browser to: http://localhost:8081")
    print("💡 This will give you a beautiful UI to test all Sphero commands!")
    print("\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8081)