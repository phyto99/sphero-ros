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
        
        # Active command tracking
        self.active_effects = {
            'animations': [],
            'leds': {},
            'matrix_effects': [],
            'movements': []
        }
        
        # Matrix display tracking
        self.matrix_state = [[{'r': 0, 'g': 0, 'b': 0} for _ in range(8)] for _ in range(8)]
        self.last_matrix_command = None
        self.matrix_tracking_enabled = True
        
        # Sphero health monitoring
        self.sphero_health = {
            'heading': 0,
            'battery_percentage': 0,
            'accelerometer': {'x': 0, 'y': 0, 'z': 0},
            'gyroscope': {'x': 0, 'y': 0, 'z': 0},
            'last_update': 0
        }
        self.gyro_stabilization_enabled = True
        
        # LED status tracking
        self.led_status = {
            'back_led': {'r': 0, 'g': 0, 'b': 0, 'active': False},
            'front_led': {'r': 0, 'g': 0, 'b': 0, 'active': False},
            'main_led': {'r': 0, 'g': 0, 'b': 0, 'active': False}
        }
        
        # Integrity validation
        self.last_verified_state = None
        self.state_verification_enabled = True
        self.command_execution_log = []
        
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
            'draw_compressed_frame_player_fill': {'params': ['x1', 'y1', 'x2', 'y2', 'r', 'g', 'b'], 'safe_defaults': [0, 0, 7, 7, 255, 0, 0]},
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
                
                # Reset display states on fresh connection
                self.reset_display_states()
                
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
        """Intelligent command execution with comprehensive validation"""
        if not self.connected:
            return False, "❌ Not connected"
        
        # Pre-execution integrity check
        if self.state_verification_enabled:
            integrity_passed, _ = self.verify_connection_integrity()
            if not integrity_passed:
                return False, "❌ Connection integrity check failed - please reconnect"
        
        # Convert parameters
        converted_params = self._convert_params(params) if params else []
        
        # Execute command
        if not force_raw and command_name in self.edu_api_specs:
            success, result = self._execute_edu_command(command_name, converted_params)
        else:
            success, result = self._execute_raw_command(command_name, converted_params)
        
        # Post-execution validation
        if self.state_verification_enabled:
            validation_report = self.validate_command_result(command_name, converted_params, result, success)
            
            # Add validation info to result if there are issues
            if validation_report['issues']:
                validation_summary = f" [Validation: {len(validation_report['issues'])} issues]"
                result = result + validation_summary if isinstance(result, str) else str(result) + validation_summary
        
        return success, result
    
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
                # Track active effects
                self._track_command_effect(command_name, params)
                # Update matrix state for matrix commands
                if 'matrix' in command_name.lower():
                    self.update_matrix_state(command_name, params)
                # Update LED status for LED commands
                if command_name in ['set_back_led', 'set_front_led', 'set_main_led'] and params:
                    self.update_led_status(command_name, params)
                return True, f"✅ EDU {command_name}({self._format_params(params)}) → {self._format_result(result)}"
            except Exception as e:
                # Auto-fix with safe defaults
                if "missing" in str(e) and "required" in str(e):
                    return self._auto_fix_edu_command(command_name, params, api_obj, spec, str(e))
        
        # Try with safe defaults
        try:
            safe_params = spec['safe_defaults']
            result = api_obj(*safe_params)
            # Track active effects
            self._track_command_effect(command_name, safe_params)
            # Update matrix state for matrix commands
            if 'matrix' in command_name.lower():
                self.update_matrix_state(command_name, safe_params)
            # Update LED status for LED commands
            if command_name in ['set_back_led', 'set_front_led', 'set_main_led'] and safe_params:
                self.update_led_status(command_name, safe_params)
            return True, f"✅ EDU {command_name}({self._format_params(safe_params)}) → SAFE DEFAULTS → {self._format_result(result)}"
        except Exception as e:
            return False, f"❌ EDU {command_name} failed: {e}"
    
    def _track_command_effect(self, command_name: str, params: List[Any]):
        """Track command effects for management"""
        # Determine effect type and track accordingly
        if 'led' in command_name.lower():
            # LED effects - track as persistent
            if any(isinstance(p, Color) and (p.r > 0 or p.g > 0 or p.b > 0) for p in params):
                self.track_active_effect(command_name, params, 'led')
            else:
                # LED turned off - remove from tracking
                if command_name in self.active_effects['leds']:
                    del self.active_effects['leds'][command_name]
        
        elif 'matrix' in command_name.lower() or 'scroll' in command_name.lower():
            # Matrix effects - track as temporary
            if command_name != 'clear_matrix':
                self.track_active_effect(command_name, params, 'matrix')
            else:
                # Matrix cleared - remove all matrix effects
                self.active_effects['matrix_effects'].clear()
        
        elif command_name in ['roll', 'spin'] and params:
            # Movement effects - track as temporary
            self.track_active_effect(command_name, params, 'movement')
    
    def _track_raw_command_effect(self, command_name: str, params: List[Any]):
        """Track RAW command effects for management"""
        # Matrix/Display effects
        if any(keyword in command_name.lower() for keyword in ['compressed_frame', 'matrix', 'character_matrix']):
            if 'clear' not in command_name.lower():
                self.track_active_effect(command_name, params, 'matrix')
            else:
                # Clear command - remove matrix effects
                self.active_effects['matrix_effects'].clear()
        
        # LED effects
        elif any(keyword in command_name.lower() for keyword in ['led', 'rgb']):
            # Check if LEDs are being turned on (non-zero values)
            has_color = False
            if params:
                # Look for non-zero RGB values
                for param in params:
                    if isinstance(param, (int, float)) and param > 0:
                        has_color = True
                        break
                    elif isinstance(param, list):
                        # Check for non-zero values in LED arrays
                        if any(v > 0 for v in param if isinstance(v, (int, float))):
                            has_color = True
                            break
            
            if has_color:
                self.track_active_effect(command_name, params, 'led')
            else:
                # LEDs turned off - remove from tracking
                if command_name in self.active_effects['leds']:
                    del self.active_effects['leds'][command_name]
        
        # Animation effects
        elif any(keyword in command_name.lower() for keyword in ['animation', 'start_compressed']):
            if 'stop' not in command_name.lower():
                self.track_active_effect(command_name, params, 'animation')
            else:
                # Stop animation - clear animations
                self.active_effects['animations'].clear()
    
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
                # Track RAW command effects
                self._track_raw_command_effect(command_name, params)
                # Update matrix state for matrix-related commands
                if (command_name.lower() in [
                    'draw_compressed_frame_player_fill',
                    'draw_compressed_frame_player_pixel', 
                    'draw_compressed_frame_player_line',
                    'set_compressed_frame_player_one_color',
                    'stop_compressed_frame_player_animation',
                    'set_character_matrix_display_fill',
                    'set_character_matrix_display_pixel',
                    'set_character_matrix_display_line',
                    'clear_character_matrix_display'
                ] or 'matrix' in command_name.lower()):
                    self.update_matrix_state(command_name, params)
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
            # Track RAW command effects
            self._track_raw_command_effect(command_name, fixed_params)
            # Update matrix state for matrix-related commands
            if (command_name.lower() in [
                'draw_compressed_frame_player_fill',
                'draw_compressed_frame_player_pixel', 
                'draw_compressed_frame_player_line',
                'set_compressed_frame_player_one_color',
                'stop_compressed_frame_player_animation',
                'set_character_matrix_display_fill',
                'set_character_matrix_display_pixel',
                'set_character_matrix_display_line',
                'clear_character_matrix_display'
            ] or 'matrix' in command_name.lower()):
                self.update_matrix_state(command_name, fixed_params)
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
                
        elif 'draw_compressed_frame_player_fill' == command_name:
            # draw_compressed_frame_player_fill(x1, y1, x2, y2, r, g, b)
            if len(provided_params) == 3:
                # If only RGB provided, fill entire matrix
                return [0, 0, 7, 7] + provided_params  # full matrix + provided RGB
            elif len(provided_params) == 4:
                # If coordinates provided, add safe RGB
                return provided_params + [255, 0, 0]  # coordinates + red color
            elif len(provided_params) == 5:
                return provided_params + [0, 0]  # add g, b components
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
    
    def track_active_effect(self, command_name: str, params: List[Any], effect_type: str):
        """Track active effects for management"""
        effect_id = f"{command_name}_{int(time.time() * 1000)}"
        
        effect_info = {
            'id': effect_id,
            'command': command_name,
            'params': params,
            'timestamp': time.time(),
            'type': effect_type
        }
        
        if effect_type == 'animation':
            self.active_effects['animations'].append(effect_info)
        elif effect_type == 'led':
            self.active_effects['leds'][command_name] = effect_info
        elif effect_type == 'matrix':
            self.active_effects['matrix_effects'].append(effect_info)
        elif effect_type == 'movement':
            self.active_effects['movements'].append(effect_info)
        
        return effect_id
    
    def get_active_effects(self):
        """Get all currently active effects"""
        total_effects = (
            len(self.active_effects['animations']) +
            len(self.active_effects['leds']) +
            len(self.active_effects['matrix_effects']) +
            len(self.active_effects['movements'])
        )
        
        return {
            'total': total_effects,
            'effects': self.active_effects,
            'summary': {
                'animations': len(self.active_effects['animations']),
                'leds': len(self.active_effects['leds']),
                'matrix': len(self.active_effects['matrix_effects']),
                'movements': len(self.active_effects['movements'])
            }
        }
    
    def stop_effect(self, effect_id: str):
        """Stop a specific effect by ID"""
        if not self.connected:
            return False, "❌ Not connected"
        
        # Find and remove the effect
        for category in self.active_effects:
            if category == 'leds':
                for cmd, effect in list(self.active_effects[category].items()):
                    if effect['id'] == effect_id:
                        # Turn off LED (try both EDU and RAW methods)
                        try:
                            # Try EDU API first
                            if 'led' in cmd and hasattr(self.api, cmd):
                                getattr(self.api, cmd)(Color(0, 0, 0))
                            # Try RAW commands
                            elif hasattr(self.toy, cmd):
                                if 'rgb' in cmd.lower():
                                    getattr(self.toy, cmd)(0, 0, 0)
                                elif 'led' in cmd.lower():
                                    getattr(self.toy, cmd)(0, [0, 0, 0, 0, 0, 0, 0, 0])
                            
                            del self.active_effects[category][cmd]
                            return True, f"✅ Stopped LED effect: {cmd}"
                        except Exception as e:
                            return False, f"❌ Failed to stop {cmd}: {e}"
            else:
                effects_list = self.active_effects[category]
                for i, effect in enumerate(effects_list):
                    if effect['id'] == effect_id:
                        # Stop animation/matrix effect
                        try:
                            if category == 'animations':
                                if hasattr(self.toy, 'stop_compressed_frame_player_animation'):
                                    self.toy.stop_compressed_frame_player_animation()
                            elif category == 'matrix_effects':
                                # Try multiple methods to clear matrix effects
                                if hasattr(self.api, 'clear_matrix'):
                                    self.api.clear_matrix()
                                if hasattr(self.toy, 'draw_compressed_frame_player_fill'):
                                    self.toy.draw_compressed_frame_player_fill(0, 0, 7, 7, 0, 0, 0)
                                if hasattr(self.toy, 'clear_character_matrix_display'):
                                    self.toy.clear_character_matrix_display()
                            
                            effects_list.pop(i)
                            return True, f"✅ Stopped {category} effect: {effect['command']}"
                        except Exception as e:
                            return False, f"❌ Failed to stop {effect['command']}: {e}"
        
        return False, f"❌ Effect {effect_id} not found"
    
    def update_matrix_state(self, command_name: str, params: List[Any]):
        """Track matrix state changes from commands"""
        if not self.matrix_tracking_enabled:
            return
        
        try:
            if command_name == 'clear_matrix':
                # Only clear matrix, not LEDs
                self.matrix_state = [[{'r': 0, 'g': 0, 'b': 0} for _ in range(8)] for _ in range(8)]
                
            # Detect when matrix is being cleared/turned off
            elif (command_name in ['draw_compressed_frame_player_fill', 'set_compressed_frame_player_one_color'] 
                  and len(params) >= 3 and int(params[0]) == 0 and int(params[1]) == 0 and int(params[2]) == 0):
                # All black = matrix off
                self.matrix_state = [[{'r': 0, 'g': 0, 'b': 0} for _ in range(8)] for _ in range(8)]
                
            elif command_name == 'set_matrix_character' and len(params) >= 2:
                char = str(params[0]) if params[0] else 'A'
                color = params[1] if hasattr(params[1], 'r') else type('Color', (), {'r': 255, 'g': 255, 'b': 255})()
                
                patterns = {
                    'A': [(1,0),(2,0),(3,0),(4,0),(5,0),(0,1),(0,2),(0,3),(0,4),(0,5),(6,1),(6,2),(6,3),(6,4),(6,5),(2,3)],
                    'X': [(0,0),(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(0,7),(1,6),(2,5),(3,4),(4,3),(5,2),(6,1),(7,0)],
                    'O': [(1,0),(2,0),(3,0),(4,0),(5,0),(0,1),(0,2),(0,3),(0,4),(0,5),(6,1),(6,2),(6,3),(6,4),(6,5),(1,6),(2,6),(3,6),(4,6),(5,6)]
                }
                
                self.matrix_state = [[{'r': 0, 'g': 0, 'b': 0} for _ in range(8)] for _ in range(8)]
                if char.upper() in patterns:
                    for x, y in patterns[char.upper()]:
                        if 0 <= x < 8 and 0 <= y < 8:
                            self.matrix_state[y][x] = {'r': color.r, 'g': color.g, 'b': color.b}
                
            elif command_name == 'draw_compressed_frame_player_fill' and len(params) >= 3:
                if len(params) >= 7:  # x1, y1, x2, y2, r, g, b format
                    r, g, b = params[4], params[5], params[6]
                else:  # r, g, b format
                    r, g, b = params[0], params[1], params[2]
                for y in range(8):
                    for x in range(8):
                        self.matrix_state[y][x] = {'r': int(r), 'g': int(g), 'b': int(b)}
                        
            elif command_name == 'set_compressed_frame_player_one_color' and len(params) >= 3:
                r, g, b = params[0], params[1], params[2]
                for y in range(8):
                    for x in range(8):
                        self.matrix_state[y][x] = {'r': int(r), 'g': int(g), 'b': int(b)}
                        
            elif command_name == 'draw_compressed_frame_player_pixel' and len(params) >= 5:
                x, y, r, g, b = params[0], params[1], params[2], params[3], params[4]
                if 0 <= x < 8 and 0 <= y < 8:
                    self.matrix_state[y][x] = {'r': int(r), 'g': int(g), 'b': int(b)}
                    
            elif command_name == 'draw_compressed_frame_player_line' and len(params) >= 7:
                x1, y1, x2, y2, r, g, b = params[0], params[1], params[2], params[3], params[4], params[5], params[6]
                dx = abs(x2 - x1)
                dy = abs(y2 - y1)
                sx = 1 if x1 < x2 else -1
                sy = 1 if y1 < y2 else -1
                err = dx - dy
                
                x, y = x1, y1
                while True:
                    if 0 <= x < 8 and 0 <= y < 8:
                        self.matrix_state[y][x] = {'r': int(r), 'g': int(g), 'b': int(b)}
                    if x == x2 and y == y2:
                        break
                    e2 = 2 * err
                    if e2 > -dy:
                        err -= dy
                        x += sx
                    if e2 < dx:
                        err += dx
                        y += sy
            
            # Detect stop/clear commands
            elif command_name in ['stop_compressed_frame_player_animation', 'clear_character_matrix_display']:
                self.matrix_state = [[{'r': 0, 'g': 0, 'b': 0} for _ in range(8)] for _ in range(8)]
            
            self.last_matrix_command = {
                'command': command_name,
                'params': params,
                'timestamp': time.time()
            }
            
        except Exception as e:
            pass
    
    def update_led_status(self, command_name: str, params: List[Any]):
        """Track LED status changes from commands"""
        try:
            if command_name in ['set_back_led', 'set_front_led', 'set_main_led'] and params:
                led_name = command_name  # Keep full name for mapping
                color = params[0] if params and hasattr(params[0], 'r') else None
                
                if color:
                    self.led_status[led_name] = {
                        'r': color.r,
                        'g': color.g, 
                        'b': color.b,
                        'active': color.r > 0 or color.g > 0 or color.b > 0
                    }
        except Exception as e:
            pass
    
    def get_matrix_display_data(self):
        """Get complete matrix display data"""
        return {
            'matrix': self.matrix_state,
            'current_heading': self.sphero_health.get('heading', 0),
            'gyro_enabled': self.gyro_stabilization_enabled,
            'led_status': self.led_status,
            'last_command': self.last_matrix_command,
            'tracking_enabled': self.matrix_tracking_enabled,
            'timestamp': time.time()
        }
    

    
    def get_live_sensor_data(self):
        """Get live sensor data"""
        if not self.connected or not self.api:
            return None
        
        sensor_data = {
            'timestamp': time.time(),
            'heading': None,
            'battery_percentage': None,
            'accelerometer': None,
            'gyroscope': None,
            'stabilization_enabled': self.gyro_stabilization_enabled
        }
        
        try:
            heading = self.api.get_heading()
            if heading is not None:
                sensor_data['heading'] = heading
                self.sphero_health['heading'] = heading
        except:
            pass
        
        try:
            if self.toy and hasattr(self.toy, 'get_battery_percentage'):
                battery = self.toy.get_battery_percentage()
                if battery is not None:
                    sensor_data['battery_percentage'] = battery
        except:
            pass
        
        try:
            if hasattr(self.api, 'get_acceleration'):
                accel = self.api.get_acceleration()
                if accel:
                    sensor_data['accelerometer'] = accel
        except:
            pass
        
        try:
            if hasattr(self.api, 'get_gyroscope'):
                gyro = self.api.get_gyroscope()
                if gyro:
                    sensor_data['gyroscope'] = gyro
        except:
            pass
        
        return sensor_data
    
    def toggle_gyro_stabilization(self):
        """Toggle gyroscope stabilization"""
        if not self.connected or not self.api:
            return False, "Not connected"
        
        try:
            self.gyro_stabilization_enabled = not self.gyro_stabilization_enabled
            self.api.set_stabilization(self.gyro_stabilization_enabled)
            status = "enabled" if self.gyro_stabilization_enabled else "disabled"
            return True, f"Gyroscope stabilization {status}"
        except Exception as e:
            return False, f"Failed to toggle stabilization: {e}"
    
    def reset_display_states(self):
        """Reset all display states to match fresh Sphero state"""
        # Clear matrix state
        self.matrix_state = [[{'r': 0, 'g': 0, 'b': 0} for _ in range(8)] for _ in range(8)]
        
        # Clear LED states
        self.led_status = {
            'set_back_led': {'r': 0, 'g': 0, 'b': 0, 'active': False},
            'set_front_led': {'r': 0, 'g': 0, 'b': 0, 'active': False},
            'set_main_led': {'r': 0, 'g': 0, 'b': 0, 'active': False}
        }
        
        # Clear last command
        self.last_matrix_command = None
    
    def clear_matrix_only(self):
        """Clear only the matrix, not LEDs"""
        if not self.connected or not self.api:
            return False, "Not connected"
        
        try:
            # Clear matrix via EDU API
            if hasattr(self.api, 'clear_matrix'):
                self.api.clear_matrix()
            
            # Clear compressed frame player with multiple methods
            if self.toy:
                # Method 1: Fill entire frame with black
                if hasattr(self.toy, 'draw_compressed_frame_player_fill'):
                    self.toy.draw_compressed_frame_player_fill(0, 0, 7, 7, 0, 0, 0)
                
                # Method 2: Set one color to black (the command that was causing issues)
                if hasattr(self.toy, 'set_compressed_frame_player_one_color'):
                    self.toy.set_compressed_frame_player_one_color(0, 0, 0)
                
                # Method 3: Stop any running animations
                if hasattr(self.toy, 'stop_compressed_frame_player_animation'):
                    self.toy.stop_compressed_frame_player_animation()
                
                # Method 4: Clear character matrix display
                if hasattr(self.toy, 'clear_character_matrix_display'):
                    self.toy.clear_character_matrix_display()
            
            # Reset only matrix state, keep LED states
            self.matrix_state = [[{'r': 0, 'g': 0, 'b': 0} for _ in range(8)] for _ in range(8)]
            
            # Clear matrix effects from active effects tracking
            self.active_effects['matrix_effects'].clear()
            
            return True, "Matrix cleared completely"
            
        except Exception as e:
            return False, f"Failed to clear matrix: {e}"
    
    def clear_all_display(self):
        """Clear all display elements on the Sphero"""
        if not self.connected or not self.api:
            return False, "Not connected"
        
        try:
            # Clear matrix
            if hasattr(self.api, 'clear_matrix'):
                self.api.clear_matrix()
            
            # Clear LEDs
            if hasattr(self.api, 'set_front_led'):
                self.api.set_front_led(Color(0, 0, 0))
            if hasattr(self.api, 'set_back_led'):
                self.api.set_back_led(Color(0, 0, 0))
            if hasattr(self.api, 'set_main_led'):
                self.api.set_main_led(Color(0, 0, 0))
            
            # Clear compressed frame player
            if self.toy and hasattr(self.toy, 'draw_compressed_frame_player_fill'):
                self.toy.draw_compressed_frame_player_fill(0, 0, 7, 7, 0, 0, 0)
            
            # Reset our tracking states
            self.reset_display_states()
            
            return True, "All display elements cleared"
            
        except Exception as e:
            return False, f"Failed to clear display: {e}"
    
    def force_stop_all_effects(self):
        """Emergency stop - turn off all effects and reset Sphero"""
        if not self.connected:
            return False, "❌ Not connected"
        
        results = []
        
        try:
            # Stop all LEDs
            if self.api:
                try:
                    self.api.set_main_led(Color(0, 0, 0))
                    results.append("✅ Main LED off")
                except: pass
                
                try:
                    self.api.set_back_led(Color(0, 0, 0))
                    results.append("✅ Back LED off")
                except: pass
                
                try:
                    self.api.set_front_led(Color(0, 0, 0))
                    results.append("✅ Front LED off")
                except: pass
                
                try:
                    self.api.clear_matrix()
                    results.append("✅ Matrix cleared")
                except: pass
                
                try:
                    self.api.set_stabilization(True)
                    results.append("✅ Stabilization restored")
                except: pass
            
            # Stop RAW effects with proper verification
            if self.toy:
                # Stop compressed frame player animations
                try:
                    self.toy.stop_compressed_frame_player_animation()
                    results.append("✅ Animations stopped")
                except Exception as e:
                    results.append(f"⚠️ Animation stop failed: {e}")
                
                # Clear compressed frame player completely
                try:
                    # Method 1: Fill with black
                    self.toy.draw_compressed_frame_player_fill(0, 0, 7, 7, 0, 0, 0)
                    results.append("✅ Frame player filled black")
                except Exception as e:
                    results.append(f"⚠️ Frame fill failed: {e}")
                
                try:
                    # Method 2: Set one color to black (this is what you used)
                    self.toy.set_compressed_frame_player_one_color(0, 0, 0)
                    results.append("✅ Frame player one color cleared")
                except Exception as e:
                    results.append(f"⚠️ One color clear failed: {e}")
                
                try:
                    # Method 3: Clear character matrix display
                    self.toy.clear_character_matrix_display()
                    results.append("✅ Character matrix cleared")
                except Exception as e:
                    results.append(f"⚠️ Character matrix clear failed: {e}")
                
                # Additional clearing attempts
                try:
                    # Try to clear any active frame player content
                    for i in range(8):
                        for j in range(8):
                            self.toy.draw_compressed_frame_player_pixel(i, j, 0, 0, 0)
                    results.append("✅ All pixels cleared individually")
                except Exception as e:
                    results.append(f"⚠️ Pixel clear failed: {e}")
                
                try:
                    # Reset all LEDs via raw commands
                    self.toy.set_all_leds_with_8_bit_mask(0, [0, 0, 0, 0, 0, 0, 0, 0])
                    results.append("✅ All LEDs reset")
                except: pass
                
                try:
                    # Reset RGB LED output
                    self.toy.set_rgb_led_output(0, 0, 0)
                    results.append("✅ RGB LED reset")
                except: pass
            
            # Clear active effects tracking
            self.active_effects = {
                'animations': [],
                'leds': {},
                'matrix_effects': [],
                'movements': []
            }
            
            # Reset LED states
            self.led_states = {'back_led': False, 'front_led': False, 'main_led': False}
            
            results.append("🔄 Effect tracking cleared")
            
            # Verification phase - actually check if effects are off
            verification_results = []
            
            # Wait a moment for commands to take effect
            time.sleep(0.5)
            
            # Verify LEDs are actually off by checking if we can detect any light
            try:
                # Try to get ambient light sensor to see if LEDs are affecting it
                if hasattr(self.toy, 'get_ambient_light_sensor_value'):
                    light_before = self.toy.get_ambient_light_sensor_value()
                    
                    # Briefly flash an LED to test responsiveness
                    if self.api:
                        self.api.set_main_led(Color(255, 255, 255))
                        time.sleep(0.1)
                        light_during = self.toy.get_ambient_light_sensor_value()
                        self.api.set_main_led(Color(0, 0, 0))
                        time.sleep(0.1)
                        light_after = self.toy.get_ambient_light_sensor_value()
                        
                        if abs(light_during - light_before) > 1:  # LED caused light change
                            verification_results.append("✅ LED control verified working")
                        else:
                            verification_results.append("⚠️ LED control verification inconclusive")
                        
                        if abs(light_after - light_before) < 1:  # Back to baseline
                            verification_results.append("✅ LEDs verified off")
                        else:
                            verification_results.append("❌ LEDs may still be on")
                
            except Exception as e:
                verification_results.append(f"⚠️ LED verification failed: {e}")
            
            # Verify matrix is clear by trying to detect if it responds to commands
            try:
                if self.api:
                    # Try to set a character and see if it works
                    self.api.set_matrix_character('X', Color(255, 0, 0))
                    time.sleep(0.1)
                    self.api.clear_matrix()
                    verification_results.append("✅ Matrix control verified working")
                    
            except Exception as e:
                verification_results.append(f"⚠️ Matrix verification failed: {e}")
            
            # Add verification results
            if verification_results:
                results.append("\n🔍 Verification Results:")
                results.extend(verification_results)
            
            return True, "\n".join(results)
            
        except Exception as e:
            return False, f"❌ Force stop failed: {e}"
    
    def clear_compressed_frame_player_completely(self):
        """Specifically target compressed frame player effects"""
        if not self.toy:
            return False, "❌ No toy access"
        
        results = []
        
        try:
            # Multiple methods to ensure compressed frame player is cleared
            
            # Method 1: Stop any running animations
            try:
                self.toy.stop_compressed_frame_player_animation()
                results.append("✅ Stopped frame player animation")
            except Exception as e:
                results.append(f"⚠️ Stop animation failed: {e}")
            
            # Method 2: Set one color to black (your problematic command)
            try:
                self.toy.set_compressed_frame_player_one_color(0, 0, 0)
                results.append("✅ Set one color to black")
            except Exception as e:
                results.append(f"❌ One color black failed: {e}")
            
            # Method 3: Fill entire frame with black
            try:
                self.toy.draw_compressed_frame_player_fill(0, 0, 7, 7, 0, 0, 0)
                results.append("✅ Filled frame with black")
            except Exception as e:
                results.append(f"⚠️ Fill black failed: {e}")
            
            # Method 4: Clear all pixels individually
            try:
                for x in range(8):
                    for y in range(8):
                        self.toy.draw_compressed_frame_player_pixel(x, y, 0, 0, 0)
                results.append("✅ Cleared all pixels individually")
            except Exception as e:
                results.append(f"⚠️ Individual pixel clear failed: {e}")
            
            # Method 5: Try to reset the frame player state
            try:
                # Assign empty frame to animation and stop it
                self.toy.assign_compressed_frame_player_frames_to_animation(0, [])
                self.toy.stop_compressed_frame_player_animation()
                results.append("✅ Reset frame player state")
            except Exception as e:
                results.append(f"⚠️ State reset failed: {e}")
            
            return True, "\n".join(results)
            
        except Exception as e:
            return False, f"❌ Compressed frame clear failed: {e}"
    
    def enhanced_force_disconnect(self):
        """Enhanced force disconnect with complete cleanup"""
        messages = []
        
        try:
            # First, stop all effects
            success, stop_result = self.force_stop_all_effects()
            if success:
                messages.append("🛑 All effects stopped")
            else:
                messages.append("⚠️ Effect stop had issues")
            
            # Give Sphero time to process stop commands
            time.sleep(0.5)
            
            # Standard disconnect
            disconnect_messages = self.disconnect(force=True)
            messages.extend(disconnect_messages)
            
            # Additional cleanup
            messages.append("🧹 Enhanced cleanup complete")
            
            return messages
            
        except Exception as e:
            messages.append(f"❌ Enhanced disconnect error: {e}")
            # Fallback to standard disconnect
            return self.disconnect(force=True)
    
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
    
    def verify_connection_integrity(self):
        """Comprehensive connection integrity verification"""
        integrity_report = {
            'connection_valid': False,
            'api_functional': False,
            'toy_accessible': False,
            'led_states_accurate': False,
            'active_effects_valid': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 1. Basic connection verification
            if not self.connected:
                integrity_report['errors'].append("Connection flag is False")
                return False, integrity_report
            
            if not self.api:
                integrity_report['errors'].append("API object is None")
                return False, integrity_report
            
            integrity_report['connection_valid'] = True
            
            # 2. API functionality verification
            try:
                heading = self.api.get_heading()
                if isinstance(heading, (int, float)) and 0 <= heading <= 360:
                    integrity_report['api_functional'] = True
                else:
                    integrity_report['warnings'].append(f"Heading value unusual: {heading}")
            except Exception as e:
                integrity_report['errors'].append(f"API test failed: {e}")
                return False, integrity_report
            
            # 3. Toy object verification
            if self.toy:
                try:
                    # Test a safe toy method
                    battery = self.toy.get_battery_percentage()
                    if isinstance(battery, (int, float)) and 0 <= battery <= 100:
                        integrity_report['toy_accessible'] = True
                    else:
                        integrity_report['warnings'].append(f"Battery value unusual: {battery}")
                except Exception as e:
                    integrity_report['warnings'].append(f"Toy access limited: {e}")
            else:
                integrity_report['warnings'].append("No toy object available")
            
            # 4. LED state verification
            led_verification_passed = True
            for led_name, state in self.led_states.items():
                if not isinstance(state, bool):
                    integrity_report['errors'].append(f"LED state {led_name} is not boolean: {state}")
                    led_verification_passed = False
            
            integrity_report['led_states_accurate'] = led_verification_passed
            
            # 5. Active effects validation
            effects_valid = True
            total_effects = 0
            
            for category, effects in self.active_effects.items():
                if category == 'leds':
                    if not isinstance(effects, dict):
                        integrity_report['errors'].append(f"LED effects should be dict, got {type(effects)}")
                        effects_valid = False
                    else:
                        total_effects += len(effects)
                else:
                    if not isinstance(effects, list):
                        integrity_report['errors'].append(f"{category} effects should be list, got {type(effects)}")
                        effects_valid = False
                    else:
                        total_effects += len(effects)
            
            integrity_report['active_effects_valid'] = effects_valid
            integrity_report['total_tracked_effects'] = total_effects
            
            # Overall integrity assessment
            all_critical_passed = (
                integrity_report['connection_valid'] and
                integrity_report['api_functional'] and
                integrity_report['led_states_accurate'] and
                integrity_report['active_effects_valid']
            )
            
            return all_critical_passed, integrity_report
            
        except Exception as e:
            integrity_report['errors'].append(f"Integrity check failed: {e}")
            return False, integrity_report
    
    def validate_command_result(self, command_name: str, params: List[Any], result: Any, success: bool):
        """Validate that command results are accurate and consistent"""
        validation_report = {
            'result_valid': False,
            'state_consistent': False,
            'tracking_accurate': False,
            'issues': []
        }
        
        try:
            # 1. Result validation
            if success:
                if result is None:
                    validation_report['issues'].append("Success reported but result is None")
                else:
                    validation_report['result_valid'] = True
            else:
                if not isinstance(result, str) or not result.strip():
                    validation_report['issues'].append("Failure reported but no error message")
                else:
                    validation_report['result_valid'] = True
            
            # 2. State consistency check
            if success and 'led' in command_name.lower():
                # Verify LED state tracking matches command
                led_name = command_name.replace('set_', '')
                if led_name in self.led_states:
                    expected_state = any(isinstance(p, Color) and (p.r > 0 or p.g > 0 or p.b > 0) for p in params) if params else False
                    actual_state = self.led_states[led_name]
                    if expected_state == actual_state:
                        validation_report['state_consistent'] = True
                    else:
                        validation_report['issues'].append(f"LED state mismatch: expected {expected_state}, got {actual_state}")
            else:
                validation_report['state_consistent'] = True  # Non-LED commands pass by default
            
            # 3. Effect tracking validation
            if success:
                if 'led' in command_name.lower():
                    # Check if LED effect is properly tracked
                    if command_name in self.active_effects['leds'] or all(isinstance(p, Color) and p.r == 0 and p.g == 0 and p.b == 0 for p in params if isinstance(p, Color)):
                        validation_report['tracking_accurate'] = True
                    else:
                        validation_report['issues'].append(f"LED effect tracking inconsistent for {command_name}")
                else:
                    validation_report['tracking_accurate'] = True  # Non-LED commands pass by default
            else:
                validation_report['tracking_accurate'] = True  # Failed commands don't affect tracking
            
            # Log the validation
            self.command_execution_log.append({
                'timestamp': time.time(),
                'command': command_name,
                'params': str(params),
                'success': success,
                'result': str(result),
                'validation': validation_report
            })
            
            # Keep log size manageable
            if len(self.command_execution_log) > 100:
                self.command_execution_log = self.command_execution_log[-50:]
            
            return validation_report
            
        except Exception as e:
            validation_report['issues'].append(f"Validation failed: {e}")
            return validation_report
    
    def get_integrity_status(self):
        """Get comprehensive integrity and accuracy status"""
        if not self.state_verification_enabled:
            return {
                'status': 'disabled',
                'message': 'Integrity verification is disabled'
            }
        
        # Run full integrity check
        integrity_passed, integrity_report = self.verify_connection_integrity()
        
        # Analyze recent command validations
        recent_validations = self.command_execution_log[-10:] if self.command_execution_log else []
        validation_issues = []
        
        for log_entry in recent_validations:
            validation = log_entry['validation']
            if validation['issues']:
                validation_issues.extend(validation['issues'])
        
        # Generate status report
        status_report = {
            'overall_integrity': 'PASS' if integrity_passed else 'FAIL',
            'connection_integrity': integrity_report,
            'recent_validation_issues': validation_issues,
            'total_commands_logged': len(self.command_execution_log),
            'verification_enabled': self.state_verification_enabled,
            'timestamp': time.time()
        }
        
        return status_report
    
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
        
        # Reset display states on disconnect
        self.reset_display_states()
        
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
        
        .effect-count {
            background: #21262d;
            color: #7d8590;
            padding: 1px 4px;
            border-radius: 8px;
            font-size: 8px;
            margin-left: 4px;
        }
        
        .effect-count.active {
            background: #f85149;
            color: white;
        }
        
        .active-effects-list {
            max-height: 120px;
            overflow-y: auto;
            margin-top: 4px;
        }
        
        .active-effect {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 2px 4px;
            margin: 1px 0;
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 2px;
            font-size: 8px;
        }
        
        .active-effect.led { border-left: 3px solid #f85149; }
        .active-effect.matrix { border-left: 3px solid #d29922; }
        .active-effect.animation { border-left: 3px solid #a5a5a5; }
        .active-effect.movement { border-left: 3px solid #238636; }
        
        .effect-name {
            color: #c9d1d9;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex: 1;
        }
        
        .stop-btn {
            background: #f85149;
            color: white;
            border: none;
            border-radius: 2px;
            width: 12px;
            height: 12px;
            font-size: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-left: 4px;
        }
        
        .stop-btn:hover {
            background: #da3633;
        }
        
        .control-btn.emergency {
            background: #f85149;
            border-color: #da3633;
            color: white;
        }
        
        .control-btn.emergency:hover {
            background: #da3633;
        }
        
        .control-btn.warning {
            background: #d29922;
            border-color: #bb8009;
            color: white;
        }
        
        .control-btn.warning:hover {
            background: #bb8009;
        }
        
        .control-btn.info {
            background: #0969da;
            border-color: #1f6feb;
            color: white;
        }
        
        .control-btn.info:hover {
            background: #1f6feb;
        }
        
        .control-btn.success {
            background: #238636;
            border-color: #2ea043;
            color: white;
        }
        
        .control-btn.success:hover {
            background: #2ea043;
        }
        
        .integrity-status {
            background: #21262d;
            color: #7d8590;
            padding: 1px 4px;
            border-radius: 8px;
            font-size: 8px;
            margin-left: 4px;
        }
        
        .integrity-status.pass {
            background: #238636;
            color: white;
        }
        
        .integrity-status.fail {
            background: #f85149;
            color: white;
        }
        
        .integrity-status.unknown {
            background: #d29922;
            color: white;
        }
        
        .matrix-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            padding: 16px;
        }
        
        .sphero-display {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            width: 280px;
            height: 280px;
            transition: transform 0.3s ease;
            position: relative;
        }
        
        .led-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            position: absolute;
        }
        
        .front-led {
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
        }
        
        .back-led {
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
        }
        
        .led-symbol {
            font-size: 14px;
            color: #7d8590;
            font-weight: bold;
            min-width: 16px;
            text-align: center;
        }
        
        .led-dot {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #21262d;
            border: 1px solid #30363d;
            transition: all 0.2s ease;
        }
        
        .led-dot.active {
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.4);
            border-color: rgba(255, 255, 255, 0.6);
        }
        
        .matrix-grid {
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            gap: 1px;
            background: #21262d;
            padding: 4px;
            border-radius: 4px;
            width: 240px;
            height: 240px;
        }
        
        .matrix-pixel {
            width: 28px;
            height: 28px;
            background: #000000;
            border-radius: 2px;
            transition: all 0.1s ease;
            border: 1px solid #30363d;
        }
        
        .matrix-pixel:hover {
            border-color: #58a6ff;
            transform: scale(1.05);
            z-index: 1;
            position: relative;
        }
        
        .matrix-pixel.active-pixel {
            border-color: rgba(255,255,255,0.3);
            box-shadow: inset 0 0 2px rgba(255,255,255,0.2);
        }
        
        .matrix-controls {
            display: flex;
            flex-direction: column;
            gap: 8px;
            align-items: center;
        }
        
        .matrix-control-row {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .matrix-btn {
            padding: 6px 12px;
            border: 1px solid #30363d;
            border-radius: 3px;
            background: #21262d;
            color: #c9d1d9;
            cursor: pointer;
            font-size: 10px;
            transition: all 0.1s;
        }
        
        .matrix-btn:hover {
            background: #30363d;
            border-color: #484f58;
        }
        
        .matrix-btn.active {
            background: #238636;
            border-color: #2ea043;
            color: white;
        }
        
        .rotation-slider {
            width: 120px;
            height: 4px;
            background: #21262d;
            border-radius: 2px;
            outline: none;
            -webkit-appearance: none;
        }
        
        .rotation-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            background: #58a6ff;
            border-radius: 50%;
            cursor: pointer;
        }
        
        .matrix-rotation {
            font-size: 9px;
            color: #7d8590;
            background: #21262d;
            padding: 2px 6px;
            border-radius: 3px;
        }
        
        .sensor-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 6px;
            padding: 8px;
        }
        
        .sensor-item {
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 8px;
            text-align: center;
        }
        
        .sensor-label {
            font-size: 9px;
            color: #7d8590;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        
        .sensor-value {
            font-size: 12px;
            font-weight: 600;
            color: #58a6ff;
            font-family: monospace;
        }
        
        .integrity-details {
            max-height: 100px;
            overflow-y: auto;
            margin-top: 4px;
        }
        
        .integrity-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1px 4px;
            margin: 1px 0;
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 2px;
            font-size: 8px;
        }
        
        .integrity-item.pass { border-left: 3px solid #238636; }
        .integrity-item.fail { border-left: 3px solid #f85149; }
        
        .integrity-errors {
            color: #f85149;
            font-size: 7px;
            padding: 2px 4px;
            background: #161b22;
            border: 1px solid #f85149;
            border-radius: 2px;
            margin: 1px 0;
        }
        
        .integrity-warnings {
            color: #d29922;
            font-size: 7px;
            padding: 2px 4px;
            background: #161b22;
            border: 1px solid #d29922;
            border-radius: 2px;
            margin: 1px 0;
        }
        
        .integrity-issues {
            color: #f85149;
            font-size: 7px;
            padding: 2px 4px;
            text-align: center;
        }
        
        .integrity-stats {
            color: #7d8590;
            font-size: 7px;
            padding: 2px 4px;
            text-align: center;
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
                    <div class="section">
                        <div class="section-header">🔴 Active Effects <span id="effectCount" class="effect-count">0</span></div>
                        <div class="controls-grid">
                            <div class="control-btn emergency" onclick="forceStopAll()">🛑 STOP ALL</div>
                            <div class="control-btn warning" onclick="clearCompressedFrame()">🔲 CLEAR MATRIX</div>
                            <div class="control-btn warning" onclick="enhancedDisconnect()">🔥 FORCE DC</div>
                            <div class="control-btn info" onclick="refreshActiveEffects()">🔄 Refresh</div>
                        </div>
                        <div id="activeEffectsList" class="active-effects-list">
                            <div style="padding: 10px; text-align: center; color: #7d8590; font-size: 9px;">No active effects</div>
                        </div>
                    </div>
                    <div class="section">
                        <div class="section-header">Expected Matrix Display <span id="matrixRotation" class="matrix-rotation">0°</span></div>
                        <div class="matrix-container">
                            <div class="sphero-display" id="spheroDisplay">
                                <!-- Front LED indicator (rotates with matrix) -->
                                <div class="led-indicator front-led" id="frontLedIndicator">
                                    <div class="led-symbol">F</div>
                                    <div class="led-dot" id="frontLedDot"></div>
                                </div>
                                
                                <div class="matrix-grid" id="matrixGrid">
                                    <!-- 8x8 matrix will be generated here -->
                                </div>
                                
                                <!-- Back LED indicator (rotates with matrix) -->
                                <div class="led-indicator back-led" id="backLedIndicator">
                                    <div class="led-symbol">B</div>
                                    <div class="led-dot" id="backLedDot"></div>
                                </div>
                            </div>
                            <div class="matrix-controls">
                                <div class="matrix-control-row">
                                    <button class="matrix-btn" onclick="refreshMatrixDisplay()">Refresh</button>
                                    <button class="matrix-btn" onclick="clearMatrix()">Clear</button>
                                </div>
                                <div class="matrix-control-row">
                                    <button class="matrix-btn" id="gyroToggle" onclick="toggleGyroStabilization()">Gyro</button>
                                </div>
                                <div class="matrix-control-row">
                                    <label>Rotation Offset:</label>
                                    <input type="range" id="rotationSlider" min="0" max="360" value="0" 
                                           oninput="setMatrixRotation(this.value)" class="rotation-slider">
                                    <span id="rotationValue">0°</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="section">
                        <div class="section-header">Live Sensor Data</div>
                        <div class="sensor-grid">
                            <div class="sensor-item">
                                <div class="sensor-label">Heading</div>
                                <div class="sensor-value" id="liveHeading">N/A</div>
                            </div>
                            <div class="sensor-item">
                                <div class="sensor-label">Battery</div>
                                <div class="sensor-value" id="liveBattery">N/A</div>
                            </div>
                            <div class="sensor-item">
                                <div class="sensor-label">Gyro Stab</div>
                                <div class="sensor-value" id="stabilizationStatus">N/A</div>
                            </div>
                            <div class="sensor-item">
                                <div class="sensor-label">Accel X</div>
                                <div class="sensor-value" id="accelX">N/A</div>
                            </div>
                            <div class="sensor-item">
                                <div class="sensor-label">Accel Y</div>
                                <div class="sensor-value" id="accelY">N/A</div>
                            </div>
                            <div class="sensor-item">
                                <div class="sensor-label">Accel Z</div>
                                <div class="sensor-value" id="accelZ">N/A</div>
                            </div>
                        </div>
                    </div>
                    <div class="section">
                        <div class="section-header">🔍 Integrity Monitor <span id="integrityStatus" class="integrity-status">UNKNOWN</span></div>
                        <div class="controls-grid">
                            <div class="control-btn info" onclick="checkIntegrity()">🔍 Check</div>
                            <div class="control-btn" id="verificationToggle" onclick="toggleVerification()">✅ ON</div>
                        </div>
                        <div id="integrityDetails" class="integrity-details">
                            <div style="padding: 10px; text-align: center; color: #7d8590; font-size: 9px;">Click Check to verify integrity</div>
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
                    // Refresh active effects after successful command
                    setTimeout(refreshActiveEffects, 100);
                }
            } else if (type === 'active_effects') {
                updateActiveEffects(data);
            } else if (type === 'matrix_display') {
                updateMatrixDisplay(data);
            } else if (type === 'live_sensors') {
                updateLiveSensors(data);
            } else if (type === 'integrity_status') {
                updateIntegrityStatus(data);
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
        
        function refreshActiveEffects() {
            if (!connected) {
                addConsoleMessage('Not connected', 'error');
                return;
            }
            
            ws.send(JSON.stringify({
                action: 'get_active_effects'
            }));
        }
        
        function stopEffect(effectId) {
            if (!connected) {
                addConsoleMessage('Not connected', 'error');
                return;
            }
            
            ws.send(JSON.stringify({
                action: 'stop_effect',
                effect_id: effectId
            }));
        }
        
        function forceStopAll() {
            if (!connected) {
                addConsoleMessage('Not connected', 'error');
                return;
            }
            
            addConsoleMessage('🛑 EMERGENCY STOP - Stopping all effects...', 'warning');
            
            ws.send(JSON.stringify({
                action: 'force_stop_all'
            }));
        }
        
        function clearCompressedFrame() {
            if (!connected) {
                addConsoleMessage('Not connected', 'error');
                return;
            }
            
            addConsoleMessage('🔲 CLEARING MATRIX - Multiple clear methods...', 'warning');
            
            ws.send(JSON.stringify({
                action: 'clear_compressed_frame'
            }));
        }
        
        function enhancedDisconnect() {
            addConsoleMessage('🔥 ENHANCED FORCE DISCONNECT - Stopping everything...', 'warning');
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'enhanced_disconnect' }));
            }
            
            // Always force reset state
            connected = false;
            updateStatus(false);
            resetLEDStates();
        }
        
        function updateActiveEffects(effectsData) {
            const countElement = document.getElementById('effectCount');
            const listElement = document.getElementById('activeEffectsList');
            
            countElement.textContent = effectsData.total;
            countElement.className = effectsData.total > 0 ? 'effect-count active' : 'effect-count';
            
            if (effectsData.total === 0) {
                listElement.innerHTML = '<div style="padding: 10px; text-align: center; color: #7d8590; font-size: 9px;">No active effects</div>';
                return;
            }
            
            let html = '';
            
            // LEDs
            Object.values(effectsData.effects.leds).forEach(effect => {
                html += `
                    <div class="active-effect led">
                        <span class="effect-name">💡 ${effect.command}</span>
                        <button class="stop-btn" onclick="stopEffect('${effect.id}')">×</button>
                    </div>
                `;
            });
            
            // Matrix effects
            effectsData.effects.matrix_effects.forEach(effect => {
                html += `
                    <div class="active-effect matrix">
                        <span class="effect-name">🔲 ${effect.command}</span>
                        <button class="stop-btn" onclick="stopEffect('${effect.id}')">×</button>
                    </div>
                `;
            });
            
            // Animations
            effectsData.effects.animations.forEach(effect => {
                html += `
                    <div class="active-effect animation">
                        <span class="effect-name">🎬 ${effect.command}</span>
                        <button class="stop-btn" onclick="stopEffect('${effect.id}')">×</button>
                    </div>
                `;
            });
            
            // Movements
            effectsData.effects.movements.forEach(effect => {
                html += `
                    <div class="active-effect movement">
                        <span class="effect-name">🏃 ${effect.command}</span>
                        <button class="stop-btn" onclick="stopEffect('${effect.id}')">×</button>
                    </div>
                `;
            });
            
            listElement.innerHTML = html;
        }
        
        function checkIntegrity() {
            if (!connected) {
                addConsoleMessage('Not connected', 'error');
                return;
            }
            
            addConsoleMessage('🔍 Running integrity check...', 'info');
            
            ws.send(JSON.stringify({
                action: 'get_integrity_status'
            }));
        }
        
        function toggleVerification() {
            ws.send(JSON.stringify({
                action: 'toggle_verification'
            }));
        }
        
        function updateIntegrityStatus(statusData) {
            const statusElement = document.getElementById('integrityStatus');
            const detailsElement = document.getElementById('integrityDetails');
            const toggleBtn = document.getElementById('verificationToggle');
            
            // Update main status
            const overallStatus = statusData.overall_integrity || 'UNKNOWN';
            statusElement.textContent = overallStatus;
            statusElement.className = `integrity-status ${overallStatus.toLowerCase()}`;
            
            // Update verification toggle
            const verificationEnabled = statusData.verification_enabled;
            toggleBtn.textContent = verificationEnabled ? '✅ ON' : '❌ OFF';
            toggleBtn.className = verificationEnabled ? 'control-btn success' : 'control-btn';
            
            // Update details
            let detailsHtml = '';
            
            if (statusData.connection_integrity) {
                const ci = statusData.connection_integrity;
                detailsHtml += `
                    <div class="integrity-item ${ci.connection_valid ? 'pass' : 'fail'}">
                        Connection: ${ci.connection_valid ? '✅' : '❌'}
                    </div>
                    <div class="integrity-item ${ci.api_functional ? 'pass' : 'fail'}">
                        API: ${ci.api_functional ? '✅' : '❌'}
                    </div>
                    <div class="integrity-item ${ci.led_states_accurate ? 'pass' : 'fail'}">
                        LED States: ${ci.led_states_accurate ? '✅' : '❌'}
                    </div>
                    <div class="integrity-item ${ci.active_effects_valid ? 'pass' : 'fail'}">
                        Effect Tracking: ${ci.active_effects_valid ? '✅' : '❌'}
                    </div>
                `;
                
                if (ci.errors && ci.errors.length > 0) {
                    detailsHtml += `<div class="integrity-errors">Errors: ${ci.errors.join(', ')}</div>`;
                }
                
                if (ci.warnings && ci.warnings.length > 0) {
                    detailsHtml += `<div class="integrity-warnings">Warnings: ${ci.warnings.join(', ')}</div>`;
                }
            }
            
            if (statusData.recent_validation_issues && statusData.recent_validation_issues.length > 0) {
                detailsHtml += `<div class="integrity-issues">Recent Issues: ${statusData.recent_validation_issues.length}</div>`;
            }
            
            if (statusData.total_commands_logged) {
                detailsHtml += `<div class="integrity-stats">Commands Logged: ${statusData.total_commands_logged}</div>`;
            }
            
            detailsElement.innerHTML = detailsHtml || '<div style="padding: 10px; text-align: center; color: #7d8590; font-size: 9px;">No integrity data</div>';
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
        
        // Matrix Display Functions
        function initializeMatrixDisplay() {
            const matrixGrid = document.getElementById('matrixGrid');
            matrixGrid.innerHTML = '';
            
            // Create 8x8 grid
            for (let y = 0; y < 8; y++) {
                for (let x = 0; x < 8; x++) {
                    const pixel = document.createElement('div');
                    pixel.className = 'matrix-pixel';
                    pixel.id = `pixel-${x}-${y}`;
                    pixel.style.backgroundColor = '#000000';
                    matrixGrid.appendChild(pixel);
                }
            }
        }
        
        function refreshMatrixDisplay() {
            if (!connected) return;
            
            ws.send(JSON.stringify({
                action: 'get_matrix_display'
            }));
        }
        
        function updateMatrixDisplay(matrixData) {
            const matrix = matrixData.matrix;
            const heading = matrixData.current_heading || 0;
            const gyroEnabled = matrixData.gyro_enabled || false;
            
            // Update heading display only (rotation is client-side)
            document.getElementById('matrixRotation').textContent = `H:${heading.toFixed(1)}°`;
            
            // Update LED status indicators
            if (matrixData.led_status) {
                updateLedIndicators(matrixData.led_status);
            }
            
            // Don't override client-side rotation - let user control it
            // The rotation slider and wrapper transform are handled by setMatrixRotation()
            
            // Update matrix pixels
            for (let y = 0; y < 8; y++) {
                for (let x = 0; x < 8; x++) {
                    const pixel = document.getElementById(`pixel-${x}-${y}`);
                    if (pixel && matrix && matrix[y] && matrix[y][x]) {
                        const color = matrix[y][x];
                        const rgb = `rgb(${color.r}, ${color.g}, ${color.b})`;
                        pixel.style.backgroundColor = rgb;
                        
                        const brightness = (color.r + color.g + color.b) / 3;
                        if (brightness > 0) {
                            pixel.style.opacity = 1.0;  // Full opacity for active pixels
                            pixel.classList.add('active-pixel');
                        } else {
                            pixel.style.opacity = 1.0;  // Keep black boxes fully opaque
                            pixel.classList.remove('active-pixel');
                        }
                        
                        if (brightness > 200) {
                            pixel.style.border = '1px solid rgba(255,255,255,0.3)';
                        } else {
                            pixel.style.border = '1px solid #30363d';
                        }
                    }
                }
            }
        }
        
        function setMatrixRotation(degrees) {
            // Pure client-side rotation - no server delay
            document.getElementById('rotationValue').textContent = degrees + '°';
            
            // Apply rotation to entire sphero display (matrix + LEDs)
            const spheroDisplay = document.getElementById('spheroDisplay');
            if (spheroDisplay) {
                spheroDisplay.style.transform = `rotate(${degrees}deg)`;
            }
        }
        
        function clearMatrix() {
            if (!connected) return;
            
            // Clear matrix visualization immediately (client-side)
            clearMatrixVisualization();
            
            // Send clear matrix command to Sphero (only matrix, not LEDs)
            ws.send(JSON.stringify({
                action: 'clear_matrix_only'
            }));
            
            // Force refresh after a short delay to ensure server state is updated
            setTimeout(() => {
                if (connected) {
                    refreshMatrixDisplay();
                }
            }, 500);
        }
        
        function clearMatrixVisualization() {
            // Immediately clear the matrix display (client-side)
            for (let y = 0; y < 8; y++) {
                for (let x = 0; x < 8; x++) {
                    const pixel = document.getElementById(`pixel-${x}-${y}`);
                    if (pixel) {
                        pixel.style.backgroundColor = '#000000';
                        pixel.style.opacity = 1.0;
                        pixel.classList.remove('active-pixel');
                        pixel.style.border = '1px solid #30363d';
                    }
                }
            }
        }
        
        function toggleGyroStabilization() {
            if (!connected) return;
            
            ws.send(JSON.stringify({
                action: 'toggle_gyro_stabilization'
            }));
        }
        
        function refreshSensors() {
            if (!connected) return;
            
            ws.send(JSON.stringify({
                action: 'get_live_sensors'
            }));
        }
        
        function updateLedIndicators(ledStatus) {
            // Update front LED
            const frontDot = document.getElementById('frontLedDot');
            if (frontDot && ledStatus.set_front_led) {
                const front = ledStatus.set_front_led;
                if (front.active) {
                    frontDot.style.backgroundColor = `rgb(${front.r}, ${front.g}, ${front.b})`;
                    frontDot.classList.add('active');
                } else {
                    frontDot.style.backgroundColor = '#21262d';
                    frontDot.classList.remove('active');
                }
            }
            
            // Update back LED
            const backDot = document.getElementById('backLedDot');
            if (backDot && ledStatus.set_back_led) {
                const back = ledStatus.set_back_led;
                if (back.active) {
                    backDot.style.backgroundColor = `rgb(${back.r}, ${back.g}, ${back.b})`;
                    backDot.classList.add('active');
                } else {
                    backDot.style.backgroundColor = '#21262d';
                    backDot.classList.remove('active');
                }
            }
        }
        
        function updateLiveSensors(sensorData) {
            if (!sensorData) return;
            
            if (sensorData.heading !== null && sensorData.heading !== undefined) {
                document.getElementById('liveHeading').textContent = sensorData.heading.toFixed(1) + '°';
            } else {
                document.getElementById('liveHeading').textContent = 'N/A';
            }
            
            if (sensorData.battery_percentage !== null && sensorData.battery_percentage !== undefined) {
                document.getElementById('liveBattery').textContent = sensorData.battery_percentage.toFixed(0) + '%';
            } else {
                document.getElementById('liveBattery').textContent = 'N/A';
            }
            
            const gyroBtn = document.getElementById('gyroToggle');
            if (sensorData.stabilization_enabled) {
                document.getElementById('stabilizationStatus').textContent = 'ON';
                gyroBtn.textContent = 'Gyro ON';
                gyroBtn.className = 'matrix-btn active';
            } else {
                document.getElementById('stabilizationStatus').textContent = 'OFF';
                gyroBtn.textContent = 'Gyro OFF';
                gyroBtn.className = 'matrix-btn';
            }
            
            if (sensorData.accelerometer) {
                document.getElementById('accelX').textContent = sensorData.accelerometer.x.toFixed(2);
                document.getElementById('accelY').textContent = sensorData.accelerometer.y.toFixed(2);
                document.getElementById('accelZ').textContent = sensorData.accelerometer.z.toFixed(2);
            } else {
                document.getElementById('accelX').textContent = 'N/A';
                document.getElementById('accelY').textContent = 'N/A';
                document.getElementById('accelZ').textContent = 'N/A';
            }
        }
        
        // Auto-refresh matrix and sensors
        setInterval(() => {
            if (connected) {
                refreshMatrixDisplay();
                refreshSensors();
            }
        }, 2000);
        
        // Initialize matrix display on page load
        document.addEventListener('DOMContentLoaded', function() {
            initializeMatrixDisplay();
        });
        
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
                
            elif action == 'get_active_effects':
                effects = tester.get_active_effects()
                await websocket.send_json({'type': 'active_effects', 'data': effects})
                
            elif action == 'stop_effect':
                effect_id = data.get('effect_id')
                success, result = tester.stop_effect(effect_id)
                await websocket.send_json({'type': 'result', 'data': result})
                # Send updated effects list
                effects = tester.get_active_effects()
                await websocket.send_json({'type': 'active_effects', 'data': effects})
                
            elif action == 'force_stop_all':
                success, result = tester.force_stop_all_effects()
                await websocket.send_json({'type': 'result', 'data': result})
                # Send updated effects list
                effects = tester.get_active_effects()
                await websocket.send_json({'type': 'active_effects', 'data': effects})
                
            elif action == 'enhanced_disconnect':
                messages = tester.enhanced_force_disconnect()
                for message in messages:
                    await websocket.send_json({'type': 'status', 'data': message})
                    await asyncio.sleep(0.1)
                
            elif action == 'get_integrity_status':
                status = tester.get_integrity_status()
                await websocket.send_json({'type': 'integrity_status', 'data': status})
                
            elif action == 'toggle_verification':
                tester.state_verification_enabled = not tester.state_verification_enabled
                status = f"Integrity verification {'enabled' if tester.state_verification_enabled else 'disabled'}"
                await websocket.send_json({'type': 'result', 'data': status})
                
            elif action == 'clear_compressed_frame':
                success, result = tester.clear_compressed_frame_player_completely()
                await websocket.send_json({'type': 'result', 'data': result})
                
            elif action == 'get_matrix_display':
                matrix_data = tester.get_matrix_display_data()
                await websocket.send_json({'type': 'matrix_display', 'data': matrix_data})
                

                
            elif action == 'toggle_gyro_stabilization':
                success, result = tester.toggle_gyro_stabilization()
                await websocket.send_json({'type': 'result', 'data': result})
                
            elif action == 'get_live_sensors':
                sensor_data = tester.get_live_sensor_data()
                await websocket.send_json({'type': 'live_sensors', 'data': sensor_data})
                
            elif action == 'clear_matrix_only':
                success, result = tester.clear_matrix_only()
                await websocket.send_json({'type': 'result', 'data': result})
                # Send updated matrix display immediately after clearing
                if success:
                    await asyncio.sleep(0.1)  # Small delay to ensure commands are processed
                    matrix_data = tester.get_matrix_display_data()
                    await websocket.send_json({'type': 'matrix_display', 'data': matrix_data})
                
            elif action == 'clear_all_display':
                success, result = tester.clear_all_display()
                await websocket.send_json({'type': 'result', 'data': result})
                # Send updated matrix display immediately after clearing
                if success:
                    await asyncio.sleep(0.1)  # Small delay to ensure commands are processed
                    matrix_data = tester.get_matrix_display_data()
                    await websocket.send_json({'type': 'matrix_display', 'data': matrix_data})
                
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