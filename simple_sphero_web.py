"""
Simple Sphero Web Tester - Using EXACT api.py connection approach
"""

import time
import json
import asyncio
import threading
import concurrent.futures
from typing import Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.types import Color
import uvicorn

class SimpleSpheroTester:
    def __init__(self):
        self.toy = None
        self.api = None
        self.connected = False
        self.websocket = None
        self.commands_cache = []
        self.working_led_method = None
        self.working_matrix_method = None
    
    def wait_for_full_wake(self, wait_seconds=3):
        """Wait for full initialization - EXACT api.py method"""
        messages = []
        messages.append(f"⏳ Waiting {wait_seconds}s for initialization...")
        for i in range(wait_seconds):
            messages.append(f"   {'█' * (i+1)}{'░' * (wait_seconds-i-1)} {i+1}/{wait_seconds}s")
            time.sleep(1)
        messages.append("✅ Ready")
        return messages
    
    def connect_sphero(self, robot_id="SB-5925", scan_timeout=8, max_attempts=3):
        """Connect using EXACT api.py approach with full troubleshooting"""
        messages = []
        
        messages.append("=" * 60)
        messages.append("🔌 SPHERO BOLT - WEB TESTER CONNECTION")
        messages.append("=" * 60)
        messages.append("📋 Setup: Charger → Wait 2-3s → Remove → Wait 3s")
        messages.append("⚠️  Make sure Sphero is ready before connecting!")
        
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            messages.append(f"\n{'='*60}")
            messages.append(f"🔄 ATTEMPT #{attempt}/{max_attempts}")
            messages.append('='*60)
            
            messages.append(f"\n[1/3] 🔍 Scanning...")
            
            try:
                toys = scanner.find_toys(timeout=scan_timeout)
                
                if not toys:
                    messages.append("❌ No toys found")
                    if attempt < max_attempts:
                        messages.append("⏳ Waiting 5s before retry...")
                        time.sleep(5)
                        continue
                    return False, messages + ["❌ Failed to find any Sphero toys"]
                
                matching_toys = [t for t in toys if robot_id.upper() in t.name.upper()]
                
                if not matching_toys:
                    messages.append(f"❌ Found {len(toys)} toys but none match '{robot_id}'")
                    for toy in toys:
                        messages.append(f"   - {toy.name}")
                    if attempt < max_attempts:
                        messages.append("⏳ Waiting 5s before retry...")
                        time.sleep(5)
                        continue
                    return False, messages + [f"❌ No Sphero matching '{robot_id}' found"]
                
                self.toy = matching_toys[0]
                messages.append(f"✅ Found: {self.toy.name}")
                
            except Exception as e:
                messages.append(f"❌ Scan error: {e}")
                if attempt < max_attempts:
                    messages.append("⏳ Waiting 5s before retry...")
                    time.sleep(5)
                    continue
                return False, messages + [f"❌ Scan failed: {e}"]
            
            messages.append(f"\n[2/3] ⏳ Waiting for initialization...")
            wake_messages = self.wait_for_full_wake(3)
            messages.extend(wake_messages)
            
            messages.append(f"[3/3] 🔗 Connecting...")
            
            try:
                self.api = SpheroEduAPI(self.toy)
                self.api.__enter__()
                
                heading = self.api.get_heading()
                messages.append(f"   ✓ Connected (heading: {heading}°)")
                
                # Get low-level toy object for experimentation
                if hasattr(self.api, '_toy'):
                    self.toy = self.api._toy
                    messages.append(f"   ✓ Low-level toy access: {type(self.toy)}")
                else:
                    messages.append(f"   ⚠️  Using original toy object")
                
                self.connected = True
                
                messages.append("\n" + "="*60)
                messages.append("✅ CONNECTION SUCCESS!")
                messages.append("="*60)
                
                # Cache commands
                self.cache_commands()
                
                return True, messages
                
            except Exception as e:
                messages.append(f"❌ Connection failed: {e}")
                
                if self.api:
                    try:
                        self.api.__exit__(None, None, None)
                    except:
                        pass
                    self.api = None
                
                if attempt < max_attempts:
                    messages.append("⏳ Waiting 5s before retry...")
                    time.sleep(5)
                    continue
                return False, messages + [f"❌ All connection attempts failed"]
        
        return False, messages + ["❌ Failed after all attempts"]
    
    def cache_commands(self):
        """Cache all available commands"""
        if not self.toy:
            return
        
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
    
    def categorize_command(self, name: str) -> str:
        """Categorize commands"""
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
    
    def execute_command(self, command_name: str, params: List[Any] = None):
        """Execute a command - try API first for known working commands"""
        if not self.connected:
            return False, "❌ Not connected to Sphero"
        
        # Convert parameters first
        converted_params = []
        if params:
            for param in params:
                if isinstance(param, str) and param.strip():
                    try:
                        if '.' in param:
                            converted_params.append(float(param))
                        else:
                            converted_params.append(int(param))
                    except ValueError:
                        if ',' in param:
                            try:
                                rgb_values = [int(x.strip()) for x in param.split(',')]
                                if len(rgb_values) == 3:
                                    converted_params.append(Color(*rgb_values))
                                    continue
                            except:
                                pass
                        converted_params.append(param)
                else:
                    converted_params.append(param)
        
        # Known working commands - try API first
        api_commands = ['set_back_led', 'set_front_led', 'set_main_led', 'spin', 'roll', 
                       'get_heading', 'get_acceleration', 'get_gyroscope', 'scroll_matrix_text', 
                       'set_matrix_character', 'clear_matrix']
        
        if command_name in api_commands and self.api and hasattr(self.api, command_name):
            try:
                api_obj = getattr(self.api, command_name)
                if callable(api_obj):
                    if converted_params:
                        result = api_obj(*converted_params)
                    else:
                        result = api_obj()
                    return True, f"✅ API {command_name}() executed successfully. Result: {result}"
                else:
                    return True, f"API {command_name} = {api_obj}"
            except Exception as e:
                # If API fails, try low-level as fallback
                pass
        
        # Try low-level toy object (for experimentation)
        if self.toy:
            try:
                obj = getattr(self.toy, command_name)
                
                if callable(obj):
                    if converted_params:
                        result = obj(*converted_params)
                    else:
                        result = obj()
                    
                    return True, f"✅ Low-level {command_name}() executed successfully. Result: {result}"
                else:
                    return True, f"Low-level {command_name} = {obj}"
                    
            except Exception as e:
                # If both fail, try API as final fallback
                if self.api and hasattr(self.api, command_name):
                    try:
                        api_obj = getattr(self.api, command_name)
                        if callable(api_obj):
                            if converted_params:
                                result = api_obj(*converted_params)
                            else:
                                result = api_obj()
                            return True, f"✅ API fallback {command_name}() worked! Result: {result}"
                        else:
                            return True, f"API fallback {command_name} = {api_obj}"
                    except Exception as e2:
                        return False, f"❌ Both API and low-level failed. API: {e2}, Low-level: {e}"
                else:
                    return False, f"❌ Low-level failed: {e}"
        
        return False, f"❌ No toy object available"
    
    def disconnect(self):
        """Disconnect"""
        if self.connected and self.api:
            try:
                self.api.__exit__(None, None, None)
            except:
                pass
            self.api = None
            self.toy = None
            self.connected = False

