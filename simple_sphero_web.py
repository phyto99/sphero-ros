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
        self.edu_commands = []
        self.raw_commands = []
        self.led_states = {'back_led': False, 'front_led': False, 'main_led': False}
        
        # EDU API command definitions with safe defaults
        self.edu_api_specs = {
            'set_back_led': {'params': ['Color'], 'safe_defaults': [Color(255, 0, 0)]},
            'set_front_led': {'params': ['Color'], 'safe_defaults': [Color(0, 255, 0)]},
            'set_main_led': {'params': ['Color'], 'safe_defaults': [Color(0, 0, 255)]},
            'spin': {'params': ['degrees', 'speed'], 'safe_defaults': [360, 1]},
            'roll': {'params': ['heading', 'speed', 'duration'], 'safe_defaults': [0, 50, 1]},
            'get_heading': {'params': [], 'safe_defaults': []},
            'get_acceleration': {'params': [], 'safe_defaults': []},
            'get_gyroscope': {'params': [], 'safe_defaults': []},
            'scroll_matrix_text': {'params': ['text', 'fps', 'wait'], 'safe_defaults': ['HI', 10, True]},
            'set_matrix_character': {'params': ['char', 'Color'], 'safe_defaults': ['A', Color(0, 255, 255)]},
            'clear_matrix': {'params': [], 'safe_defaults': []},
            'set_stabilization': {'params': ['enabled'], 'safe_defaults': [True]},
            # Note: set_matrix_pixel and set_matrix_line don't exist in EDU API - remove them
            'set_matrix_fill': {'params': ['x1', 'y1', 'x2', 'y2', 'color'], 'safe_defaults': [0, 0, 7, 7, Color(0, 255, 0)]},
            # Note: draw_matrix_text doesn't exist in EDU API - remove it
        }
        
        # RAW command auto-fix definitions with comprehensive LED/Matrix commands
        self.raw_command_specs = {
            # LED Control Commands
            'set_all_leds_with_8_bit_mask': {'params': ['mask', 'values'], 'safe_defaults': [255, [255, 0, 0, 255, 255, 0, 0, 255]]},
            'set_led': {'params': ['led_id', 'r', 'g', 'b', 'brightness'], 'safe_defaults': [0, 255, 0, 0, 255]},
            'set_rgb_led_output': {'params': ['r', 'g', 'b'], 'safe_defaults': [255, 0, 0]},
            'set_back_led_output': {'params': ['brightness'], 'safe_defaults': [255]},
            'set_front_led_output': {'params': ['brightness'], 'safe_defaults': [255]},
            
            # Matrix/Display Commands  
            'draw_compressed_frame_player_fill': {'params': ['r', 'g', 'b'], 'safe_defaults': [255, 0, 0]},
            'draw_compressed_frame_player_line': {'params': ['x1', 'y1', 'x2', 'y2', 'r', 'g', 'b'], 'safe_defaults': [0, 0, 7, 7, 0, 255, 0]},
            'draw_compressed_frame_player_pixel': {'params': ['x', 'y', 'r', 'g', 'b'], 'safe_defaults': [4, 4, 0, 0, 255]},
            'set_compressed_frame_player_one_color': {'params': ['r', 'g', 'b'], 'safe_defaults': [255, 255, 0]},
            'assign_compressed_frame_player_frames_to_animation': {'params': ['animation_id', 'i_arr'], 'safe_defaults': [1, [0]]},
            'start_compressed_frame_player_animation': {'params': ['animation_id'], 'safe_defaults': [1]},
            'stop_compressed_frame_player_animation': {'params': [], 'safe_defaults': []},
            
            # Matrix Text/Character Commands
            'set_character_matrix_display_fill': {'params': ['r', 'g', 'b'], 'safe_defaults': [255, 0, 255]},
            'set_character_matrix_display_pixel': {'params': ['x', 'y', 'r', 'g', 'b'], 'safe_defaults': [4, 4, 255, 255, 255]},
            'set_character_matrix_display_line': {'params': ['x1', 'y1', 'x2', 'y2', 'r', 'g', 'b'], 'safe_defaults': [0, 0, 7, 7, 255, 0, 0]},
            'clear_character_matrix_display': {'params': [], 'safe_defaults': []},
            
            # Advanced LED Commands
            'set_all_leds': {'params': ['led_mask', 'r', 'g', 'b'], 'safe_defaults': [255, 255, 0, 0]},
            'set_user_led_color': {'params': ['r', 'g', 'b'], 'safe_defaults': [0, 255, 0]},
        }
        
        # Matrix/LED workaround attempts using raw commands
        self.matrix_workarounds = [
            'set_all_leds_with_8_bit_mask',
            'draw_compressed_frame_player_fill',
            'draw_compressed_frame_player_line',
            'set_compressed_frame_player_one_color',
            'assign_compressed_frame_player_frames_to_animation',
            'LEDs'  # Direct LED object access
        ]
    
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
        """Cache EDU and raw commands separately"""
        # EDU API commands
        self.edu_commands = []
        if self.api:
            for cmd_name, spec in self.edu_api_specs.items():
                if hasattr(self.api, cmd_name):
                    self.edu_commands.append({
                        'name': cmd_name,
                        'type': 'edu_method',
                        'params': spec['params'],
                        'defaults': spec['safe_defaults'],
                        'category': self.categorize_command(cmd_name),
                        'working': cmd_name in ['set_back_led', 'set_front_led', 'spin', 'roll', 'get_heading']
                    })
        
        # Raw toy commands
        self.raw_commands = []
        if self.toy:
            attrs = [a for a in dir(self.toy) if not a.startswith('_')]
            for attr in attrs:
                try:
                    obj = getattr(self.toy, attr)
                    # Skip if this is covered by EDU API
                    is_edu_duplicate = attr in self.edu_api_specs
                    
                    self.raw_commands.append({
                        'name': attr,
                        'type': 'raw_method' if callable(obj) else 'raw_property',
                        'category': self.categorize_command(attr),
                        'is_workaround': attr in self.matrix_workarounds,
                        'edu_duplicate': is_edu_duplicate
                    })
                except:
                    pass
        
        self.raw_commands = sorted(self.raw_commands, key=lambda x: (x['category'], x['name']))
    
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
    
    def execute_command(self, command_name: str, params: List[Any] = None, force_raw: bool = False):
        """Intelligent command execution with auto-solving"""
        if not self.connected:
            return False, "❌ Not connected"
        
        # Convert parameters
        converted_params = self._convert_params(params) if params else []
        
        # EDU API commands (try first with intelligent auto-fixing)
        if not force_raw and command_name in self.edu_api_specs:
            return self._execute_edu_command(command_name, converted_params)
        
        # Raw toy commands (for experimentation and workarounds)
        return self._execute_raw_command(command_name, converted_params)
    
    def _convert_params(self, params):
        """Smart parameter conversion"""
        converted = []
        for param in params:
            if isinstance(param, str) and param.strip():
                # RGB color detection
                if ',' in param and len(param.split(',')) == 3:
                    try:
                        rgb = [int(x.strip()) for x in param.split(',')]
                        converted.append(Color(*rgb))
                        continue
                    except:
                        pass
                # Number detection
                try:
                    converted.append(float(param) if '.' in param else int(param))
                except ValueError:
                    converted.append(param)
            else:
                converted.append(param)
        return converted
    
    def _execute_edu_command(self, command_name: str, params: List[Any]):
        """Execute EDU API command with intelligent auto-fixing"""
        if not self.api:
            return False, f"❌ No EDU API connection"
            
        if not hasattr(self.api, command_name):
            return False, f"❌ EDU API doesn't have '{command_name}' command"
        
        if command_name not in self.edu_api_specs:
            return False, f"❌ '{command_name}' not in command specs - may not be supported"
        
        spec = self.edu_api_specs[command_name]
        api_obj = getattr(self.api, command_name)
        
        if api_obj is None:
            return False, f"❌ '{command_name}' exists but is None - not available on this Sphero model"
        
        if not callable(api_obj):
            return True, f"📊 EDU {command_name} = {api_obj}"
        
        # Try with provided parameters first
        if params:
            try:
                result = api_obj(*params)
                return True, f"✅ EDU {command_name}({self._format_params(params)}) → {self._format_result(result)}"
            except Exception as e:
                # Auto-fix with safe defaults
                if "missing" in str(e) and "required" in str(e):
                    return self._auto_fix_edu_command(command_name, params, api_obj, spec, str(e))
        
        # Try with safe defaults
        try:
            safe_params = spec['safe_defaults']
            result = api_obj(*safe_params)
            return True, f"✅ EDU {command_name}({self._format_params(safe_params)}) → SAFE DEFAULTS → {self._format_result(result)}"
        except Exception as e:
            return False, f"❌ EDU {command_name} failed: {e}"
    
    def _auto_fix_edu_command(self, command_name: str, params: List[Any], api_obj, spec, error: str):
        """Intelligent auto-fixing for EDU commands"""
        safe_defaults = spec['safe_defaults']
        
        # Smart parameter completion based on what's provided
        fixed_params = self._complete_missing_params(command_name, params, safe_defaults, error)
        
        try:
            result = api_obj(*fixed_params)
            return True, f"✅ EDU {command_name}({self._format_params(fixed_params)}) → AUTO-FIXED → {self._format_result(result)}"
        except Exception as e2:
            return False, f"❌ EDU {command_name} auto-fix failed: {e2}"
    
    def _complete_missing_params(self, command_name: str, provided_params: List[Any], safe_defaults: List[Any], error: str):
        """Intelligently complete missing parameters"""
        if not provided_params:
            return safe_defaults
        
        # Command-specific parameter completion
        if "scroll_matrix_text" in command_name:
            # scroll_matrix_text(text, fps, wait)
            if len(provided_params) == 1:
                return [provided_params[0], 10, True]  # text + safe fps + wait
            elif len(provided_params) == 2:
                return [provided_params[0], provided_params[1], True]  # text + fps + safe wait
            
        elif "set_matrix_fill" in command_name:
            # set_matrix_fill(x1, y1, x2, y2, color)
            if len(provided_params) == 1:
                # If only color provided, fill entire matrix
                return [0, 0, 7, 7, provided_params[0]]  # full matrix + provided color
            elif len(provided_params) == 4:
                # If coordinates provided, add safe color
                return provided_params + [Color(0, 255, 0)]  # coordinates + safe color
            
        elif "roll" in command_name:
            # roll(heading, speed, duration)
            if len(provided_params) == 1:
                return [provided_params[0], 50, 1]  # heading + safe speed + duration
            elif len(provided_params) == 2:
                return [provided_params[0], provided_params[1], 1]  # heading + speed + safe duration
                
        elif "spin" in command_name:
            # spin(degrees, speed)
            if len(provided_params) == 1:
                return [provided_params[0], 1]  # degrees + safe speed
        
        # Default: use safe defaults if we can't intelligently complete
        return safe_defaults
    
    def _execute_raw_command(self, command_name: str, params: List[Any]):
        """Execute raw toy command with auto-fixing"""
        if not self.toy:
            return False, f"❌ No raw toy access"
        
        try:
            obj = getattr(self.toy, command_name)
            
            if callable(obj):
                result = obj(*params) if params else obj()
                return True, f"✅ RAW {command_name}({self._format_params(params)}) → {self._format_result(result)}"
            else:
                return True, f"📊 RAW {command_name} = {obj}"
                
        except Exception as e:
            # Try auto-fixing for missing parameters
            if "missing" in str(e) and "required" in str(e) and command_name in self.raw_command_specs:
                return self._auto_fix_raw_command(command_name, params, obj, e)
            return False, f"❌ RAW {command_name} failed: {e}"
    
    def _auto_fix_raw_command(self, command_name: str, params: List[Any], obj, error: Exception):
        """Auto-fix raw commands with missing parameters"""
        if command_name not in self.raw_command_specs:
            return False, f"❌ RAW {command_name} not in auto-fix specs"
            
        spec = self.raw_command_specs[command_name]
        safe_defaults = spec['safe_defaults']
        
        # Intelligent parameter completion based on command type
        fixed_params = self._complete_raw_params(command_name, params, safe_defaults)
        
        try:
            result = obj(*fixed_params)
            return True, f"✅ RAW {command_name}({self._format_params(fixed_params)}) → AUTO-FIXED → {self._format_result(result)}"
        except Exception as e2:
            return False, f"❌ RAW {command_name} auto-fix failed: {e2}"
    
    def _complete_raw_params(self, command_name: str, provided_params: List[Any], safe_defaults: List[Any]):
        """Intelligently complete RAW command parameters"""
        if not provided_params:
            return safe_defaults
        
        # LED Commands
        if 'set_led' == command_name:
            # set_led(led_id, r, g, b, brightness)
            if len(provided_params) == 1:
                return [provided_params[0], 255, 0, 0, 255]  # led_id + red color + full brightness
            elif len(provided_params) == 4:
                return provided_params + [255]  # add full brightness
                
        elif 'set_all_leds_with_8_bit_mask' == command_name:
            # set_all_leds_with_8_bit_mask(mask, values)
            if len(provided_params) == 1:
                return [provided_params[0], [255, 0, 0, 255, 255, 0, 0, 255]]  # mask + safe LED pattern
                
        elif 'draw_compressed_frame_player_line' == command_name:
            # draw_compressed_frame_player_line(x1, y1, x2, y2, r, g, b)
            if len(provided_params) == 4:
                return provided_params + [0, 255, 0]  # coordinates + green color
            elif len(provided_params) == 5:
                return provided_params + [255, 0]  # add g, b components
            elif len(provided_params) == 6:
                return provided_params + [0]  # add b component
                
        elif 'draw_compressed_frame_player_pixel' == command_name:
            # draw_compressed_frame_player_pixel(x, y, r, g, b)
            if len(provided_params) == 2:
                return provided_params + [0, 0, 255]  # x, y + blue color
            elif len(provided_params) == 3:
                return provided_params + [0, 255]  # add g, b components
            elif len(provided_params) == 4:
                return provided_params + [255]  # add b component
                
        elif 'assign_compressed_frame_player_frames_to_animation' == command_name:
            # assign_compressed_frame_player_frames_to_animation(animation_id, i_arr)
            if len(provided_params) == 1:
                return [provided_params[0], [0]]  # animation_id + safe frame array
        
        # Default: fill missing parameters with safe defaults
        needed_params = len(safe_defaults) - len(provided_params)
        if needed_params > 0:
            return provided_params + safe_defaults[-needed_params:]
        
        return provided_params
    
    def test_raw_command_discovery(self, command_name: str):
        """Discover RAW command parameters through safe testing"""
        if not self.toy:
            return False, "❌ No raw toy access for discovery"
        
        if not hasattr(self.toy, command_name):
            return False, f"❌ RAW command '{command_name}' not found"
        
        obj = getattr(self.toy, command_name)
        if not callable(obj):
            return True, f"📊 RAW {command_name} = {obj} (not callable)"
        
        # Try to get function signature information
        import inspect
        try:
            sig = inspect.signature(obj)
            param_names = list(sig.parameters.keys())
            param_count = len(param_names)
            
            result_parts = [f"🔍 RAW {command_name} discovery:"]
            result_parts.append(f"   Parameters: {param_count} → {param_names}")
            
            # Try safe test calls based on parameter patterns
            if command_name in self.raw_command_specs:
                safe_defaults = self.raw_command_specs[command_name]['safe_defaults']
                try:
                    result = obj(*safe_defaults)
                    result_parts.append(f"   ✅ Test call successful → {self._format_result(result)}")
                    result_parts.append(f"   Safe params: {self._format_params(safe_defaults)}")
                except Exception as e:
                    result_parts.append(f"   ⚠️ Test call failed: {e}")
            else:
                result_parts.append(f"   ⚠️ No safe defaults defined for testing")
            
            return True, "\n".join(result_parts)
            
        except Exception as e:
            return False, f"❌ Discovery failed: {e}"
    
    def _format_params(self, params):
        """Format parameters for display"""
        if not params:
            return ""
        formatted = []
        for p in params:
            if isinstance(p, Color):
                formatted.append(f"RGB({p.r},{p.g},{p.b})")
            else:
                formatted.append(str(p))
        return ", ".join(formatted)
    
    def _format_result(self, result):
        """Format result for display"""
        return "OK" if result is None else str(result)
    
    def test_connection(self):
        """Test if Sphero is actually responding"""
        if not self.connected or not self.api:
            return False, "Not connected"
        
        try:
            # Try to get heading - this should work if connected
            heading = self.api.get_heading()
            return True, f"✅ Sphero responding - Heading: {heading}°"
        except Exception as e:
            return False, f"❌ Sphero not responding: {e}"
    
    def get_matrix_workarounds(self):
        """Get potential matrix/LED workaround commands"""
        workarounds = []
        if self.toy:
            for cmd in self.matrix_workarounds:
                if hasattr(self.toy, cmd):
                    obj = getattr(self.toy, cmd)
                    workarounds.append({
                        'name': cmd,
                        'type': 'method' if callable(obj) else 'object',
                        'description': f"Potential matrix/LED workaround"
                    })
        return workarounds
    
    def disconnect(self, force=False):
        """Disconnect with optional force mode"""
        messages = []
        
        if force:
            messages.append("🔥 FORCE DISCONNECT - Clearing all connections")
        
        # Try to turn off LEDs before disconnecting
        if self.api:
            try:
                messages.append("🔄 Turning off LEDs before disconnect...")
                self.api.set_back_led(Color(0, 0, 0))
                self.api.set_front_led(Color(0, 0, 0))
                self.api.set_main_led(Color(0, 0, 0))
                messages.append("✅ LEDs turned off")
            except Exception as e:
                messages.append(f"⚠️ LED cleanup error: {e}")
        
        # Disconnect API with proper cleanup
        if self.api:
            try:
                # Try to close the connection properly
                if hasattr(self.api, '_toy') and hasattr(self.api._toy, 'close'):
                    self.api._toy.close()
                    messages.append("✅ Toy connection closed")
                
                # Exit the API context
                self.api.__exit__(None, None, None)
                messages.append("✅ API context exited")
                
            except Exception as e:
                messages.append(f"⚠️ API disconnect error: {e}")
            finally:
                self.api = None
                messages.append("✅ API reference cleared")
        
        # Clear toy reference
        if self.toy:
            try:
                # Try to close toy connection if it has a close method
                if hasattr(self.toy, 'close'):
                    self.toy.close()
                    messages.append("✅ Direct toy connection closed")
            except Exception as e:
                messages.append(f"⚠️ Toy close error: {e}")
            finally:
                self.toy = None
                messages.append("✅ Toy reference cleared")
        
        # Reset all states
        self.led_states = {'back_led': False, 'front_led': False, 'main_led': False}
        self.connected = False
        
        if force:
            messages.append("🔥 AGGRESSIVE DISCONNECT COMPLETE")
            messages.append("💡 Sphero should now be available for new connections")
        else:
            messages.append("👋 Clean disconnect complete")
        
        return messages

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
    <title>Sphero Bolt Command Center</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            background: #0d1117;
            color: #c9d1d9;
            font-size: 12px;
            line-height: 1.3;
        }
        
        .container { max-width: 1800px; margin: 0 auto; padding: 8px; }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #21262d;
            margin-bottom: 8px;
        }
        
        .header h1 { font-size: 16px; font-weight: 600; color: #f0f6fc; }
        
        .status-bar { display: flex; gap: 8px; align-items: center; font-size: 11px; }
        
        .status {
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: 500;
        }
        
        .status.connected { background: #238636; color: #fff; }
        .status.disconnected { background: #da3633; color: #fff; }
        
        .btn {
            padding: 4px 12px;
            border: 1px solid #30363d;
            border-radius: 3px;
            background: #21262d;
            color: #c9d1d9;
            cursor: pointer;
            font-size: 11px;
            transition: all 0.1s;
        }
        
        .btn:hover { background: #30363d; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-primary { background: #238636; border-color: #238636; }
        .btn-danger { background: #da3633; border-color: #da3633; }
        
        .main-grid {
            display: grid;
            grid-template-columns: 280px 1fr 350px;
            gap: 8px;
            height: calc(100vh - 60px);
        }
        
        .panel {
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .panel-header {
            padding: 6px 12px;
            background: #21262d;
            border-bottom: 1px solid #30363d;
            font-weight: 600;
            font-size: 11px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .panel-content {
            height: calc(100% - 29px);
            overflow-y: auto;
        }
        
        .section {
            border-bottom: 1px solid #21262d;
        }
        
        .section-header {
            padding: 6px 12px;
            background: #0d1117;
            font-size: 10px;
            font-weight: 600;
            color: #7d8590;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .controls-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4px;
            padding: 8px;
        }
        
        .control-btn {
            padding: 8px 6px;
            border: 1px solid #30363d;
            border-radius: 3px;
            background: #21262d;
            color: #c9d1d9;
            cursor: pointer;
            font-size: 10px;
            text-align: center;
            transition: all 0.1s;
        }
        
        .control-btn:hover { background: #30363d; }
        .control-btn.active { border-color: #238636; background: #0d4a1a; }
        
        .commands-container {
            padding: 4px;
        }
        
        .command-section {
            margin-bottom: 8px;
        }
        
        .command-section-title {
            padding: 4px 8px;
            background: #0d1117;
            font-size: 10px;
            font-weight: 600;
            color: #58a6ff;
            border-bottom: 1px solid #21262d;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .command-section-title:hover { background: #161b22; }
        
        .command-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 2px;
            padding: 4px;
            background: #0d1117;
        }
        
        .cmd {
            padding: 4px 6px;
            border: 1px solid #21262d;
            border-radius: 2px;
            background: #161b22;
            cursor: pointer;
            font-size: 9px;
            transition: all 0.1s;
            position: relative;
        }
        
        .cmd:hover { background: #21262d; border-color: #30363d; }
        
        .cmd.edu { border-left: 3px solid #238636; }
        .cmd.raw { border-left: 3px solid #f85149; }
        .cmd.workaround { border-left: 3px solid #d29922; }
        .cmd.working { background: #0d4a1a; }
        .cmd.duplicate { opacity: 0.5; }
        
        .cmd-name {
            font-weight: 500;
            color: #c9d1d9;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .cmd-actions {
            display: flex;
            gap: 2px;
            margin-top: 2px;
        }
        
        .mini-btn {
            padding: 1px 4px;
            font-size: 7px;
            border: 1px solid #30363d;
            background: #21262d;
            color: #c9d1d9;
            border-radius: 2px;
            cursor: pointer;
            transition: all 0.1s;
        }
        
        .mini-btn:hover {
            background: #30363d;
            border-color: #484f58;
        }
        
        .mini-btn.discover {
            background: #0969da;
            border-color: #1f6feb;
        }
        
        .mini-btn.discover:hover {
            background: #1f6feb;
        }
        
        .cmd-meta {
            font-size: 8px;
            color: #7d8590;
            margin-top: 1px;
        }
        
        .console {
            background: #0d1117;
            color: #7d8590;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 10px;
            line-height: 1.2;
            height: 100%;
            overflow-y: auto;
            padding: 8px;
        }
        
        .console-line {
            margin-bottom: 1px;
            word-break: break-all;
        }
        
        .console-line.success { color: #238636; }
        .console-line.error { color: #f85149; }
        .console-line.info { color: #58a6ff; }
        .console-line.warning { color: #d29922; }
        
        .filter-bar {
            padding: 6px 8px;
            background: #0d1117;
            border-bottom: 1px solid #21262d;
            display: flex;
            gap: 4px;
            align-items: center;
        }
        
        .filter-btn {
            padding: 2px 6px;
            border: 1px solid #30363d;
            border-radius: 2px;
            background: #21262d;
            color: #7d8590;
            cursor: pointer;
            font-size: 9px;
            transition: all 0.1s;
        }
        
        .filter-btn:hover { background: #30363d; }
        .filter-btn.active { background: #58a6ff; color: #fff; }
        
        .stats { display: flex; gap: 12px; font-size: 10px; color: #7d8590; }
        .stat-value { color: #58a6ff; font-weight: 500; }
        
        .command-progress {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(13, 17, 23, 0.95);
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 20px;
            z-index: 1000;
            min-width: 300px;
            text-align: center;
            backdrop-filter: blur(4px);
        }
        
        .progress-bar {
            width: 100%;
            height: 4px;
            background: #21262d;
            border-radius: 2px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: #238636;
            width: 0%;
            transition: width 0.1s ease;
        }
        
        .command-name-display {
            font-weight: 600;
            color: #58a6ff;
            margin-bottom: 5px;
        }
        
        .command-params-display {
            font-size: 11px;
            color: #7d8590;
            font-family: monospace;
        }
        
        .param-input {
            width: 100%;
            padding: 2px 4px;
            margin-top: 2px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 2px;
            color: #c9d1d9;
            font-size: 9px;
        }
        
        .collapse-btn {
            background: none;
            border: none;
            color: #7d8590;
            cursor: pointer;
            font-size: 10px;
        }
        
        .section.collapsed .command-grid { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ Sphero Bolt Command Center</h1>
            <div class="status-bar">
                <div class="stats">
                    <div>EDU: <span id="eduCount" class="stat-value">0</span></div>
                    <div>RAW: <span id="rawCount" class="stat-value">0</span></div>
                    <div>Exec: <span id="execCount" class="stat-value">0</span></div>
                </div>
                <button id="connectBtn" class="btn btn-primary">Connect</button>
                <button id="disconnectBtn" class="btn btn-danger">Disconnect</button>
                <button id="forceDisconnectBtn" class="btn btn-danger">Force DC</button>
                <button id="testBtn" class="btn" style="background: #d29922; color: #fff; font-size: 10px; padding: 4px 8px;">Test</button>
                <div id="status" class="status disconnected">Disconnected</div>
            </div>
        </div>
        
        <div class="main-grid">
            <div class="panel">
                <div class="panel-header">🎛️ Quick Controls</div>
                <div class="panel-content">
                    <div class="section">
                        <div class="section-header">LEDs (EDU)</div>
                        <div class="controls-grid">
                            <div class="control-btn" id="backLedBtn" onclick="toggleLED('back_led')">Back</div>
                            <div class="control-btn" id="frontLedBtn" onclick="toggleLED('front_led')">Front</div>
                            <div class="control-btn" id="mainLedBtn" onclick="toggleLED('main_led')">Main</div>
                            <div class="control-btn" onclick="executeCommand('clear_matrix', [])">Clear</div>
                        </div>
                    </div>
                    <div class="section">
                        <div class="section-header">Movement (EDU)</div>
                        <div class="controls-grid">
                            <div class="control-btn" onclick="executeCommand('spin', ['360'])">Spin</div>
                            <div class="control-btn" onclick="executeCommand('roll', ['0'])">Roll</div>
                            <div class="control-btn" onclick="executeCommand('get_heading', [])">Heading</div>
                            <div class="control-btn" onclick="executeCommand('set_stabilization', ['false'])">Unstable</div>
                        </div>
                    </div>
                    <div class="section">
                        <div class="section-header">Matrix Workarounds (RAW)</div>
                        <div id="workarounds" class="controls-grid">
                            <div style="padding: 20px; text-align: center; color: #7d8590; font-size: 10px;">Connect to load</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    📋 Commands
                    <div class="filter-bar">
                        <div class="filter-btn active" id="filterAll" onclick="setFilter('all')">All</div>
                        <div class="filter-btn" id="filterEdu" onclick="setFilter('edu')">EDU</div>
                        <div class="filter-btn" id="filterRaw" onclick="setFilter('raw')">RAW</div>
                        <div class="filter-btn" id="filterWorkaround" onclick="setFilter('workaround')">Fix</div>
                    </div>
                </div>
                <div class="panel-content">
                    <div id="commands" class="commands-container">
                        <div style="text-align: center; padding: 40px; color: #7d8590;">
                            Connect to Sphero to load commands
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">📟 Console</div>
                <div class="panel-content" style="padding: 0;">
                    <div id="console" class="console">
                        <div class="console-line info">Sphero Bolt Command Center v2.0</div>
                        <div class="console-line">Ready for connection...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Command Progress Overlay -->
    <div id="commandProgress" class="command-progress" style="display: none;">
        <div class="command-name-display" id="progressCommandName">Executing Command...</div>
        <div class="command-params-display" id="progressCommandParams"></div>
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        <div style="font-size: 10px; color: #7d8590;">Estimated time: <span id="progressTime">1s</span></div>
    </div>

    <script>
        let ws = null;
        let eduCommands = [];
        let rawCommands = [];
        let workarounds = [];
        let connected = false;
        let execCount = 0;
        let ledStates = { back_led: false, front_led: false, main_led: false };
        let currentFilter = 'all';
        
        function initWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = function() {
                addConsoleMessage('WS connected', 'info');
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                handleMessage(message);
            };
            
            ws.onclose = function() {
                addConsoleMessage('WS disconnected', 'error');
                setTimeout(initWebSocket, 3000);
            };
        }
        
        function handleMessage(message) {
            const { type, data } = message;
            
            if (type === 'status') {
                const msgType = data.includes('✅') ? 'success' : data.includes('❌') ? 'error' : 
                              data.includes('⚠️') ? 'warning' : 'info';
                addConsoleMessage(data.replace(/[✅❌⚠️]/g, '').trim(), msgType);
                if (data.includes('CONNECTION SUCCESS')) {
                    connected = true;
                    updateStatus(true);
                }
            } else if (type === 'commands') {
                eduCommands = message.edu_commands || [];
                rawCommands = message.raw_commands || [];
                workarounds = message.workarounds || [];
                
                document.getElementById('eduCount').textContent = eduCommands.length;
                document.getElementById('rawCount').textContent = rawCommands.length;
                
                loadCommands();
                loadWorkarounds();
                addConsoleMessage(`Loaded ${eduCommands.length} EDU + ${rawCommands.length} RAW commands`, 'success');
            } else if (type === 'result') {
                const msgType = data.includes('✅') ? 'success' : data.includes('❌') ? 'error' : 'info';
                addConsoleMessage(data.replace(/[✅❌]/g, '').trim(), msgType);
                if (data.includes('✅')) {
                    execCount++;
                    document.getElementById('execCount').textContent = execCount;
                }
            }
        }
        
        function addConsoleMessage(message, type = 'info') {
            const console = document.getElementById('console');
            const div = document.createElement('div');
            div.className = `console-line ${type}`;
            div.textContent = `${new Date().toLocaleTimeString().slice(-8)} ${message}`;
            console.appendChild(div);
            console.scrollTop = console.scrollHeight;
            
            if (console.children.length > 500) {
                console.removeChild(console.firstChild);
            }
        }
        
        function updateStatus(isConnected) {
            const status = document.getElementById('status');
            const connectBtn = document.getElementById('connectBtn');
            const disconnectBtn = document.getElementById('disconnectBtn');
            const forceDisconnectBtn = document.getElementById('forceDisconnectBtn');
            
            // ROBUST STATE MANAGEMENT - Always sync with actual state
            connected = isConnected;
            
            if (isConnected) {
                status.className = 'status connected';
                status.textContent = 'Connected';
                connectBtn.disabled = true;
                disconnectBtn.disabled = false;
                forceDisconnectBtn.disabled = false;
            } else {
                status.className = 'status disconnected';
                status.textContent = 'Disconnected';
                connectBtn.disabled = false;
                disconnectBtn.disabled = false;  // Always allow disconnect
                forceDisconnectBtn.disabled = false;  // Always allow force disconnect
            }
        }
        
        function forceResetConnectionState() {
            // NUCLEAR OPTION - Reset everything to disconnected state
            connected = false;
            updateStatus(false);
            resetLEDStates();
            addConsoleMessage('Connection state force reset', 'warning');
        }
        
        function toggleLED(ledType) {
            if (!connected) {
                addConsoleMessage('Not connected', 'error');
                return;
            }
            
            // Fix button ID mapping - capitalize LED
            const btnId = ledType.replace('_led', 'Led') + 'Btn';
            const btn = document.getElementById(btnId);
            const isActive = btn.classList.contains('active');
            
            if (isActive) {
                // Turn OFF - send black color
                executeCommand(`set_${ledType}`, ['0,0,0']);
                btn.classList.remove('active');
                ledStates[ledType] = false;
                addConsoleMessage(`${ledType} OFF`, 'info');
            } else {
                // Turn ON - send color
                const colors = {
                    'back_led': '255,0,0',
                    'front_led': '0,255,0',
                    'main_led': '0,0,255'
                };
                executeCommand(`set_${ledType}`, [colors[ledType]]);
                btn.classList.add('active');
                ledStates[ledType] = true;
                addConsoleMessage(`${ledType} ON`, 'info');
            }
        }
        
        function loadWorkarounds() {
            const container = document.getElementById('workarounds');
            container.innerHTML = '';
            
            workarounds.forEach(cmd => {
                const div = document.createElement('div');
                div.className = 'control-btn';
                div.onclick = () => executeCommand(cmd.name, [], true);
                div.textContent = cmd.name.slice(0, 8);
                div.title = cmd.name;
                container.appendChild(div);
            });
        }
        
        function setFilter(filter) {
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById('filter' + filter.charAt(0).toUpperCase() + filter.slice(1)).classList.add('active');
            loadCommands();
        }
        
        function loadCommands() {
            const container = document.getElementById('commands');
            container.innerHTML = '';
            
            // Group commands by category
            const categories = {};
            
            if (currentFilter === 'all' || currentFilter === 'edu') {
                eduCommands.forEach(cmd => {
                    if (!categories[cmd.category]) categories[cmd.category] = { edu: [], raw: [] };
                    categories[cmd.category].edu.push(cmd);
                });
            }
            
            if (currentFilter === 'all' || currentFilter === 'raw') {
                rawCommands.forEach(cmd => {
                    if (currentFilter === 'workaround' && !cmd.is_workaround) return;
                    if (!categories[cmd.category]) categories[cmd.category] = { edu: [], raw: [] };
                    categories[cmd.category].raw.push(cmd);
                });
            }
            
            // Render categories
            Object.keys(categories).sort().forEach(category => {
                const section = document.createElement('div');
                section.className = 'command-section';
                
                const title = document.createElement('div');
                title.className = 'command-section-title';
                title.innerHTML = `${category} <span class="collapse-btn">−</span>`;
                title.onclick = () => toggleSection(section);
                section.appendChild(title);
                
                const grid = document.createElement('div');
                grid.className = 'command-grid';
                
                // Add EDU commands
                categories[category].edu.forEach(cmd => {
                    const div = document.createElement('div');
                    div.className = `cmd edu ${cmd.working ? 'working' : ''}`;
                    div.onclick = () => executeCommand(cmd.name);
                    div.innerHTML = `
                        <div class="cmd-name">${cmd.name}</div>
                        <div class="cmd-meta">EDU • ${cmd.params.length}p</div>
                    `;
                    grid.appendChild(div);
                });
                
                // Add RAW commands (mark duplicates)
                categories[category].raw.forEach(cmd => {
                    const div = document.createElement('div');
                    div.className = `cmd raw ${cmd.is_workaround ? 'workaround' : ''} ${cmd.edu_duplicate ? 'duplicate' : ''}`;
                    
                    // Add discovery button for LED/Matrix commands
                    const isLedMatrix = cmd.name.includes('led') || cmd.name.includes('matrix') || cmd.name.includes('compressed_frame');
                    
                    div.innerHTML = `
                        <div class="cmd-name">${cmd.name}</div>
                        <div class="cmd-meta">RAW${cmd.is_workaround ? ' • FIX' : ''}${cmd.edu_duplicate ? ' • DUP' : ''}</div>
                        <div class="cmd-actions">
                            <button class="mini-btn" onclick="event.stopPropagation(); executeCommand('${cmd.name}', [], true)">Test</button>
                            ${isLedMatrix ? `<button class="mini-btn discover" onclick="event.stopPropagation(); discoverCommand('${cmd.name}')">🔍</button>` : ''}
                        </div>
                    `;
                    grid.appendChild(div);
                });
                
                section.appendChild(grid);
                container.appendChild(section);
            });
        }
        
        function toggleSection(section) {
            section.classList.toggle('collapsed');
            const btn = section.querySelector('.collapse-btn');
            btn.textContent = section.classList.contains('collapsed') ? '+' : '−';
        }
        
        function discoverCommand(commandName) {
            if (!connected) {
                addConsoleMessage('Not connected', 'error');
                return;
            }
            
            addConsoleMessage(`🔍 Discovering: ${commandName}`, 'info');
            
            ws.send(JSON.stringify({
                action: 'discover_command',
                command: commandName
            }));
        }
        
        function executeCommand(commandName, params = null, forceRaw = false) {
            if (!connected) {
                addConsoleMessage('Not connected', 'error');
                return;
            }
            
            if (!params && event) {
                const input = event.target.closest('.cmd')?.querySelector('.param-input');
                if (input && input.value.trim()) {
                    params = input.value.split(',').map(p => p.trim());
                }
            }
            
            // DEBUG: Log what we're sending
            addConsoleMessage(`🚀 Sending: ${commandName}(${params ? params.join(', ') : ''}) [${forceRaw ? 'RAW' : 'EDU'}]`, 'info');
            
            ws.send(JSON.stringify({
                action: 'execute_command',
                command: commandName,
                params: params,
                force_raw: forceRaw
            }));
        }
        
        document.getElementById('connectBtn').onclick = function() {
            // Simple connection progress in console only
            addConsoleMessage('🔄 Connecting to Sphero...', 'info');
            showConnectionProgress();
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'connect' }));
            }
        };
        
        document.getElementById('disconnectBtn').onclick = function() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'disconnect', force: false }));
            }
            connected = false;
            updateStatus(false);
            resetLEDStates();
        };
        
        document.getElementById('forceDisconnectBtn').onclick = function() {
            addConsoleMessage('🔥 FORCE DISCONNECT - Clearing ALL connections...', 'warning');
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'disconnect', force: true }));
            }
            // Always force reset state regardless of WebSocket
            connected = false;
            updateStatus(false);
            resetLEDStates();
        };
        
        document.getElementById('testBtn').onclick = function() {
            if (!connected) {
                addConsoleMessage('Not connected - cannot test', 'error');
                return;
            }
            addConsoleMessage('🧪 Testing Sphero connection...', 'info');
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'test_connection' }));
            }
        };
        
        function resetLEDStates() {
            Object.keys(ledStates).forEach(led => {
                ledStates[led] = false;
                const btn = document.getElementById(led.replace('_', '') + 'Btn');
                if (btn) btn.classList.remove('active');
            });
        }
        
        function showConnectionProgress() {
            // Simple console-based progress for connection only
            let dots = 0;
            const progressInterval = setInterval(() => {
                dots = (dots + 1) % 4;
                const dotString = '.'.repeat(dots) + ' '.repeat(3 - dots);
                addConsoleMessage(`⏳ Connecting${dotString}`, 'info');
            }, 500);
            
            // Stop progress after 5 seconds
            setTimeout(() => {
                clearInterval(progressInterval);
            }, 5000);
        }
        
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
                        'edu_commands': tester.edu_commands,
                        'raw_commands': tester.raw_commands,
                        'workarounds': tester.get_matrix_workarounds()
                    })
                    
            elif action == 'disconnect':
                force = data.get('force', False)
                messages = tester.disconnect(force)
                for message in messages:
                    await websocket.send_json({'type': 'status', 'data': message})
                
            elif action == 'test_connection':
                success, result = tester.test_connection()
                await websocket.send_json({'type': 'result', 'data': result})
                
            elif action == 'discover_command':
                command = data.get('command')
                success, result = tester.test_raw_command_discovery(command)
                await websocket.send_json({'type': 'result', 'data': result})
                
            elif action == 'execute_command':
                command = data.get('command')
                params = data.get('params')
                force_raw = data.get('force_raw', False)
                success, result = tester.execute_command(command, params, force_raw)
                await websocket.send_json({'type': 'result', 'data': result})
                
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    print("\n🚀 Simple Sphero Web Tester")
    print("🌐 Open: http://localhost:8082")
    print("💡 Uses EXACT api.py connection - no async complications!")
    
    uvicorn.run(app, host="0.0.0.0", port=8082)