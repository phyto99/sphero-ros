
"""
LangGraph Sphero Bolt Tool System - Event-Driven Controller Mode
Clean integration with spherov2.py for using Sphero as an input device
The AI uses the Sphero's 8x8 LED matrix to communicate back
"""

from typing import Any, Dict, List, Optional, Callable
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI, EventType
from spherov2.types import Color
import time
import threading


class SpheroBoltController:
    """
    Event-driven Sphero Bolt interface for AI control
    Sphero is passive - used as a controller/input device
    AI communicates back via the 8x8 LED matrix
    """
    
    def __init__(self):
        self.toy = None
        self.droid = None
        self._connected = False
        self._event_callbacks = {}
        self._sensor_data = {}
        self._running = False
        
    def connect(self, toy_name: Optional[str] = None) -> bool:
        """Connect to Sphero Bolt and start event loop"""
        if self._connected:
            return True
            
        try:
            # Find and connect to toy
            if toy_name:
                self.toy = scanner.find_toy(toy_name=toy_name)
            else:
                self.toy = scanner.find_toy()
                
            if not self.toy:
                return False
                
            # Use context manager approach from spherov2.py docs
            self.droid = SpheroEduAPI(self.toy)
            self.droid.__enter__()
            self._connected = True
            
            # Register default event handlers
            self._setup_event_handlers()
            
            # Indicate connection with matrix
            self.display_text("AI", color=Color(0, 255, 0))
            time.sleep(1)
            self.clear_matrix()
            
            return True
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def _setup_event_handlers(self):
        """Register all event handlers for controller input"""
        
        def on_collision_handler(api):
            self._sensor_data['last_collision'] = time.time()
            if 'collision' in self._event_callbacks:
                self._event_callbacks['collision'](api)
        
        def on_gyro_max_handler(api):
            self._sensor_data['last_spin'] = time.time()
            self._sensor_data['spin_count'] = self._sensor_data.get('spin_count', 0) + 1
            if 'spin' in self._event_callbacks:
                self._event_callbacks['spin'](api)
        
        def on_freefall_handler(api):
            self._sensor_data['last_freefall'] = time.time()
            if 'freefall' in self._event_callbacks:
                self._event_callbacks['freefall'](api)
        
        def on_landing_handler(api):
            self._sensor_data['last_landing'] = time.time()
            if 'landing' in self._event_callbacks:
                self._event_callbacks['landing'](api)
        
        # Register events
        self.droid.register_event(EventType.on_collision, on_collision_handler)
        self.droid.register_event(EventType.on_gyro_max, on_gyro_max_handler)
        self.droid.register_event(EventType.on_freefall, on_freefall_handler)
        self.droid.register_event(EventType.on_landing, on_landing_handler)
        
        # Disable stabilization for better spin detection
        self.droid.set_stabilization(False)
    
    def register_event_callback(self, event_name: str, callback: Callable):
        """Allow AI to register callbacks for specific events"""
        self._event_callbacks[event_name] = callback
    
    def get_sensor_data(self) -> Dict[str, Any]:
        """Get all current sensor readings"""
        if not self._connected:
            return {"error": "Not connected"}
        
        try:
            data = {
                'heading': self.droid.get_heading(),
                'acceleration': self.droid.get_acceleration(),
                'gyroscope': self.droid.get_gyroscope(),
                'orientation': self.droid.get_orientation(),
                'velocity': self.droid.get_velocity(),
                'location': self.droid.get_location(),
                'events': self._sensor_data.copy()
            }
            return data
        except Exception as e:
            return {"error": str(e)}
    
    # LED Matrix Communication Methods
    def set_matrix_pixel(self, x: int, y: int, color: Color):
        """Set individual pixel on 8x8 matrix"""
        if self._connected:
            self.droid.set_matrix_pixel(x, y, color)
    
    def set_matrix_line(self, line: List[Color]):
        """Set entire line of pixels (8 colors)"""
        if self._connected:
            self.droid.set_matrix_line(line)
    
    def set_matrix_fill(self, color: Color):
        """Fill entire matrix with one color"""
        if self._connected:
            self.droid.set_matrix_fill(color)
    
    def set_matrix_character(self, char: str, color: Color):
        """Display a single character on matrix"""
        if self._connected:
            self.droid.set_matrix_character(char, color)
    
    def display_text(self, text: str, color: Color, fps: int = 7):
        """Scroll text across matrix"""
        if self._connected:
            self.droid.scroll_matrix_text(text, color, fps)
    
    def clear_matrix(self):
        """Clear the LED matrix"""
        if self._connected:
            self.droid.clear_matrix()
    
    def show_emotion(self, emotion: str):
        """Display simple emotion on matrix"""
        emotions = {
            'happy': [(3, 2), (4, 2), (2, 5), (3, 6), (4, 6), (5, 5)],
            'sad': [(3, 2), (4, 2), (2, 5), (3, 4), (4, 4), (5, 5)],
            'thinking': [(3, 3), (4, 3), (3, 5), (4, 5), (5, 5)],
            'alert': [(3, 2), (4, 2), (3, 4), (4, 4), (3, 6), (4, 6)]
        }
        
        if emotion in emotions and self._connected:
            self.clear_matrix()
            for x, y in emotions[emotion]:
                self.set_matrix_pixel(x, y, Color(255, 255, 0))
    
    def disconnect(self):
        """Safely disconnect from Sphero"""
        if self._connected and self.droid:
            try:
                self.clear_matrix()
                self.droid.__exit__(None, None, None)
            except:
                pass
            self._connected = False


