"""
Decision Engine - Handles complex decision-making logic for multi-modal interactions
"""

from typing import Dict, List, Any
import logging
from dataclasses import dataclass
from enum import Enum


class Priority(Enum):
    """Priority levels for system demands"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Demand:
    """Represents a system demand requiring resources"""
    name: str
    priority: Priority
    resource_requirements: Dict[str, float]
    context: Dict[str, Any]


@dataclass
class Decision:
    """Represents an AI decision with rationale"""
    action: str
    priority: Priority
    resource_allocation: Dict[str, float]
    rationale: str
    confidence: float


class DecisionEngine:
    """
    Handles complex decision-making logic for autonomous system behavior
    Requirement 2.2: Autonomous decision-making for Sphero usage
    Requirement 2.6: Intelligent conflict resolution
    """
    
    def __init__(self):
        self.priority_matrix = {}
        self.context_weights = {
            'user_attention': 0.3,
            'task_importance': 0.25,
            'battery_level': 0.15,
            'system_load': 0.1,
            'emotional_state': 0.2
        }
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        
    def initialize(self) -> bool:
        """Initialize the decision engine"""
        try:
            self.logger.info("Initializing Decision Engine...")
            self._setup_priority_matrix()
            self.is_initialized = True
            self.logger.info("Decision Engine initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Decision Engine: {e}")
            return False
    
    def evaluate_situation(self, context) -> Decision:
        """
        Evaluate current situation and make autonomous decision
        Requirement 2.2: Autonomous decision-making based on context
        """
        if not self.is_initialized:
            raise RuntimeError("Decision Engine not initialized")
            
        # Analyze context factors
        context_score = self._calculate_context_score(context)
        
        # Determine optimal action
        action = self._determine_optimal_action(context, context_score)
        
        # Calculate resource allocation
        resource_allocation = self._calculate_resource_allocation(context, action)
        
        # Generate decision with rationale
        decision = Decision(
            action=action,
            priority=self._determine_priority(context_score),
            resource_allocation=resource_allocation,
            rationale=self._generate_rationale(context, action),
            confidence=context_score
        )
        
        self.logger.info(f"Decision made: {action} (confidence: {context_score:.2f})")
        return decision
    
    def evaluate_competing_demands(self, demands: List[Demand]) -> List[Demand]:
        """
        Evaluate and prioritize competing system demands
        Requirement 2.6: Intelligent conflict resolution
        """
        if not demands:
            return []
            
        # Score each demand based on priority and context
        scored_demands = []
        for demand in demands:
            score = self._score_demand(demand)
            scored_demands.append((demand, score))
        
        # Sort by score (highest first)
        scored_demands.sort(key=lambda x: x[1], reverse=True)
        
        return [demand for demand, score in scored_demands]
    
    def resolve_conflicts(self, conflicts: List[Dict]) -> Dict[str, Any]:
        """
        Resolve conflicts between expression and input needs
        Requirement 2.6: Intelligent conflict resolution between expression and input
        """
        if not conflicts:
            return {"resolution": "no_conflicts", "actions": []}
            
        # Analyze conflict types and severity
        conflict_analysis = self._analyze_conflicts(conflicts)
        
        # Generate resolution strategy
        resolution_strategy = self._generate_resolution_strategy(conflict_analysis)
        
        return {
            "resolution": resolution_strategy["type"],
            "actions": resolution_strategy["actions"],
            "rationale": resolution_strategy["rationale"]
        }
    
    def analyze_tool_request(self, user_request: str) -> Dict[str, Any]:
        """
        Analyze user request for dynamic tool creation
        Requirement 2.3: Dynamic tool creation
        """
        # Simple analysis for now - can be enhanced with NLP
        tool_spec = {
            "type": "unknown",
            "parameters": {},
            "priority": Priority.MEDIUM
        }
        
        # Basic pattern matching for common tools
        request_lower = user_request.lower()
        if "volume" in request_lower:
            tool_spec["type"] = "volume_knob"
            tool_spec["parameters"] = {"sensitivity": 1.0, "range": (0, 100)}
        elif "controller" in request_lower:
            tool_spec["type"] = "game_controller"
            tool_spec["parameters"] = {"buttons": 4, "analog_sticks": 2}
        
        return tool_spec
    
    def create_dynamic_tool(self, tool_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new tool based on specification
        Requirement 2.3: Dynamic tool creation on-the-fly
        """
        tool_config = {
            "name": f"dynamic_{tool_spec['type']}",
            "type": tool_spec["type"],
            "parameters": tool_spec.get("parameters", {}),
            "created_at": "now",  # Would use actual timestamp
            "status": "created"
        }
        
        self.logger.info(f"Created dynamic tool: {tool_config['name']}")
        return tool_config
    
    def _setup_priority_matrix(self):
        """Setup priority matrix for decision-making"""
        self.priority_matrix = {
            "user_interaction": Priority.CRITICAL,
            "task_assistance": Priority.HIGH,
            "expression": Priority.MEDIUM,
            "monitoring": Priority.LOW
        }
    
    def _calculate_context_score(self, context) -> float:
        """Calculate weighted context score"""
        score = 0.0
        
        # User attention factor
        score += context.user_attention_level * self.context_weights['user_attention']
        
        # Battery level factor (inverted - low battery reduces score)
        battery_factor = context.sphero_battery_level / 100.0
        score += battery_factor * self.context_weights['battery_level']
        
        # System load factor (inverted - high load reduces score)
        load_factor = max(0, 1.0 - context.system_load)
        score += load_factor * self.context_weights['system_load']
        
        # Emotional state factor
        emotion_factor = 0.8 if context.user_emotional_state == "positive" else 0.5
        score += emotion_factor * self.context_weights['emotional_state']
        
        return min(1.0, score)  # Cap at 1.0
    
    def _determine_optimal_action(self, context, context_score: float) -> str:
        """Determine optimal action based on context"""
        if context_score > 0.8:
            return "full_engagement"
        elif context_score > 0.6:
            return "moderate_engagement"
        elif context_score > 0.4:
            return "minimal_engagement"
        else:
            return "standby_mode"
    
    def _calculate_resource_allocation(self, context, action: str) -> Dict[str, float]:
        """Calculate resource allocation for the chosen action"""
        base_allocations = {
            "full_engagement": {"cpu": 0.8, "sphero": 1.0, "memory": 0.7},
            "moderate_engagement": {"cpu": 0.5, "sphero": 0.7, "memory": 0.5},
            "minimal_engagement": {"cpu": 0.3, "sphero": 0.4, "memory": 0.3},
            "standby_mode": {"cpu": 0.1, "sphero": 0.1, "memory": 0.2}
        }
        
        return base_allocations.get(action, {"cpu": 0.3, "sphero": 0.3, "memory": 0.3})
    
    def _determine_priority(self, context_score: float) -> Priority:
        """Determine priority based on context score"""
        if context_score > 0.8:
            return Priority.CRITICAL
        elif context_score > 0.6:
            return Priority.HIGH
        elif context_score > 0.4:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def _generate_rationale(self, context, action: str) -> str:
        """Generate human-readable rationale for the decision"""
        return f"Chose {action} based on user attention ({context.user_attention_level:.1f}), " \
               f"battery ({context.sphero_battery_level:.0f}%), and emotional state ({context.user_emotional_state})"
    
    def _score_demand(self, demand: Demand) -> float:
        """Score a demand for prioritization"""
        base_score = {
            Priority.CRITICAL: 1.0,
            Priority.HIGH: 0.8,
            Priority.MEDIUM: 0.6,
            Priority.LOW: 0.4
        }[demand.priority]
        
        # Adjust based on resource requirements
        resource_factor = sum(demand.resource_requirements.values()) / len(demand.resource_requirements)
        
        return base_score * (1.0 - resource_factor * 0.2)  # Slight penalty for high resource usage
    
    def _analyze_conflicts(self, conflicts: List[Dict]) -> Dict[str, Any]:
        """Analyze conflicts to understand their nature and severity"""
        return {
            "count": len(conflicts),
            "severity": "medium",  # Simplified for now
            "types": ["expression_vs_input"]  # Simplified for now
        }
    
    def _generate_resolution_strategy(self, conflict_analysis: Dict) -> Dict[str, Any]:
        """Generate strategy to resolve conflicts"""
        return {
            "type": "time_slice",
            "actions": ["alternate_expression_input"],
            "rationale": "Use time-slicing to balance expression and input needs"
        }