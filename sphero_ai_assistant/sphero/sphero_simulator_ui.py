"""
Sphero Simulator UI - Visual simulation of Sphero Bolt with LED display and orientation
"""

import tkinter as tk
from tkinter import ttk
import math
import threading
import time
from typing import Tuple, Optional
import logging


class SpheroSimulatorUI:
    """
    Visual Sphero simulator showing LED patterns, orientation, and movement
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.window = None
        self.canvas = None
        self.is_running = False
        self.thread = None
        
        # Sphero state
        self.led_color = (0, 0, 0)  # RGB
        self.orientation = 0  # degrees
        self.is_spinning = False
        self.spin_speed = 0  # degrees per second
        self.battery_level = 100
        self.connection_status = "Connected"
        
        # UI elements
        self.led_circle = None
        self.orientation_line = None
        self.info_labels = {}
        
        # Animation
        self.last_update = time.time()
        self.animation_running = False
    
    def start(self):
        """Start the Sphero simulator UI"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_ui, daemon=True)
        self.thread.start()
        self.logger.info("Sphero Simulator UI started")
    
    def stop(self):
        """Stop the Sphero simulator UI"""
        self.is_running = False
        if self.window:
            try:
                self.window.quit()
                self.window.destroy()
            except:
                pass
        self.logger.info("Sphero Simulator UI stopped")
    
    def _run_ui(self):
        """Run the UI in a separate thread"""
        try:
            self.window = tk.Tk()
            self.window.title("Sphero Bolt Simulator")
            self.window.geometry("400x500")
            self.window.configure(bg='#2d3748')
            self.window.resizable(False, False)
            
            # Make window stay on top
            self.window.attributes('-topmost', True)
            
            self._create_ui_elements()
            self._start_animation()
            
            # Handle window close
            self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            self.window.mainloop()
            
        except Exception as e:
            self.logger.error(f"Error in Sphero simulator UI: {e}")
    
    def _create_ui_elements(self):
        """Create the UI elements"""
        # Title
        title_label = tk.Label(
            self.window, 
            text="Sphero Bolt Simulator", 
            font=("Arial", 16, "bold"),
            fg='white',
            bg='#2d3748'
        )
        title_label.pack(pady=10)
        
        # Main canvas for Sphero visualization
        self.canvas = tk.Canvas(
            self.window,
            width=300,
            height=300,
            bg='#1a202c',
            highlightthickness=2,
            highlightbackground='#4a5568'
        )
        self.canvas.pack(pady=10)
        
        # Draw Sphero body (outer circle)
        self.canvas.create_oval(50, 50, 250, 250, outline='#718096', width=3, fill='#4a5568')
        
        # Draw LED area (inner circle)
        self.led_circle = self.canvas.create_oval(125, 125, 175, 175, fill='#000000', outline='#718096')
        
        # Draw orientation indicator (line from center)
        self.orientation_line = self.canvas.create_line(150, 150, 150, 100, fill='#e2e8f0', width=3)
        
        # Add compass directions
        self.canvas.create_text(150, 30, text="N", fill='#cbd5e0', font=("Arial", 12, "bold"))
        self.canvas.create_text(270, 150, text="E", fill='#cbd5e0', font=("Arial", 12, "bold"))
        self.canvas.create_text(150, 270, text="S", fill='#cbd5e0', font=("Arial", 12, "bold"))
        self.canvas.create_text(30, 150, text="W", fill='#cbd5e0', font=("Arial", 12, "bold"))
        
        # Status information frame
        info_frame = tk.Frame(self.window, bg='#2d3748')
        info_frame.pack(pady=10, padx=20, fill='x')
        
        # Create status labels
        self._create_status_labels(info_frame)
    
    def _create_status_labels(self, parent):
        """Create status information labels"""
        labels_data = [
            ("Connection:", "connection_status"),
            ("Battery:", "battery_level"),
            ("LED Color:", "led_color"),
            ("Orientation:", "orientation"),
            ("Spinning:", "spinning_status")
        ]
        
        for i, (label_text, key) in enumerate(labels_data):
            # Label
            tk.Label(
                parent,
                text=label_text,
                font=("Arial", 10, "bold"),
                fg='#cbd5e0',
                bg='#2d3748'
            ).grid(row=i, column=0, sticky='w', padx=(0, 10), pady=2)
            
            # Value
            value_label = tk.Label(
                parent,
                text="--",
                font=("Arial", 10),
                fg='#e2e8f0',
                bg='#2d3748'
            )
            value_label.grid(row=i, column=1, sticky='w', pady=2)
            self.info_labels[key] = value_label
        
        # Configure grid weights
        parent.grid_columnconfigure(1, weight=1)
    
    def _start_animation(self):
        """Start the animation loop"""
        self.animation_running = True
        self._animate()
    
    def _animate(self):
        """Animation loop"""
        if not self.animation_running or not self.window:
            return
        
        try:
            current_time = time.time()
            dt = current_time - self.last_update
            self.last_update = current_time
            
            # Update spinning animation
            if self.is_spinning and self.spin_speed > 0:
                self.orientation = (self.orientation + self.spin_speed * dt) % 360
                self._update_orientation_display()
            
            # Update status labels
            self._update_status_labels()
            
            # Schedule next animation frame
            if self.window:
                self.window.after(50, self._animate)  # ~20 FPS
                
        except Exception as e:
            self.logger.error(f"Animation error: {e}")
    
    def _update_orientation_display(self):
        """Update the orientation line on the canvas"""
        if not self.canvas or not self.orientation_line:
            return
        
        try:
            # Calculate line end point based on orientation
            center_x, center_y = 150, 150
            radius = 50
            
            # Convert orientation to radians (0 degrees = North)
            angle_rad = math.radians(self.orientation - 90)  # Adjust for canvas coordinates
            
            end_x = center_x + radius * math.cos(angle_rad)
            end_y = center_y + radius * math.sin(angle_rad)
            
            # Update the line
            self.canvas.coords(self.orientation_line, center_x, center_y, end_x, end_y)
            
        except Exception as e:
            self.logger.error(f"Error updating orientation display: {e}")
    
    def _update_status_labels(self):
        """Update all status labels"""
        try:
            if not self.info_labels:
                return
            
            # Connection status
            if 'connection_status' in self.info_labels:
                self.info_labels['connection_status'].config(
                    text=self.connection_status,
                    fg='#48bb78' if self.connection_status == "Connected" else '#f56565'
                )
            
            # Battery level
            if 'battery_level' in self.info_labels:
                battery_color = '#48bb78' if self.battery_level > 50 else '#ed8936' if self.battery_level > 20 else '#f56565'
                self.info_labels['battery_level'].config(
                    text=f"{self.battery_level:.1f}%",
                    fg=battery_color
                )
            
            # LED color
            if 'led_color' in self.info_labels:
                r, g, b = self.led_color
                color_text = f"RGB({r}, {g}, {b})"
                self.info_labels['led_color'].config(text=color_text)
            
            # Orientation
            if 'orientation' in self.info_labels:
                self.info_labels['orientation'].config(text=f"{self.orientation:.1f}°")
            
            # Spinning status
            if 'spinning_status' in self.info_labels:
                if self.is_spinning:
                    spin_text = f"Yes ({self.spin_speed:.1f}°/s)"
                    spin_color = '#ed8936'
                else:
                    spin_text = "No"
                    spin_color = '#cbd5e0'
                
                self.info_labels['spinning_status'].config(
                    text=spin_text,
                    fg=spin_color
                )
                
        except Exception as e:
            self.logger.error(f"Error updating status labels: {e}")
    
    def _on_closing(self):
        """Handle window closing"""
        self.animation_running = False
        self.is_running = False
        if self.window:
            self.window.quit()
    
    def set_led_color(self, r: int, g: int, b: int):
        """Set the LED color"""
        self.led_color = (r, g, b)
        
        if self.canvas and self.led_circle:
            try:
                # Convert RGB to hex color
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                self.canvas.itemconfig(self.led_circle, fill=hex_color)
            except Exception as e:
                self.logger.error(f"Error setting LED color: {e}")
    
    def set_orientation(self, degrees: float):
        """Set the Sphero orientation"""
        self.orientation = degrees % 360
        self._update_orientation_display()
    
    def set_spinning(self, is_spinning: bool, speed: float = 0):
        """Set spinning state and speed"""
        self.is_spinning = is_spinning
        self.spin_speed = speed
    
    def set_battery_level(self, level: float):
        """Set battery level"""
        self.battery_level = max(0, min(100, level))
    
    def set_connection_status(self, status: str):
        """Set connection status"""
        self.connection_status = status
    
    def simulate_movement(self, direction: float, speed: float, duration: float):
        """Simulate movement by showing orientation change"""
        self.set_orientation(direction)
        
        # Simulate slight spinning during movement
        if speed > 0:
            self.set_spinning(True, speed * 2)  # Spin speed proportional to movement speed
            
            # Stop spinning after duration
            if self.window:
                self.window.after(int(duration * 1000), lambda: self.set_spinning(False, 0))
    
    def simulate_led_pattern(self, pattern: str, colors: list, duration: float):
        """Simulate LED patterns"""
        if not colors:
            return
        
        try:
            if pattern == "solid":
                r, g, b = colors[0]
                self.set_led_color(r, g, b)
                
            elif pattern == "pulse":
                self._animate_pulse(colors[0], duration)
                
            elif pattern == "rainbow":
                self._animate_rainbow(duration)
                
            elif pattern == "sparkle":
                self._animate_sparkle(colors, duration)
                
        except Exception as e:
            self.logger.error(f"Error simulating LED pattern: {e}")
    
    def _animate_pulse(self, color: Tuple[int, int, int], duration: float):
        """Animate pulsing LED pattern"""
        if not self.window:
            return
        
        r, g, b = color
        steps = 20
        step_duration = duration / (steps * 2)  # Fade in and fade out
        
        def pulse_step(step, fading_in=True):
            if not self.window or not self.animation_running:
                return
            
            if fading_in:
                brightness = step / steps
                next_step = step + 1
                next_fading_in = step < steps - 1
            else:
                brightness = (steps - step) / steps
                next_step = step + 1
                next_fading_in = False
            
            # Apply brightness
            pulse_r = int(r * brightness)
            pulse_g = int(g * brightness)
            pulse_b = int(b * brightness)
            
            self.set_led_color(pulse_r, pulse_g, pulse_b)
            
            if step < steps - 1 or fading_in:
                self.window.after(
                    int(step_duration * 1000),
                    lambda: pulse_step(next_step if next_fading_in else 0, next_fading_in)
                )
        
        pulse_step(0, True)
    
    def _animate_rainbow(self, duration: float):
        """Animate rainbow LED pattern"""
        if not self.window:
            return
        
        colors = [
            (255, 0, 0),    # Red
            (255, 165, 0),  # Orange
            (255, 255, 0),  # Yellow
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (75, 0, 130),   # Indigo
            (238, 130, 238) # Violet
        ]
        
        step_duration = duration / len(colors)
        
        def rainbow_step(color_index):
            if not self.window or not self.animation_running or color_index >= len(colors):
                return
            
            r, g, b = colors[color_index]
            self.set_led_color(r, g, b)
            
            self.window.after(
                int(step_duration * 1000),
                lambda: rainbow_step(color_index + 1)
            )
        
        rainbow_step(0)
    
    def _animate_sparkle(self, colors: list, duration: float):
        """Animate sparkling LED pattern"""
        if not self.window or not colors:
            return
        
        import random
        
        steps = int(duration * 10)  # 10 sparkles per second
        step_duration = duration / steps
        
        def sparkle_step(step):
            if not self.window or not self.animation_running or step >= steps:
                return
            
            # Random color from the list
            color = random.choice(colors)
            r, g, b = color
            
            # Random brightness
            brightness = random.uniform(0.3, 1.0)
            sparkle_r = int(r * brightness)
            sparkle_g = int(g * brightness)
            sparkle_b = int(b * brightness)
            
            self.set_led_color(sparkle_r, sparkle_g, sparkle_b)
            
            self.window.after(
                int(step_duration * 1000),
                lambda: sparkle_step(step + 1)
            )
        
        sparkle_step(0)