# Global controller instance
sphero_controller = SpheroBoltController()


# LangGraph Tools
@tool
def sphero_connect(toy_name: Optional[str] = None) -> str:
    """
    Connect to Sphero Bolt in controller mode.
    Sphero acts as input device, AI responds via LED matrix.
    
    Args:
        toy_name: Optional specific toy name
        
    Returns:
        Connection status
    """
    success = sphero_controller.connect(toy_name)
    if success:
        return "Connected to Sphero Bolt. Ready for controller input. Use LED matrix to communicate."
    return "Failed to connect. Ensure Sphero is powered on and nearby."


@tool
def sphero_read_sensors() -> Dict[str, Any]:
    """
    Read all sensor data from Sphero Bolt.
    Includes heading, acceleration, gyroscope, velocity, location, and recent events.
    
    Returns:
        Dictionary of all sensor readings and event data
    """
    return sphero_controller.get_sensor_data()


@tool
def sphero_display_text(text: str, color: str = "white") -> str:
    """
    Display scrolling text on Sphero's 8x8 LED matrix.
    This is how the AI communicates back to the user.
    
    Args:
        text: Text to display (will scroll if longer than 1 char)
        color: Color name (red, green, blue, white, yellow, purple, cyan)
        
    Returns:
        Status message
    """
    color_map = {
        'red': Color(255, 0, 0),
        'green': Color(0, 255, 0),
        'blue': Color(0, 0, 255),
        'white': Color(255, 255, 255),
        'yellow': Color(255, 255, 0),
        'purple': Color(255, 0, 255),
        'cyan': Color(0, 255, 255)
    }
    
    c = color_map.get(color.lower(), Color(255, 255, 255))
    sphero_controller.display_text(text, c)
    return f"Displayed '{text}' in {color}"


@tool
def sphero_show_emotion(emotion: str) -> str:
    """
    Show an emotion icon on the LED matrix.
    
    Args:
        emotion: Emotion to display (happy, sad, thinking, alert)
        
    Returns:
        Status message
    """
    sphero_controller.show_emotion(emotion)
    return f"Showing {emotion} emotion"


@tool
def sphero_clear_display() -> str:
    """
    Clear the LED matrix display.
    
    Returns:
        Status message
    """
    sphero_controller.clear_matrix()
    return "Display cleared"


