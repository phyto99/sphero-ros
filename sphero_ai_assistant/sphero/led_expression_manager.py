"""
LED Expression Manager - AI creative communication through LED patterns
"""

import logging
import asyncio
import math
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

try:
    from spherov2.types import Color
    SPHERO_AVAILABLE = True
except ImportError:
    SPHERO_AVAILABLE = False
    class Color:
        def __init__(self, r, g, b): pass


class EmotionType(Enum):
    """AI emotion types for expression"""
    HAPPY = "happy"
    EXCITED = "excited"
    CALM = "calm"
    FOCUSED = "focused"
    THINKING = "thinking"
    CONFUSED = "confused"
    CONCERNED = "concerned"
    CELEBRATING = "celebrating"
    WORKING = "working"
    LISTENING = "listening"


class ExpressionPattern(Enum):
    """LED expression patterns"""
    SOLID = "solid"
    PULSE = "pulse"
    BREATHE = "breathe"
    RAINBOW = "rainbow"
    SPARKLE = "sparkle"
    WAVE = "wave"
    HEARTBEAT = "heartbeat"
    THINKING_DOTS = "thinking_dots"
    CELEBRATION = "celebration"
    ALERT = "alert"


class LEDExpressionManager:
    """
    LED Expression Manager for AI creative communication through LED patterns
    Requirement 2.3: Create LED Expression Manager for AI creative communication
    """
    
    def __init__(self, sphero_controller):
        self.sphero_controller = sphero_controller
        self.logger = logging.getLogger(__name__)
        
        # Expression state
        self.current_expression = None
        self.is_expressing = False
        self.expression_task = None
        
        # Color palettes for different emotions
        self.emotion_colors = {
            EmotionType.HAPPY: [(255, 255, 0), (255, 165, 0), (255, 192, 203)],  # Yellow, Orange, Pink
            EmotionType.EXCITED: [(255, 0, 255), (255, 20, 147), (255, 69, 0)],  # Magenta, Deep Pink, Red-Orange
            EmotionType.CALM: [(0, 191, 255), (135, 206, 235), (173, 216, 230)],  # Deep Sky Blue, Sky Blue, Light Blue
            EmotionType.FOCUSED: [(0, 255, 0), (50, 205, 50), (34, 139, 34)],    # Green, Lime Green, Forest Green
            EmotionType.THINKING: [(138, 43, 226), (147, 112, 219), (186, 85, 211)],  # Blue Violet, Medium Orchid, Medium Orchid
            EmotionType.CONFUSED: [(255, 165, 0), (255, 140, 0), (255, 215, 0)],  # Orange, Dark Orange, Gold
            EmotionType.CONCERNED: [(255, 255, 0), (255, 215, 0), (255, 69, 0)],  # Yellow, Gold, Red-Orange
            EmotionType.CELEBRATING: [(255, 0, 255), (0, 255, 255), (255, 255, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)],  # Rainbow
            EmotionType.WORKING: [(0, 100, 255), (0, 150, 255), (0, 200, 255)],   # Blue variations
            EmotionType.LISTENING: [(255, 255, 255), (200, 200, 255), (150, 150, 255)]  # White to light blue
        }
        
        # Pattern configurations
        self.pattern_configs = {
            ExpressionPattern.PULSE: {'speed': 1.0, 'intensity': 1.0},
            ExpressionPattern.BREATHE: {'speed': 0.5, 'intensity': 0.8},
            ExpressionPattern.RAINBOW: {'speed': 1.5, 'intensity': 1.0},
            ExpressionPattern.SPARKLE: {'speed': 2.0, 'intensity': 0.9},
            ExpressionPattern.WAVE: {'speed': 1.2, 'intensity': 0.7},
            ExpressionPattern.HEARTBEAT: {'speed': 1.0, 'intensity': 1.0},
            ExpressionPattern.THINKING_DOTS: {'speed': 0.8, 'intensity': 0.6},
            ExpressionPattern.CELEBRATION: {'speed': 3.0, 'intensity': 1.0},
            ExpressionPattern.ALERT: {'speed': 4.0, 'intensity': 1.0}
        }
        
        # Expression history for learning
        self.expression_history = []
        self.max_history = 100
        
        # Context awareness
        self.current_context = {
            'user_activity': 'unknown',
            'time_of_day': 'day',
            'system_load': 'normal',
            'user_mood': 'neutral'
        }
    
    async def express_emotion(self, emotion: EmotionType, intensity: float = 1.0, 
                            duration: Optional[float] = None, context: Optional[Dict] = None) -> str:
        """
        Express an AI emotion through LED patterns
        
        Args:
            emotion: The emotion to express
            intensity: Expression intensity (0.0 to 1.0)
            duration: How long to express (None for indefinite)
            context: Additional context for expression adaptation
            
        Returns:
            Expression ID for tracking
        """
        try:
            # Update context if provided
            if context:
                self.current_context.update(context)
            
            # Choose appropriate pattern and colors for emotion
            pattern = self._select_pattern_for_emotion(emotion, intensity)
            colors = self._select_colors_for_emotion(emotion, intensity)
            
            # Adapt expression based on context
            pattern, colors = self._adapt_expression_to_context(pattern, colors, emotion)
            
            # Create expression task
            expression_id = f"expr_{datetime.now().timestamp()}"
            
            # Add to Sphero task queue
            task_id = await self.sphero_controller.add_task(
                task_type="led_expression",
                priority=self._calculate_expression_priority(emotion, intensity),
                duration=duration,
                data={
                    'expression': {
                        'id': expression_id,
                        'emotion': emotion.value,
                        'pattern': pattern.value,
                        'colors': colors,
                        'intensity': intensity,
                        'context': self.current_context.copy()
                    }
                }
            )
            
            # Record expression
            self._record_expression(expression_id, emotion, pattern, colors, intensity, context)
            
            self.logger.info(f"Expressing emotion: {emotion.value} with pattern: {pattern.value}")
            return expression_id
            
        except Exception as e:
            self.logger.error(f"Failed to express emotion {emotion.value}: {e}")
            raise
    
    async def express_message(self, message_type: str, content: str, urgency: int = 5) -> str:
        """
        Express a message through LED patterns
        
        Args:
            message_type: Type of message (info, success, warning, error, etc.)
            content: Message content for context
            urgency: Message urgency (1-10)
            
        Returns:
            Expression ID
        """
        try:
            # Map message types to emotions and patterns
            message_emotion_map = {
                'info': (EmotionType.CALM, ExpressionPattern.PULSE),
                'success': (EmotionType.HAPPY, ExpressionPattern.CELEBRATION),
                'warning': (EmotionType.CONCERNED, ExpressionPattern.ALERT),
                'error': (EmotionType.CONCERNED, ExpressionPattern.ALERT),
                'thinking': (EmotionType.THINKING, ExpressionPattern.THINKING_DOTS),
                'working': (EmotionType.WORKING, ExpressionPattern.WAVE),
                'listening': (EmotionType.LISTENING, ExpressionPattern.BREATHE),
                'celebrating': (EmotionType.CELEBRATING, ExpressionPattern.CELEBRATION)
            }
            
            emotion, pattern = message_emotion_map.get(message_type, (EmotionType.CALM, ExpressionPattern.PULSE))
            
            # Calculate duration based on urgency and content length
            base_duration = 3.0
            urgency_multiplier = urgency / 5.0
            content_multiplier = min(len(content) / 50.0, 2.0)
            duration = base_duration * urgency_multiplier * content_multiplier
            
            # Express the message
            return await self.express_emotion(
                emotion=emotion,
                intensity=min(urgency / 10.0, 1.0),
                duration=duration,
                context={
                    'message_type': message_type,
                    'content_length': len(content),
                    'urgency': urgency
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to express message: {e}")
            raise
    
    async def express_ai_state(self, state: str, details: Optional[Dict] = None) -> str:
        """
        Express current AI state through LED patterns
        
        Args:
            state: AI state (processing, idle, learning, responding, etc.)
            details: Additional state details
            
        Returns:
            Expression ID
        """
        try:
            # Map AI states to emotions and patterns
            state_emotion_map = {
                'processing': (EmotionType.THINKING, ExpressionPattern.THINKING_DOTS),
                'idle': (EmotionType.CALM, ExpressionPattern.BREATHE),
                'learning': (EmotionType.FOCUSED, ExpressionPattern.WAVE),
                'responding': (EmotionType.WORKING, ExpressionPattern.PULSE),
                'listening': (EmotionType.LISTENING, ExpressionPattern.BREATHE),
                'analyzing': (EmotionType.FOCUSED, ExpressionPattern.SPARKLE),
                'creating': (EmotionType.EXCITED, ExpressionPattern.RAINBOW),
                'helping': (EmotionType.HAPPY, ExpressionPattern.PULSE),
                'error': (EmotionType.CONCERNED, ExpressionPattern.ALERT)
            }
            
            emotion, pattern = state_emotion_map.get(state, (EmotionType.CALM, ExpressionPattern.SOLID))
            
            # Determine duration based on state
            state_durations = {
                'processing': None,  # Indefinite until processing complete
                'idle': None,        # Indefinite until new activity
                'learning': 10.0,    # Learning sessions
                'responding': 5.0,   # Response generation
                'listening': None,   # Indefinite while listening
                'analyzing': 8.0,    # Analysis tasks
                'creating': 15.0,    # Creative tasks
                'helping': 3.0,      # Quick help confirmations
                'error': 2.0         # Brief error notifications
            }
            
            duration = state_durations.get(state, 5.0)
            
            return await self.express_emotion(
                emotion=emotion,
                intensity=0.7,
                duration=duration,
                context={
                    'ai_state': state,
                    'state_details': details or {}
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to express AI state {state}: {e}")
            raise
    
    async def create_custom_expression(self, colors: List[Tuple[int, int, int]], 
                                     pattern: ExpressionPattern, duration: float = 5.0,
                                     intensity: float = 1.0) -> str:
        """
        Create a custom LED expression
        
        Args:
            colors: List of RGB color tuples
            pattern: Expression pattern to use
            duration: Expression duration
            intensity: Expression intensity
            
        Returns:
            Expression ID
        """
        try:
            expression_id = f"custom_{datetime.now().timestamp()}"
            
            task_id = await self.sphero_controller.add_task(
                task_type="led_expression",
                priority=5,  # Medium priority for custom expressions
                duration=duration,
                data={
                    'expression': {
                        'id': expression_id,
                        'emotion': 'custom',
                        'pattern': pattern.value,
                        'colors': colors,
                        'intensity': intensity,
                        'context': {'custom': True}
                    }
                }
            )
            
            self.logger.info(f"Created custom expression: {pattern.value} with {len(colors)} colors")
            return expression_id
            
        except Exception as e:
            self.logger.error(f"Failed to create custom expression: {e}")
            raise
    
    def _select_pattern_for_emotion(self, emotion: EmotionType, intensity: float) -> ExpressionPattern:
        """Select appropriate pattern for emotion and intensity"""
        # Base patterns for emotions
        emotion_patterns = {
            EmotionType.HAPPY: [ExpressionPattern.PULSE, ExpressionPattern.SPARKLE],
            EmotionType.EXCITED: [ExpressionPattern.CELEBRATION, ExpressionPattern.RAINBOW],
            EmotionType.CALM: [ExpressionPattern.BREATHE, ExpressionPattern.WAVE],
            EmotionType.FOCUSED: [ExpressionPattern.SOLID, ExpressionPattern.PULSE],
            EmotionType.THINKING: [ExpressionPattern.THINKING_DOTS, ExpressionPattern.PULSE],
            EmotionType.CONFUSED: [ExpressionPattern.SPARKLE, ExpressionPattern.WAVE],
            EmotionType.CONCERNED: [ExpressionPattern.ALERT, ExpressionPattern.PULSE],
            EmotionType.CELEBRATING: [ExpressionPattern.CELEBRATION, ExpressionPattern.RAINBOW],
            EmotionType.WORKING: [ExpressionPattern.WAVE, ExpressionPattern.PULSE],
            EmotionType.LISTENING: [ExpressionPattern.BREATHE, ExpressionPattern.PULSE]
        }
        
        patterns = emotion_patterns.get(emotion, [ExpressionPattern.SOLID])
        
        # Select pattern based on intensity
        if intensity > 0.8:
            # High intensity - prefer more dynamic patterns
            dynamic_patterns = [p for p in patterns if p in [
                ExpressionPattern.CELEBRATION, ExpressionPattern.RAINBOW, 
                ExpressionPattern.SPARKLE, ExpressionPattern.ALERT
            ]]
            if dynamic_patterns:
                return random.choice(dynamic_patterns)
        elif intensity < 0.3:
            # Low intensity - prefer subtle patterns
            subtle_patterns = [p for p in patterns if p in [
                ExpressionPattern.SOLID, ExpressionPattern.BREATHE, ExpressionPattern.PULSE
            ]]
            if subtle_patterns:
                return random.choice(subtle_patterns)
        
        return random.choice(patterns)
    
    def _select_colors_for_emotion(self, emotion: EmotionType, intensity: float) -> List[Tuple[int, int, int]]:
        """Select appropriate colors for emotion and intensity"""
        base_colors = self.emotion_colors.get(emotion, [(255, 255, 255)])
        
        # Adjust colors based on intensity
        adjusted_colors = []
        for r, g, b in base_colors:
            # Scale colors by intensity
            r = int(r * intensity)
            g = int(g * intensity)
            b = int(b * intensity)
            adjusted_colors.append((r, g, b))
        
        return adjusted_colors
    
    def _adapt_expression_to_context(self, pattern: ExpressionPattern, colors: List[Tuple[int, int, int]], 
                                   emotion: EmotionType) -> Tuple[ExpressionPattern, List[Tuple[int, int, int]]]:
        """Adapt expression based on current context"""
        adapted_pattern = pattern
        adapted_colors = colors.copy()
        
        # Adapt based on time of day
        if self.current_context.get('time_of_day') == 'night':
            # Reduce brightness for night time
            adapted_colors = [(int(r * 0.5), int(g * 0.5), int(b * 0.5)) for r, g, b in adapted_colors]
            
            # Prefer calmer patterns at night
            if pattern in [ExpressionPattern.CELEBRATION, ExpressionPattern.ALERT]:
                adapted_pattern = ExpressionPattern.BREATHE
        
        # Adapt based on user activity
        user_activity = self.current_context.get('user_activity', 'unknown')
        if user_activity == 'focused_work':
            # Use subtle expressions during focused work
            if pattern in [ExpressionPattern.CELEBRATION, ExpressionPattern.RAINBOW]:
                adapted_pattern = ExpressionPattern.PULSE
            adapted_colors = [(int(r * 0.7), int(g * 0.7), int(b * 0.7)) for r, g, b in adapted_colors]
        
        # Adapt based on system load
        if self.current_context.get('system_load') == 'high':
            # Use simpler patterns when system is busy
            if pattern in [ExpressionPattern.CELEBRATION, ExpressionPattern.RAINBOW, ExpressionPattern.SPARKLE]:
                adapted_pattern = ExpressionPattern.SOLID
        
        return adapted_pattern, adapted_colors
    
    def _calculate_expression_priority(self, emotion: EmotionType, intensity: float) -> int:
        """Calculate priority for expression task"""
        base_priority = 5
        
        # Adjust based on emotion urgency
        emotion_urgency = {
            EmotionType.CONCERNED: 8,
            EmotionType.CELEBRATING: 7,
            EmotionType.EXCITED: 6,
            EmotionType.HAPPY: 5,
            EmotionType.WORKING: 4,
            EmotionType.THINKING: 4,
            EmotionType.FOCUSED: 3,
            EmotionType.LISTENING: 3,
            EmotionType.CALM: 2,
            EmotionType.CONFUSED: 6
        }
        
        priority = emotion_urgency.get(emotion, base_priority)
        
        # Adjust based on intensity
        intensity_adjustment = int(intensity * 2)  # 0-2 adjustment
        priority += intensity_adjustment
        
        return min(max(priority, 1), 10)  # Clamp to 1-10 range
    
    def _record_expression(self, expression_id: str, emotion: EmotionType, pattern: ExpressionPattern,
                          colors: List[Tuple[int, int, int]], intensity: float, context: Optional[Dict]):
        """Record expression for learning and analysis"""
        record = {
            'id': expression_id,
            'timestamp': datetime.now().isoformat(),
            'emotion': emotion.value,
            'pattern': pattern.value,
            'colors': colors,
            'intensity': intensity,
            'context': context or {},
            'system_context': self.current_context.copy()
        }
        
        self.expression_history.append(record)
        
        # Maintain history size
        if len(self.expression_history) > self.max_history:
            self.expression_history.pop(0)
    
    async def stop_current_expression(self):
        """Stop the current expression"""
        try:
            # This would need to be coordinated with the Sphero controller
            # to interrupt the current LED expression task
            if self.sphero_controller.current_task and \
               self.sphero_controller.current_task.task_type == "led_expression":
                # The controller will handle task interruption
                pass
            
            self.logger.info("Stopped current LED expression")
            
        except Exception as e:
            self.logger.error(f"Failed to stop current expression: {e}")
    
    def update_context(self, context_updates: Dict[str, Any]):
        """Update context for expression adaptation"""
        self.current_context.update(context_updates)
        self.logger.debug(f"Updated expression context: {context_updates}")
    
    def get_expression_history(self, limit: int = 10) -> List[Dict]:
        """Get recent expression history"""
        return self.expression_history[-limit:] if self.expression_history else []
    
    def get_emotion_statistics(self) -> Dict[str, Any]:
        """Get statistics about expressed emotions"""
        if not self.expression_history:
            return {}
        
        emotion_counts = {}
        pattern_counts = {}
        total_expressions = len(self.expression_history)
        
        for record in self.expression_history:
            emotion = record['emotion']
            pattern = record['pattern']
            
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        return {
            'total_expressions': total_expressions,
            'emotion_distribution': {k: v/total_expressions for k, v in emotion_counts.items()},
            'pattern_distribution': {k: v/total_expressions for k, v in pattern_counts.items()},
            'most_common_emotion': max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None,
            'most_common_pattern': max(pattern_counts.items(), key=lambda x: x[1])[0] if pattern_counts else None
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current LED expression manager status"""
        return {
            'is_expressing': self.is_expressing,
            'current_expression': self.current_expression,
            'context': self.current_context.copy(),
            'history_count': len(self.expression_history),
            'available_emotions': [e.value for e in EmotionType],
            'available_patterns': [p.value for p in ExpressionPattern]
        }