# Global tester
tester = SimpleSpheroTester()

# FastAPI app
app = FastAPI(title="Simple Sphero Tester")

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Sphero Tester</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 1200px; margin: 0 auto; }
        .panel { background: white; padding: 20px; margin: 10px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn:hover { opacity: 0.8; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .status.connected { background: #d4edda; color: #155724; }
        .status.disconnected { background: #f8d7da; color: #721c24; }
        .console { background: #000; color: #0f0; padding: 15px; border-radius: 5px; height: 300px; overflow-y: auto; font-family: monospace; }
        .commands { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; max-height: 500px; overflow-y: auto; }
        .command { border: 1px solid #ddd; padding: 10px; border-radius: 5px; cursor: pointer; }
        .command:hover { background: #f8f9fa; }
        .command-name { font-weight: bold; color: #007bff; }
        .command-type { font-size: 12px; color: #666; }
        .param-input { width: 100%; padding: 5px; margin-top: 5px; border: 1px solid #ddd; border-radius: 3px; }
        select { padding: 8px; margin: 10px 0; border-radius: 5px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Simple Sphero Tester</h1>
        
        <div class="panel">
            <button id="connectBtn" class="btn btn-primary">🔌 Connect to Sphero</button>
            <button id="disconnectBtn" class="btn btn-danger" disabled>🔌 Disconnect</button>
            <div id="status" class="status disconnected">❌ Disconnected</div>
        </div>
        
        <div class="panel">
            <h3>⚡ Quick Tests (Working Commands)</h3>
            <button class="btn btn-success" onclick="quickTest('set_back_led', ['255,0,0'])">🔴 Red Back LED</button>
            <button class="btn btn-success" onclick="quickTest('set_front_led', ['0,255,0'])">🟢 Green Front LED</button>
            <button class="btn btn-success" onclick="quickTest('spin', ['360', '1'])">🌀 Spin 360°</button>
            <button class="btn btn-success" onclick="quickTest('roll', ['90', '0'])">➡️ Roll Forward</button>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div class="panel">
                <h3>🎮 Commands</h3>
                <select id="categoryFilter">
                    <option value="">All Categories</option>
                </select>
                <div id="commands" class="commands">
                    <p>Connect to Sphero to load commands...</p>
                </div>
            </div>
            
            <div class="panel">
                <h3>📟 Console</h3>
                <div id="console" class="console">
                    <div>🚀 Simple Sphero Tester Ready</div>
                    <div>💡 Click 'Connect to Sphero' to start</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let commands = [];
        let connected = false;
        
        function initWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = function() {
                addConsoleMessage('🔗 WebSocket connected');
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                handleMessage(message);
            };
            
            ws.onclose = function() {
                addConsoleMessage('❌ WebSocket disconnected');
                setTimeout(initWebSocket, 3000);
            };
        }
        
        function handleMessage(message) {
            const { type, data } = message;
            
            if (type === 'status') {
                addConsoleMessage(data);
                if (data.includes('Connected')) {
                    connected = true;
                    updateStatus(true);
                }
            } else if (type === 'commands') {
                commands = data;
                loadCommands();
                addConsoleMessage(`✅ Loaded ${data.length} commands`);
            } else if (type === 'result') {
                addConsoleMessage(data);
            }
        }
        
        function addConsoleMessage(message) {
            const console = document.getElementById('console');
            const div = document.createElement('div');
            div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            console.appendChild(div);
            console.scrollTop = console.scrollHeight;
        }
        
        function updateStatus(isConnected) {
            const status = document.getElementById('status');
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
            const container = document.getElementById('commands');
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
            
            renderCommands();
        }
        
        function renderCommands(filterCategory = '') {
            const container = document.getElementById('commands');
            const filteredCommands = filterCategory ? 
                commands.filter(cmd => cmd.category === filterCategory) : 
                commands;
            
            container.innerHTML = '';
            
            filteredCommands.forEach(cmd => {
                const div = document.createElement('div');
                div.className = 'command';
                div.onclick = () => executeCommand(cmd.name);
                
                div.innerHTML = `
                    <div class="command-name">${cmd.name}</div>
                    <div class="command-type">${cmd.type} - ${cmd.category}</div>
                    ${cmd.type === 'method' ? '<input type="text" class="param-input" placeholder="Parameters (comma-separated)" onclick="event.stopPropagation()">' : ''}
                `;
                
                container.appendChild(div);
            });
        }
        
        function executeCommand(commandName, params = null) {
            if (!connected) {
                addConsoleMessage('❌ Not connected to Sphero');
                return;
            }
            
            if (!params) {
                const card = event.target.closest('.command');
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
        
        function quickTest(command, params) {
            if (!connected) {
                addConsoleMessage('❌ Not connected to Sphero');
                return;
            }
            
            ws.send(JSON.stringify({
                action: 'execute_command',
                command: command,
                params: params
            }));
        }
        
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
            updateStatus(false);
        };
        
        document.getElementById('categoryFilter').onchange = function() {
            renderCommands(this.value);
        };
        
        initWebSocket();
    </script>
</body>
</html>
"""

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get('action')
            
            if action == 'connect':
                # Run connection in a separate thread to avoid event loop conflicts
                loop = asyncio.get_event_loop()
                
                def run_connection():
                    return tester.connect_sphero()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    success, messages = await loop.run_in_executor(executor, run_connection)
                
                # Send all connection messages
                for message in messages:
                    await websocket.send_json({'type': 'status', 'data': message})
                    await asyncio.sleep(0.1)  # Small delay for readability
                
                if success:
                    await websocket.send_json({
                        'type': 'commands', 
                        'data': tester.commands_cache
                    })
                    
            elif action == 'disconnect':
                tester.disconnect()
                await websocket.send_json({'type': 'status', 'data': '👋 Disconnected'})
                
            elif action == 'execute_command':
                command = data.get('command')
                params = data.get('params')
                success, result = tester.execute_command(command, params)
                await websocket.send_json({'type': 'result', 'data': result})
                
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    print("\n🚀 Simple Sphero Web Tester")
    print("🌐 Open: http://localhost:8082")
    print("💡 Uses EXACT api.py connection - no async complications!")
    
    uvicorn.run(app, host="0.0.0.0", port=8082)