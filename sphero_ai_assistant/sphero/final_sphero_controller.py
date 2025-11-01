"""
Final Sphero Controller - Clean, working implementation
Replaces all the previous attempts with a simple, reliable approach
"""

import logging
import time
from typing import Dict, Any, Optional, Callable, List

try:
    from spherov2 import scanner
    from spherov2.sphero_edu import SpheroEduAPI
    from spherov2.types import Color
    SPHERO_AVAILABLE = True
except ImportError:
    SPHERO_AVAILABLE = False
    # Mock classes for development
    class Color:
        def __init__(self, r, g, b): pass
    class SpheroEduAPI:
        def __init__(self, toy): pass

class FinalSpheroController:
    """
    Final Sphero Controller - Simple and reliable
    Incorporates Claude's insights without complexity
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Connection state
        self.toy = None
        self.api = None
        self.is_connected = False
        self.has_matrix = False
        self.robot_name = None
        
        # Event callbacks
        self.callbacks = {
            'connected': [],
            'disconnected': [],
            'error': []
        }
        
        # Last known sensor data
        self.sensor_data = {}
    
    def connect(self, robot_id: str = None, timeout: int = 30) -> bool:
        """
        Connect to Sphero using simple, reliable method
        
        Args:
            robot_id: Specific robot ID (like 'SB-5925') or None for any
            timeout: Scan timeout in seconds
        """
        try:
            if not SPHERO_AVAILABLE:
                self.logger.error("Sphero SDK not available. Run: pip install spherov2 bleak")
                return False
            
            self.logger.info("🔍 Scanning for Sphero...")
            if robot_id:
                self.logger.info(f"Looking for: {robot_id}")
            
            # Simple scan
            if robot_id:
                self.toy = scanner.find_toy(toy_name=robot_id.upper(), timeout=timeout)
            else:
                toys = scanner.find_toys(timeout=timeout)
                if toys:
                    # Prefer Bolt, then any Sphero
                    bolt_toys = [t for t in toys if t.name and 'bolt' in t.name.lower()]
                    self.toy = bolt_toys[0] if bolt_toys else toys[0]
                else:
                    self.toy = None
            
            if not self.toy:
                self.logger.error("No Sphero found")
                self.logger.info("Troubleshooting:")
                self.logger.info("  1. Put Sphero on charger for 3 seconds")
                self.logger.info("  2. Remove from charger (it will be dark - this is normal)")
                self.logger.info("  3. Make sure it's NOT paired in Windows Bluetooth")
                self.logger.info("  4. Try again")
                return False
            
            self.robot_name = self.toy.name
            self.has_matrix = 'bolt' in self.robot_name.lower() if self.robot_name else False
            
            self.logger.info(f"✅ Found: {self.robot_name} (Matrix: {self.has_matrix})")
            
            # Connect
            self.toy.__enter__()
            self.api = SpheroEduAPI(self.toy)
            self.is_connected = True
            
            # Wake up with green LED
            self.api.set_main_led(Color(0, 255, 0))
            time.sleep(0.5)
            self.api.set_main_led(Color(0, 0, 0))
            
            # Show ready on matrix if available
            if self.has_matrix:
                try:
                    self.api.scroll_matrix_text("READY", Color(0, 255, 255), fps=8)
                    time.sleep(2)
                    self.api.clear_matrix()
                except:
                    pass
            
            self.logger.info("✅ Connected and ready!")
            self._trigger_callbacks('connected', {'name': self.robot_name})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self._trigger_callbacks('error', {'error': str(e)})
            return False
    
    def disconnect(self):
        """Safely disconnect"""
        if self.is_connected and self.toy:
            try:
                # Goodbye
                if self.has_matrix:
                    self.api.scroll_matrix_text("BYE", Color(255, 0, 255), fps=10)
                    time.sleep(1)
                    self.api.clear_matrix()
                
                self.api.set_main_led(Color(0, 0, 0))
                self.toy.__exit__(None, None, None)
                self.logger.info("Disconnected")
            except:
                pass
        
        self.is_connected = False
        self._trigger_callbacks('disconnected', {})
    
    # LED Methods
    def set_led_color(self, r: int, g: int, b: int):
        """Set main LED color"""
        if self.is_connected and self.api:
            try:
                self.api.set_main_led(Color(r, g, b))
            except Exception as e:
                self.logger.error(f"LED error: {e}")
    
    def led_off(self):
        """Turn off LED"""
        self.set_led_color(0, 0, 0)
    
    # Matrix Methods (Bolt only)
    def display_text(self, text: str, r: int = 255, g: int = 255, b: int = 255):
        """Display scrolling text"""
        if self.has_matrix and self.is_connected and self.api:
            try:
                self.api.scroll_matrix_text(text, Color(r, g, b), fps=8)
            except Exception as e:
                self.logger.error(f"Matrix error: {e}")
    
    def display_character(self, char: str, r: int = 255, g: int = 255, b: int = 255):
        """Display single character"""
        if self.has_matrix and self.is_connected and self.api:
            try:
                self.api.set_matrix_character(char, Color(r, g, b))
            except Exception as e:
                self.logger.error(f"Matrix error: {e}")
    
    def clear_display(self):
        """Clear matrix display"""
        if self.has_matrix and self.is_connected and self.api:
            try:
                self.api.clear_matrix()
            except Exception as e:
                self.logger.error(f"Matrix clear error: {e}")
    
    # AI Expression Methods
    def express_emotion(self, emotion: str, message: str = None):
        """Express AI emotion through Sphero"""
        emotions = {
            'happy': (0, 255, 0),
            'thinking': (138, 43, 226),
            'excited': (255, 0, 255),
            'calm': (0, 100, 255),
            'error': (255, 0, 0),
            'warning': (255, 165, 0),
            'neutral': (255, 255, 255)
        }
        
        color = emotions.get(emotion, (255, 255, 255))
        display_msg = message or emotion.upper()
        
        # Show on matrix if available
        if self.has_matrix:
            self.display_text(display_msg, color[0], color[1], color[2])
        
        # Set LED color
        self.set_led_color(color[0], color[1], color[2])
        time.sleep(2)
        self.led_off()
    
    def ai_thinking(self):
        """Show AI is thinking"""
        self.express_emotion('thinking', 'THINKING')
    
    def ai_ready(self):
        """Show AI is ready"""
        self.express_emotion('happy', 'READY')
    
    def ai_error(self):
        """Show AI error"""
        self.express_emotion('error', 'ERROR')
    
    # Sensor Methods
    def get_heading(self) -> float:
        """Get current heading"""
        if self.is_connected and self.api:
            try:
                heading = self.api.get_heading()
                self.sensor_data['heading'] = heading
                return heading
            except Exception as e:
                self.logger.error(f"Sensor error: {e}")
        return 0.0
    
    def get_sensor_data(self) -> Dict[str, Any]:
        """Get all sensor data"""
        if self.is_connected and self.api:
            try:
                data = {
                    'heading': self.api.get_heading()
                }
                self.sensor_data.update(data)
                return data
            except Exception as e:
                self.logger.error(f"Sensor data error: {e}")
        return {}
    
    # Event System
    def register_callback(self, event: str, callback: Callable):
        """Register event callback"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, data: Dict):
        """Trigger callbacks"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    # Status Methods
    def is_ready(self) -> bool:
        """Check if ready for commands"""
        return self.is_connected and self.api is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get status info"""
        return {
            'connected': self.is_connected,
            'robot_name': self.robot_name,
            'has_matrix': self.has_matrix,
            'sensor_data': self.sensor_data.copy()
        }
    
    # Test Methods
    def test_functionality(self) -> bool:
        """Test all functionality"""
        if not self.is_connected:
            return False
        
        try:
            self.logger.info("Testing functionality...")
            
            # Test LED
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
            for r, g, b in colors:
                self.set_led_color(r, g, b)
                time.sleep(0.3)
            self.led_off()
            
            # Test matrix
            if self.has_matrix:
                self.display_character("!", 255, 255, 0)
                time.sleep(1)
                self.clear_display()
            
            # Test sensors
            heading = self.get_heading()
            self.logger.info(f"Heading: {heading}°")
            
            self.logger.info("✅ All tests passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            return False