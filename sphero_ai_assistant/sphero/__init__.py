"""
Sphero Integration Module - Enhanced Sphero control with autonomous decision-making
"""

from .enhanced_sphero_controller import EnhancedSpheroController, SpheroMode, SpheroTask
from .led_expression_manager import LEDExpressionManager, EmotionType, ExpressionPattern

__all__ = [
    'EnhancedSpheroController',
    'SpheroMode', 
    'SpheroTask',
    'LEDExpressionManager',
    'EmotionType',
    'ExpressionPattern'
]