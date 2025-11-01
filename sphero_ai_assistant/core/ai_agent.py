"""
Autonomous AI Agent - Central intelligence for decision-making
"""

from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass

from .decision_engine import DecisionEngine
from .personality_core import PersonalityCore
from .memory_system import AIMemorySystem
from ..sphero import EnhancedSpheroController, LEDExpressionManager, EmotionType


@dataclass
class AIDecisionContext:
    """Context information for AI decision-making"""
    current_task: Optional[str] = None
    user_attention_level: float = 1.0
    sphero_battery_level: float = 100.0
    active_input_streams: list = None
    pending_expressions: list = None
    user_emotional_state: str = "neutral"
    system_load: float = 0.0
    priority_override: Optional[str] = None
    
    def __post_init__(self):
        if self.active_input_streams is None:
            self.active_input_streams = []
        if self.pending_expressions is None:
            self.pending_expressions = []


class AIAgent:
    """
    Central autonomous AI agent that makes intelligent decisions about system behavior
    Requirement 1.1: Auto-startup and initialization
    Requirement 2.2: Autonomous decision-making for Sphero usage
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.decision_engine = DecisionEngine()
        self.personality_core = PersonalityCore()
        self.memory_system = AIMemorySystem()
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        
        # Enhanced Sphero integration
        self.sphero_controller = None
        self.led_expression_manager = None
        
    async def initialize(self) -> bool:
        """
        Initialize the AI agent and all core components
        Requirement 1.1: System auto-launch and initialization
        """
        try:
            self.logger.info("Initializing AI Agent...")
            
            # Initialize core components
            self.decision_engine.initialize()
            self.personality_core.initialize()
            self.memory_system.initialize()
            
            # Initialize enhanced Sphero integration
            await self._initialize_sphero_integration()
            
            # Load user preferences and restrictions
            self._load_user_preferences()
            
            self.is_initialized = True
            self.logger.info("AI Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Agent: {e}")
            return False
    
    def make_autonomous_decision(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make intelligent decisions about system behavior
        Requirement 2.2: Autonomous decision-making based on context
        """
        if not self.is_initialized:
            raise RuntimeError("AI Agent not initialized")
            
        context = AIDecisionContext(**situation)
        
        # Use decision engine to evaluate situation
        decision = self.decision_engine.evaluate_situation(context)
        
        # Apply personality optimization
        optimized_decision = self.personality_core.optimize_for_growth(decision)
        
        # Store decision pattern in memory
        self.memory_system.store_decision_pattern(context, optimized_decision)
        
        return optimized_decision
    
    def optimize_for_user_growth(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize all interactions for maximum user growth
        Requirement 4.1: Therapeutic delivery and growth optimization
        """
        return self.personality_core.optimize_interaction(interaction)
    
    def create_tool_on_demand(self, user_request: str) -> Dict[str, Any]:
        """
        Create new tools dynamically based on user needs
        Requirement 2.3: Dynamic tool creation
        """
        tool_spec = self.decision_engine.analyze_tool_request(user_request)
        return self.decision_engine.create_dynamic_tool(tool_spec)
    
    async def _initialize_sphero_integration(self):
        """Initialize enhanced Sphero integration"""
        try:
            # Initialize enhanced Sphero controller
            self.sphero_controller = EnhancedSpheroController(self.decision_engine, self.config_manager)
            sphero_initialized = await self.sphero_controller.initialize()
            
            if sphero_initialized:
                # Initialize LED expression manager
                self.led_expression_manager = LEDExpressionManager(self.sphero_controller)
                
                # Set up event callbacks for Sphero integration
                self.sphero_controller.add_event_callback('connected', self._on_sphero_connected)
                self.sphero_controller.add_event_callback('disconnected', self._on_sphero_disconnected)
                self.sphero_controller.add_event_callback('battery_low', self._on_sphero_battery_low)
                self.sphero_controller.add_event_callback('task_completed', self._on_sphero_task_completed)
                
                self.logger.info("Enhanced Sphero integration initialized successfully")
            else:
                self.logger.warning("Sphero integration failed to initialize, continuing without Sphero")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Sphero integration: {e}")
            # Continue without Sphero integration
    
    async def _on_sphero_connected(self, data):
        """Handle Sphero connection event"""
        self.logger.info("Sphero connected - expressing greeting")
        if self.led_expression_manager:
            await self.led_expression_manager.express_emotion(
                emotion=EmotionType.HAPPY,
                intensity=0.8,
                duration=3.0
            )
    
    async def _on_sphero_disconnected(self, data):
        """Handle Sphero disconnection event"""
        self.logger.warning("Sphero disconnected")
        # Could trigger reconnection attempts or notifications
    
    async def _on_sphero_battery_low(self, data):
        """Handle Sphero low battery event"""
        battery_level = data.get('level', 0)
        self.logger.warning(f"Sphero battery low: {battery_level}%")
        
        # Store battery concern in memory
        self.memory_system.store_memory(
            "system_status",
            f"Sphero battery low at {battery_level}%",
            importance=7
        )
    
    async def _on_sphero_task_completed(self, task):
        """Handle Sphero task completion event"""
        self.logger.info(f"Sphero task completed: {task.task_type}")
        
        # Learn from task completion patterns
        self.memory_system.store_decision_pattern(
            {"task_type": task.task_type, "priority": task.priority},
            {"completed": True, "duration": (task.completed_at - task.started_at).total_seconds()}
        )
    
    async def express_ai_emotion(self, emotion: str, intensity: float = 0.7, context: dict = None):
        """
        Express AI emotion through Sphero LED patterns
        Requirement 2.3: AI creative communication through LED patterns
        """
        if not self.led_expression_manager:
            self.logger.warning("LED expression manager not available")
            return
        
        try:
            from ..sphero import EmotionType
            
            # Map string emotions to EmotionType enum
            emotion_map = {
                'happy': EmotionType.HAPPY,
                'excited': EmotionType.EXCITED,
                'calm': EmotionType.CALM,
                'focused': EmotionType.FOCUSED,
                'thinking': EmotionType.THINKING,
                'confused': EmotionType.CONFUSED,
                'concerned': EmotionType.CONCERNED,
                'celebrating': EmotionType.CELEBRATING,
                'working': EmotionType.WORKING,
                'listening': EmotionType.LISTENING
            }
            
            emotion_type = emotion_map.get(emotion.lower(), EmotionType.CALM)
            
            return await self.led_expression_manager.express_emotion(
                emotion=emotion_type,
                intensity=intensity,
                context=context
            )
            
        except Exception as e:
            self.logger.error(f"Failed to express AI emotion: {e}")
    
    async def express_ai_state(self, state: str, details: dict = None):
        """
        Express current AI state through Sphero
        Requirement 2.3: AI creative communication
        """
        if not self.led_expression_manager:
            return
        
        try:
            return await self.led_expression_manager.express_ai_state(state, details)
        except Exception as e:
            self.logger.error(f"Failed to express AI state: {e}")
    
    async def get_sphero_status(self) -> dict:
        """Get current Sphero status"""
        if not self.sphero_controller:
            return {'available': False}
        
        try:
            status = await self.sphero_controller.get_status()
            status['available'] = True
            return status
        except Exception as e:
            self.logger.error(f"Failed to get Sphero status: {e}")
            return {'available': False, 'error': str(e)}
    
    def _load_user_preferences(self):
        """Load user preferences from configuration"""
        preferences = self.config_manager.get_user_preferences()
        self.memory_system.load_preferences(preferences)
        
    async def shutdown(self):
        """Graceful shutdown of AI agent"""
        self.logger.info("Shutting down AI Agent...")
        
        # Shutdown Sphero integration
        if self.sphero_controller:
            await self.sphero_controller.shutdown()
        
        self.memory_system.save_state()
        self.is_initialized = False