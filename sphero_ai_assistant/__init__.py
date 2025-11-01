"""
Sphero AI Assistant - Core System Foundation
A low-maintenance, productivity-focused AI assistant using Sphero Bolt
"""

__version__ = "1.0.0"
__author__ = "Sphero AI Assistant Team"

from .core import AIAgent, DecisionEngine
from .config import ConfigManager
from .startup import AutoStartupService

__all__ = [
    "AIAgent",
    "DecisionEngine", 
    "ConfigManager",
    "AutoStartupService"
]