@tool
def sphero_draw_pattern(pattern: str) -> str:
    """
    Draw a simple pattern on the matrix.
    
    Args:
        pattern: Pattern name (checkerboard, border, cross, x)
        
    Returns:
        Status message
    """
    patterns = {
        'checkerboard': lambda: [
            sphero_controller.set_matrix_pixel(x, y, Color(255, 255, 255))
            for x in range(8) for y in range(8) if (x + y) % 2 == 0
        ],
        'border': lambda: [
            sphero_controller.set_matrix_pixel(x, y, Color(0, 255, 255))
            for x in range(8) for y in range(8) if x in [0, 7] or y in [0, 7]
        ],
        'cross': lambda: [
            sphero_controller.set_matrix_pixel(x, y, Color(255, 0, 0))
            for x in range(8) for y in range(8) if x == 3 or x == 4 or y == 3 or y == 4
        ]
    }
    
    if pattern in patterns:
        sphero_controller.clear_matrix()
        patterns[pattern]()
        return f"Drew {pattern} pattern"
    return f"Unknown pattern: {pattern}"


@tool
def sphero_set_main_led(color: str) -> str:
    """
    Set the main LED color (the ball's internal light).
    
    Args:
        color: Color name
        
    Returns:
        Status message
    """
    color_map = {
        'red': Color(255, 0, 0),
        'green': Color(0, 255, 0),
        'blue': Color(0, 0, 255),
        'white': Color(255, 255, 255),
        'off': Color(0, 0, 0)
    }
    
    c = color_map.get(color.lower(), Color(255, 255, 255))
    sphero_controller.droid.set_main_led(c)
    return f"Main LED set to {color}"


@tool
def sphero_register_spin_callback(message: str) -> str:
    """
    Set up a callback for when user spins the Sphero.
    When detected, AI will display the message on the matrix.
    
    Args:
        message: Message to display when spin detected
        
    Returns:
        Status message
    """
    def spin_handler(api):
        sphero_controller.display_text(message, Color(255, 255, 0))
    
    sphero_controller.register_event_callback('spin', spin_handler)
    return f"Spin callback registered: will display '{message}'"


@tool
def sphero_disconnect() -> str:
    """
    Disconnect from Sphero Bolt.
    
    Returns:
        Status message
    """
    sphero_controller.disconnect()
    return "Disconnected from Sphero Bolt"


# Export tools for LangGraph
SPHERO_TOOLS = [
    sphero_connect,
    sphero_read_sensors,
    sphero_display_text,
    sphero_show_emotion,
    sphero_clear_display,
    sphero_draw_pattern,
    sphero_set_main_led,
    sphero_register_spin_callback,
    sphero_disconnect,
]

sphero_tool_node = ToolNode(SPHERO_TOOLS)


# Example Usage
if __name__ == "__main__":
    print("=== Sphero Bolt Controller Mode ===\n")
    print("Example: AI responds to physical Sphero inputs\n")
    
    # Connect
    result = sphero_connect.invoke({})
    print(f"1. {result}\n")
    
    # Set up spin callback
    result = sphero_register_spin_callback.invoke({"message": "SPIN!"})
    print(f"2. {result}\n")
    
    # Display message to user
    result = sphero_display_text.invoke({"text": "Ready!", "color": "green"})
    print(f"3. {result}\n")
    
    # Monitor for 10 seconds
    print("4. Monitoring sensors for 10 seconds...")
    print("   (Try spinning or moving the Sphero!)\n")
    
    for i in range(10):
        sensors = sphero_read_sensors.invoke({})
        if 'spin_count' in sensors.get('events', {}):
            print(f"   Detected {sensors['events']['spin_count']} spins!")
        time.sleep(1)
    
    # Show emotion
    result = sphero_show_emotion.invoke({"emotion": "happy"})
    print(f"\n5. {result}\n")
    
    time.sleep(2)
    
    # Disconnect
    result = sphero_disconnect.invoke({})
    print(f"6. {result}")