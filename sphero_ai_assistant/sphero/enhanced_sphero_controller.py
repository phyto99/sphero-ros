"""
Enhanced Sphero Controller - Autonomous decision-making capabilities for Sphero Bolt
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path

try:
    from spherov2 import scanner
    from spherov2.sphero_edu import SpheroEduAPI
    from spherov2.types import Color
    import spherov2.commands.power as power
    SPHERO_AVAILABLE = True
except ImportError:
    SPHERO_AVAILABLE = False
    # Mock classes for development without Sphero hardware
    class Color:
        def __init__(self, r, g, b): pass
    class SpheroEduAPI:
        def __init__(self, toy): pass


class SpheroMode(Enum):
    """Sphero operation modes"""
    IDLE = "idle"
    EXPRESSION = "expression"
    INPUT_DEVICE = "input_device"
    HYBRID = "hybrid"
    MAINTENANCE = "maintenance"


class SpheroTask:
    """Represents a task for the Sphero"""
    def __init__(self, task_id: str, task_type: str, priority: int, 
                 duration: Optional[float] = None, data: Optional[Dict] = None):
        self.task_id = task_id
        self.task_type = task_type
        self.priority = priority  # 1-10, 10 being highest
        self.duration = duration
        self.data = data or {}
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.status = "pending"


class EnhancedSpheroController:
    """
    Enhanced Sphero Controller with autonomous decision-making capabilities
    Requirements 2.2, 2.5, 2.6: Autonomous Sphero intelligence and decision-making
    """
    
    def __init__(self, decision_engine, config_manager):
        self.decision_engine = decision_engine
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Sphero connection
        self.sphero_toy = None
        self.sphero_api = None
        self.is_connected = False
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.target_sphero_name = None  # Can be set to target specific Sphero
        self.discovered_spheros = []
        
        # State management
        self.current_mode = SpheroMode.IDLE
        self.task_queue: List[SpheroTask] = []
        self.current_task: Optional[SpheroTask] = None
        self.is_running = False
        
        # Battery and power management
        self.battery_level = 100
        self.last_battery_check = None
        self.low_battery_threshold = 20
        self.critical_battery_threshold = 10
        
        # Performance tracking
        self.task_history: List[SpheroTask] = []
        self.performance_metrics = {
            'tasks_completed': 0,
            'expression_time': 0,
            'input_time': 0,
            'idle_time': 0,
            'errors': 0
        }
        
        # Simulator UI
        self.simulator_ui = None
        
        # Autonomous behavior settings
        self.autonomous_mode = True
        self.decision_interval = 1.0  # seconds
        self.task_timeout = 30.0  # seconds
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'connected': [],
            'disconnected': [],
            'battery_low': [],
            'battery_critical': [],
            'task_completed': [],
            'mode_changed': [],
            'error': []
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the enhanced Sphero controller
        Requirement 2.1: Establish connection with Sphero Bolt
        """
        try:
            self.logger.info("Initializing Enhanced Sphero Controller...")
            
            if not SPHERO_AVAILABLE:
                self.logger.warning("Sphero SDK not available - running in simulation mode")
                await self._initialize_simulation_mode()
                return True
            
            # Attempt to connect to Sphero
            success = await self._connect_to_sphero()
            if success:
                # Start autonomous decision-making loop
                asyncio.create_task(self._autonomous_decision_loop())
                # Start battery monitoring
                asyncio.create_task(self._battery_monitoring_loop())
                
                self.is_running = True
                self.logger.info("Enhanced Sphero Controller initialized successfully")
                await self._trigger_event('connected')
                return True
            else:
                self.logger.error("Failed to connect to Sphero after multiple attempts")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Enhanced Sphero Controller: {e}")
            return False
    
    async def _connect_to_sphero(self, target_name: str = None) -> bool:
        """
        Attempt to connect to Sphero Bolt
        Args:
            target_name: Optional specific Sphero name to connect to
        """
        try:
            self.logger.info("Scanning for Sphero devices...")
            
            # Scan for Sphero devices with longer timeout
            toys = scanner.find_toys(timeout=15)
            
            if not toys:
                self.logger.warning("No Sphero devices found during scan")
                return False
            
            self.discovered_spheros = [(toy.name, toy.address) for toy in toys]
            self.logger.info(f"Found {len(toys)} Sphero device(s): {self.discovered_spheros}")
            
            # Select target Sphero
            target_toy = None
            if target_name:
                # Look for specific Sphero by name
                for toy in toys:
                    if toy.name and target_name.lower() in toy.name.lower():
                        target_toy = toy
                        break
                if not target_toy:
                    self.logger.warning(f"Sphero '{target_name}' not found. Available: {[toy.name for toy in toys]}")
                    return False
            else:
                # Use first available Sphero Bolt (prefer Bolt over other models)
                bolt_toys = [toy for toy in toys if 'bolt' in toy.name.lower() if toy.name]
                if bolt_toys:
                    target_toy = bolt_toys[0]
                else:
                    target_toy = toys[0]  # Fallback to first available
            
            self.sphero_toy = target_toy
            self.logger.info(f"Attempting to connect to: {target_toy.name} ({target_toy.address})")
            
            # Connect to the selected Sphero
            with target_toy:
                self.logger.info("Establishing connection...")
                
                # Initialize Sphero Edu API
                self.sphero_api = SpheroEduAPI(target_toy)
                
                # Test connection with LED
                self.logger.info("Testing connection with LED...")
                self.sphero_api.set_main_led(Color(0, 255, 0))  # Green
                await asyncio.sleep(0.5)
                self.sphero_api.set_main_led(Color(0, 0, 0))    # Off
                
                # Get battery level
                try:
                    battery_voltage = target_toy.get_battery_voltage()
                    if battery_voltage:
                        # Convert voltage to approximate percentage (Sphero Bolt: ~3.6V = 0%, ~4.2V = 100%)
                        self.battery_level = max(0, min(100, (battery_voltage - 3.6) / 0.6 * 100))
                        self.logger.info(f"Battery level: {self.battery_level:.1f}% ({battery_voltage:.2f}V)")
                except Exception as e:
                    self.logger.warning(f"Could not read battery level: {e}")
                
                self.is_connected = True
                self.connection_attempts = 0
                self.logger.info(f"Successfully connected to Sphero: {target_toy.name}")
                
                return True
            
        except Exception as e:
            self.connection_attempts += 1
            self.logger.error(f"Failed to connect to Sphero (attempt {self.connection_attempts}): {e}")
            
            if self.connection_attempts >= self.max_connection_attempts:
                self.logger.error("Max connection attempts reached, switching to simulation mode")
                await self._initialize_simulation_mode()
                return True
            
            return False
    
    async def _initialize_simulation_mode(self):
        """Initialize simulation mode when Sphero hardware is not available"""
        self.logger.info("Initializing Sphero simulation mode")
        self.is_connected = True  # Simulate connection
        self.battery_level = 85   # Simulate battery level
        
        # Initialize simulator UI
        try:
            from .sphero_simulator_ui import SpheroSimulatorUI
            self.simulator_ui = SpheroSimulatorUI()
            self.simulator_ui.set_battery_level(self.battery_level)
            self.simulator_ui.set_connection_status("Connected (Simulation)")
            self.simulator_ui.start()
            self.logger.info("Sphero simulator UI started")
        except Exception as e:
            self.logger.warning(f"Could not start simulator UI: {e}")
            self.simulator_ui = None
        
        # Start simulation loops
        asyncio.create_task(self._simulation_loop())
        asyncio.create_task(self._autonomous_decision_loop())
        asyncio.create_task(self._battery_monitoring_loop())
        
        self.is_running = True
    
    async def _simulation_loop(self):
        """Simulation loop for development without hardware"""
        while self.is_running:
            try:
                # Simulate battery drain
                if self.current_mode != SpheroMode.IDLE:
                    self.battery_level = max(0, self.battery_level - 0.1)
                
                # Simulate task execution
                if self.current_task and self.current_task.status == "running":
                    # Simulate task completion after some time
                    if (datetime.now() - self.current_task.started_at).total_seconds() > 5:
                        await self._complete_current_task()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(5)
    
    async def add_task(self, task_type: str, priority: int, duration: Optional[float] = None, 
                      data: Optional[Dict] = None) -> str:
        """
        Add a task to the Sphero task queue
        Requirement 2.8: Process multiple simultaneous demands with prioritization
        """
        try:
            task_id = f"sphero_task_{datetime.now().timestamp()}"
            task = SpheroTask(task_id, task_type, priority, duration, data)
            
            # Insert task in priority order
            inserted = False
            for i, existing_task in enumerate(self.task_queue):
                if task.priority > existing_task.priority:
                    self.task_queue.insert(i, task)
                    inserted = True
                    break
            
            if not inserted:
                self.task_queue.append(task)
            
            self.logger.info(f"Added Sphero task: {task_type} (priority: {priority})")
            
            # Trigger autonomous decision-making
            if self.autonomous_mode:
                await self._evaluate_task_queue()
            
            return task_id
            
        except Exception as e:
            self.logger.error(f"Failed to add Sphero task: {e}")
            raise
    
    async def _autonomous_decision_loop(self):
        """
        Main autonomous decision-making loop
        Requirement 2.2: Autonomous decision-making for optimal Sphero resource use
        """
        while self.is_running:
            try:
                if self.autonomous_mode:
                    await self._make_autonomous_decisions()
                
                await asyncio.sleep(self.decision_interval)
                
            except Exception as e:
                self.logger.error(f"Error in autonomous decision loop: {e}")
                await asyncio.sleep(5)
    
    async def _make_autonomous_decisions(self):
        """Make autonomous decisions about Sphero usage"""
        try:
            # Check battery level and adjust behavior
            await self._check_battery_constraints()
            
            # Evaluate current task and queue
            await self._evaluate_task_queue()
            
            # Check for mode optimization opportunities
            await self._optimize_mode()
            
            # Handle task timeouts
            await self._handle_task_timeouts()
            
        except Exception as e:
            self.logger.error(f"Error in autonomous decision-making: {e}")
    
    async def _evaluate_task_queue(self):
        """Evaluate and potentially switch tasks based on priority and context"""
        if not self.task_queue:
            if self.current_mode != SpheroMode.IDLE:
                await self._switch_mode(SpheroMode.IDLE)
            return
        
        # Get the highest priority task
        next_task = self.task_queue[0]
        
        # Decide whether to interrupt current task
        should_switch = False
        
        if not self.current_task:
            should_switch = True
        elif next_task.priority > self.current_task.priority + 2:  # Significant priority difference
            should_switch = True
        elif self.current_task.status == "completed":
            should_switch = True
        
        if should_switch:
            await self._start_next_task()
    
    async def _start_next_task(self):
        """Start the next task from the queue"""
        if not self.task_queue:
            return
        
        # Complete current task if running
        if self.current_task and self.current_task.status == "running":
            await self._interrupt_current_task()
        
        # Get next task
        next_task = self.task_queue.pop(0)
        self.current_task = next_task
        next_task.status = "running"
        next_task.started_at = datetime.now()
        
        # Execute the task
        await self._execute_task(next_task)
    
    async def _execute_task(self, task: SpheroTask):
        """Execute a specific Sphero task"""
        try:
            self.logger.info(f"Executing Sphero task: {task.task_type}")
            
            if task.task_type == "led_expression":
                await self._execute_led_expression(task)
            elif task.task_type == "input_device":
                await self._execute_input_device(task)
            elif task.task_type == "movement":
                await self._execute_movement(task)
            elif task.task_type == "notification":
                await self._execute_notification(task)
            else:
                self.logger.warning(f"Unknown task type: {task.task_type}")
                await self._complete_current_task()
            
        except Exception as e:
            self.logger.error(f"Error executing task {task.task_id}: {e}")
            await self._fail_current_task(str(e))
    
    async def _execute_led_expression(self, task: SpheroTask):
        """Execute LED expression task"""
        try:
            expression_data = task.data.get('expression', {})
            pattern = expression_data.get('pattern', 'solid')
            color = expression_data.get('color', [0, 255, 0])
            duration = task.duration or 3.0
            
            await self._switch_mode(SpheroMode.EXPRESSION)
            
            if self.sphero_api and SPHERO_AVAILABLE and self.is_connected:
                try:
                    if pattern == 'solid':
                        self.sphero_api.set_main_led(Color(color[0], color[1], color[2]))
                    elif pattern == 'pulse':
                        await self._led_pulse_pattern(color, duration)
                    elif pattern == 'rainbow':
                        await self._led_rainbow_pattern(duration)
                except Exception as e:
                    self.logger.error(f"Error controlling Sphero LED: {e}")
            else:
                # Simulation mode
                self.logger.info(f"Simulating LED expression: {pattern} with color {color}")
                if self.simulator_ui:
                    self.simulator_ui.simulate_led_pattern(pattern, [color], duration)
            
            # Schedule task completion
            if task.duration:
                asyncio.create_task(self._schedule_task_completion(task.duration))
            
        except Exception as e:
            self.logger.error(f"Error in LED expression: {e}")
            await self._fail_current_task(str(e))
    
    async def _execute_input_device(self, task: SpheroTask):
        """Execute input device task"""
        try:
            device_type = task.data.get('device_type', 'generic')
            await self._switch_mode(SpheroMode.INPUT_DEVICE)
            
            self.logger.info(f"Sphero configured as input device: {device_type}")
            
            # Input device tasks typically run until explicitly stopped
            # They don't auto-complete like expression tasks
            
        except Exception as e:
            self.logger.error(f"Error configuring input device: {e}")
            await self._fail_current_task(str(e))
    
    async def _execute_movement(self, task: SpheroTask):
        """Execute movement task"""
        try:
            movement_data = task.data.get('movement', {})
            direction = movement_data.get('direction', 0)
            speed = movement_data.get('speed', 50)
            duration = task.duration or 2.0
            
            if self.sphero_api and SPHERO_AVAILABLE and self.is_connected:
                try:
                    # Convert speed (0-100) to Sphero speed (0-255)
                    sphero_speed = int(speed * 2.55)
                    self.sphero_api.roll(sphero_speed, direction, duration)
                except Exception as e:
                    self.logger.error(f"Error controlling Sphero movement: {e}")
            else:
                # Simulation mode
                self.logger.info(f"Simulating movement: direction={direction}, speed={speed}, duration={duration}")
                if self.simulator_ui:
                    self.simulator_ui.simulate_movement(direction, speed, duration)
            
            # Schedule task completion
            asyncio.create_task(self._schedule_task_completion(duration))
            
        except Exception as e:
            self.logger.error(f"Error in movement: {e}")
            await self._fail_current_task(str(e))
    
    async def _execute_notification(self, task: SpheroTask):
        """Execute notification task"""
        try:
            notification_data = task.data.get('notification', {})
            notification_type = notification_data.get('type', 'info')
            
            if notification_type == 'success':
                color = [0, 255, 0]  # Green
            elif notification_type == 'warning':
                color = [255, 165, 0]  # Orange
            elif notification_type == 'error':
                color = [255, 0, 0]  # Red
            else:
                color = [0, 0, 255]  # Blue for info
            
            # Quick flash notification
            if self.sphero_api and SPHERO_AVAILABLE and self.is_connected:
                try:
                    self.sphero_api.set_main_led(Color(color[0], color[1], color[2]))
                    await asyncio.sleep(0.5)
                    self.sphero_api.set_main_led(Color(0, 0, 0))
                except Exception as e:
                    self.logger.error(f"Error with Sphero notification: {e}")
            else:
                self.logger.info(f"Simulating notification: {notification_type}")
                if self.simulator_ui:
                    self.simulator_ui.set_led_color(color[0], color[1], color[2])
                    # Brief flash
                    await asyncio.sleep(0.5)
                    self.simulator_ui.set_led_color(0, 0, 0)
            
            await self._complete_current_task()
            
        except Exception as e:
            self.logger.error(f"Error in notification: {e}")
            await self._fail_current_task(str(e))
    
    async def _led_pulse_pattern(self, color: List[int], duration: float):
        """Create a pulsing LED pattern"""
        if not self.sphero_api or not SPHERO_AVAILABLE or not self.is_connected:
            return
        
        try:
            end_time = datetime.now() + timedelta(seconds=duration)
            while datetime.now() < end_time:
                # Fade in
                for brightness in range(0, 256, 32):
                    r = int(color[0] * brightness / 255)
                    g = int(color[1] * brightness / 255)
                    b = int(color[2] * brightness / 255)
                    self.sphero_api.set_main_led(Color(r, g, b))
                    await asyncio.sleep(0.05)
                
                # Fade out
                for brightness in range(255, -1, -32):
                    r = int(color[0] * brightness / 255)
                    g = int(color[1] * brightness / 255)
                    b = int(color[2] * brightness / 255)
                    self.sphero_api.set_main_led(Color(r, g, b))
                    await asyncio.sleep(0.05)
        except Exception as e:
            self.logger.error(f"Error in pulse pattern: {e}")
    
    async def _led_rainbow_pattern(self, duration: float):
        """Create a rainbow LED pattern"""
        if not self.sphero_api or not SPHERO_AVAILABLE or not self.is_connected:
            return
        
        try:
            colors = [
                [255, 0, 0],    # Red
                [255, 165, 0],  # Orange
                [255, 255, 0],  # Yellow
                [0, 255, 0],    # Green
                [0, 0, 255],    # Blue
                [75, 0, 130],   # Indigo
                [238, 130, 238] # Violet
            ]
            
            end_time = datetime.now() + timedelta(seconds=duration)
            color_index = 0
            
            while datetime.now() < end_time:
                color = colors[color_index % len(colors)]
                self.sphero_api.set_main_led(Color(color[0], color[1], color[2]))
                await asyncio.sleep(0.3)
                color_index += 1
        except Exception as e:
            self.logger.error(f"Error in rainbow pattern: {e}")
    
    async def _schedule_task_completion(self, delay: float):
        """Schedule task completion after a delay"""
        await asyncio.sleep(delay)
        if self.current_task and self.current_task.status == "running":
            await self._complete_current_task()
    
    async def _complete_current_task(self):
        """Complete the current task"""
        if not self.current_task:
            return
        
        self.current_task.status = "completed"
        self.current_task.completed_at = datetime.now()
        
        # Add to history
        self.task_history.append(self.current_task)
        self.performance_metrics['tasks_completed'] += 1
        
        self.logger.info(f"Completed Sphero task: {self.current_task.task_type}")
        await self._trigger_event('task_completed', self.current_task)
        
        self.current_task = None
        
        # Check for next task
        await self._evaluate_task_queue()
    
    async def _fail_current_task(self, error_message: str):
        """Fail the current task"""
        if not self.current_task:
            return
        
        self.current_task.status = "failed"
        self.current_task.completed_at = datetime.now()
        self.current_task.data['error'] = error_message
        
        # Add to history
        self.task_history.append(self.current_task)
        self.performance_metrics['errors'] += 1
        
        self.logger.error(f"Failed Sphero task: {self.current_task.task_type} - {error_message}")
        await self._trigger_event('error', {'task': self.current_task, 'error': error_message})
        
        self.current_task = None
        
        # Check for next task
        await self._evaluate_task_queue()
    
    async def _interrupt_current_task(self):
        """Interrupt the current task for a higher priority one"""
        if not self.current_task:
            return
        
        self.current_task.status = "interrupted"
        self.current_task.completed_at = datetime.now()
        
        # Add back to queue if it should be resumed
        if self.current_task.task_type in ['input_device']:
            # Re-queue interrupted input device tasks
            self.task_queue.insert(0, self.current_task)
            self.current_task.status = "pending"
            self.current_task.completed_at = None
        else:
            # Add to history
            self.task_history.append(self.current_task)
        
        self.logger.info(f"Interrupted Sphero task: {self.current_task.task_type}")
        self.current_task = None
    
    async def _switch_mode(self, new_mode: SpheroMode):
        """Switch Sphero operation mode"""
        if self.current_mode == new_mode:
            return
        
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        self.logger.info(f"Sphero mode changed: {old_mode.value} -> {new_mode.value}")
        await self._trigger_event('mode_changed', {'old_mode': old_mode, 'new_mode': new_mode})
    
    async def _optimize_mode(self):
        """Optimize current mode based on context"""
        # This could be enhanced with more sophisticated logic
        if not self.current_task and self.current_mode != SpheroMode.IDLE:
            await self._switch_mode(SpheroMode.IDLE)
    
    async def _handle_task_timeouts(self):
        """Handle task timeouts"""
        if not self.current_task or self.current_task.status != "running":
            return
        
        if not self.current_task.started_at:
            return
        
        elapsed = (datetime.now() - self.current_task.started_at).total_seconds()
        if elapsed > self.task_timeout:
            self.logger.warning(f"Task timeout: {self.current_task.task_type}")
            await self._fail_current_task("Task timeout")
    
    async def _battery_monitoring_loop(self):
        """
        Monitor battery level and adjust behavior
        Requirement 2.5: Battery monitoring with intelligent power management
        """
        while self.is_running:
            try:
                await self._check_battery_level()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in battery monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _check_battery_level(self):
        """Check current battery level"""
        try:
            if self.sphero_toy and SPHERO_AVAILABLE and self.is_connected:
                try:
                    # Get battery voltage from Sphero
                    battery_voltage = self.sphero_toy.get_battery_voltage()
                    if battery_voltage:
                        # Convert voltage to percentage (3.6V = 0%, 4.2V = 100%)
                        self.battery_level = max(0, min(100, (battery_voltage - 3.6) / 0.6 * 100))
                except Exception as e:
                    self.logger.warning(f"Could not read battery level: {e}")
            else:
                # Simulation mode - gradually decrease battery
                if self.current_mode != SpheroMode.IDLE:
                    self.battery_level = max(0, self.battery_level - 0.5)
                
                # Update simulator UI
                if self.simulator_ui:
                    self.simulator_ui.set_battery_level(self.battery_level)
            
            self.last_battery_check = datetime.now()
            
            # Check for low battery conditions
            if self.battery_level <= self.critical_battery_threshold:
                await self._handle_critical_battery()
            elif self.battery_level <= self.low_battery_threshold:
                await self._handle_low_battery()
            
        except Exception as e:
            self.logger.error(f"Error checking battery level: {e}")
    
    async def _check_battery_constraints(self):
        """Check battery constraints for decision-making"""
        if self.battery_level <= self.critical_battery_threshold:
            # Cancel all non-essential tasks
            self.task_queue = [task for task in self.task_queue if task.priority >= 8]
            if self.current_task and self.current_task.priority < 8:
                await self._interrupt_current_task()
        elif self.battery_level <= self.low_battery_threshold:
            # Reduce task frequency and prefer low-power operations
            self.decision_interval = 2.0  # Slower decision-making
        else:
            self.decision_interval = 1.0  # Normal decision-making
    
    async def _handle_low_battery(self):
        """Handle low battery condition"""
        self.logger.warning(f"Sphero battery low: {self.battery_level}%")
        await self._trigger_event('battery_low', {'level': self.battery_level})
        
        # Add low battery notification
        await self.add_task('notification', 7, data={
            'notification': {'type': 'warning'}
        })
    
    async def _handle_critical_battery(self):
        """Handle critical battery condition"""
        self.logger.error(f"Sphero battery critical: {self.battery_level}%")
        await self._trigger_event('battery_critical', {'level': self.battery_level})
        
        # Switch to maintenance mode
        await self._switch_mode(SpheroMode.MAINTENANCE)
        
        # Clear all non-critical tasks
        self.task_queue = [task for task in self.task_queue if task.priority >= 9]
        
        # Add critical battery notification
        await self.add_task('notification', 9, data={
            'notification': {'type': 'error'}
        })
    
    async def _trigger_event(self, event_name: str, data: Any = None):
        """Trigger event callbacks"""
        if event_name in self.event_callbacks:
            for callback in self.event_callbacks[event_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"Error in event callback {event_name}: {e}")
    
    def add_event_callback(self, event_name: str, callback: Callable):
        """Add event callback"""
        if event_name not in self.event_callbacks:
            self.event_callbacks[event_name] = []
        self.event_callbacks[event_name].append(callback)
    
    async def scan_for_spheros(self) -> List[Dict[str, str]]:
        """Scan for available Sphero devices"""
        try:
            if not SPHERO_AVAILABLE:
                return []
            
            self.logger.info("Scanning for Sphero devices...")
            toys = scanner.find_toys(timeout=10)
            
            sphero_list = []
            for toy in toys:
                sphero_list.append({
                    'name': toy.name or 'Unknown Sphero',
                    'address': toy.address,
                    'type': 'Sphero Bolt' if 'bolt' in (toy.name or '').lower() else 'Sphero'
                })
            
            self.discovered_spheros = [(s['name'], s['address']) for s in sphero_list]
            self.logger.info(f"Found {len(sphero_list)} Sphero device(s)")
            
            return sphero_list
            
        except Exception as e:
            self.logger.error(f"Error scanning for Spheros: {e}")
            return []
    
    async def connect_to_specific_sphero(self, sphero_name: str) -> bool:
        """Connect to a specific Sphero by name"""
        try:
            self.target_sphero_name = sphero_name
            return await self._connect_to_sphero(sphero_name)
        except Exception as e:
            self.logger.error(f"Error connecting to specific Sphero: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current Sphero status"""
        return {
            'connected': self.is_connected,
            'mode': self.current_mode.value,
            'battery_level': self.battery_level,
            'sphero_name': self.sphero_toy.name if self.sphero_toy else None,
            'discovered_spheros': self.discovered_spheros,
            'current_task': {
                'id': self.current_task.task_id,
                'type': self.current_task.task_type,
                'priority': self.current_task.priority,
                'status': self.current_task.status
            } if self.current_task else None,
            'queue_length': len(self.task_queue),
            'performance_metrics': self.performance_metrics.copy(),
            'autonomous_mode': self.autonomous_mode
        }
    
    async def shutdown(self):
        """Shutdown the Sphero controller"""
        try:
            self.logger.info("Shutting down Enhanced Sphero Controller...")
            self.is_running = False
            
            # Complete current task
            if self.current_task:
                await self._interrupt_current_task()
            
            # Clear task queue
            self.task_queue.clear()
            
            # Disconnect from Sphero
            if self.sphero_toy and self.is_connected:
                await self.sphero_toy.disconnect()
            
            # Close simulator UI
            if self.simulator_ui:
                self.simulator_ui.stop()
            
            await self._trigger_event('disconnected')
            self.logger.info("Enhanced Sphero Controller shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during Sphero controller shutdown: {e}")