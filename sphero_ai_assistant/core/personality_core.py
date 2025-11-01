"""
Personality Core - Handles therapeutic delivery and growth optimization
"""

from typing import Dict, Any
import logging


class PersonalityCore:
    """
    Manages AI personality for therapeutic delivery and user growth optimization
    Requirement 4.1: Therapeutic delivery in all statements
    Requirement 4.2: Frame negatives as probabilities, positives as certainties
    """
    
    def __init__(self):
        self.therapeutic_patterns = {}
        self.growth_strategies = {}
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        
    def initialize(self) -> bool:
        """Initialize personality core with therapeutic patterns"""
        try:
            self.logger.info("Initializing Personality Core...")
            self._setup_therapeutic_patterns()
            self._setup_growth_strategies()
            self.is_initialized = True
            self.logger.info("Personality Core initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Personality Core: {e}")
            return False
    
    def optimize_for_growth(self, decision: Any) -> Dict[str, Any]:
        """
        Optimize decision for maximum user growth
        Requirement 4.3: Prioritize actions that promote user growth
        """
        if not self.is_initialized:
            raise RuntimeError("Personality Core not initialized")
            
        # Convert decision to dict if it's a Decision object
        if hasattr(decision, '__dict__'):
            decision_dict = {
                'action': decision.action,
                'priority': decision.priority.name if hasattr(decision.priority, 'name') else str(decision.priority),
                'resource_allocation': decision.resource_allocation,
                'rationale': decision.rationale,
                'confidence': decision.confidence
            }
        else:
            decision_dict = decision.copy() if hasattr(decision, 'copy') else dict(decision)
        
        # Apply growth optimization to decision
        optimized_decision = decision_dict.copy()
        
        # Add growth-oriented messaging
        if 'rationale' in optimized_decision:
            optimized_decision['rationale'] = self._apply_therapeutic_framing(
                optimized_decision['rationale']
            )
        
        # Add growth opportunity identification
        optimized_decision['growth_opportunities'] = self._identify_growth_opportunities(decision_dict)
        
        return optimized_decision
    
    def optimize_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize interaction for therapeutic delivery and growth
        Requirement 4.1: Therapeutic delivery in all statements
        Requirement 4.4: Maintain positive framing possible
        """
        optimized = interaction.copy()
        
        # Apply therapeutic framing to all messages
        if 'message' in optimized:
            optimized['message'] = self._apply_therapeutic_framing(optimized['message'])
        
        # Ensure positive framing
        optimized = self._ensure_positive_framing(optimized)
        
        # Add growth elements
        optimized['growth_element'] = self._add_growth_element(interaction)
        
        return optimized
    
    def format_therapeutically(self, message: str) -> str:
        """
        Format message with therapeutic delivery
        Requirement 4.1: Therapeutic delivery in all statements
        """
        return self._apply_therapeutic_framing(message)
    
    def _setup_therapeutic_patterns(self):
        """Setup therapeutic communication patterns"""
        self.therapeutic_patterns = {
            'uncertainty_phrases': [
                "there's a possibility that",
                "it might be that",
                "one way to look at this is",
                "this could suggest"
            ],
            'certainty_phrases': [
                "you will",
                "this will definitely",
                "you can count on",
                "this ensures"
            ],
            'growth_phrases': [
                "this is an opportunity to",
                "you're developing",
                "this builds your",
                "you're strengthening"
            ]
        }
    
    def _setup_growth_strategies(self):
        """Setup growth optimization strategies"""
        self.growth_strategies = {
            'skill_building': {
                'focus': 'developing new capabilities',
                'messaging': 'building your expertise'
            },
            'confidence_building': {
                'focus': 'reinforcing positive outcomes',
                'messaging': 'strengthening your confidence'
            },
            'learning_acceleration': {
                'focus': 'optimizing learning opportunities',
                'messaging': 'expanding your knowledge'
            }
        }
    
    def _apply_therapeutic_framing(self, message: str) -> str:
        """
        Apply therapeutic framing to message
        Requirement 4.2: Frame negatives as probabilities, positives as certainties
        """
        # Simple implementation - can be enhanced with NLP
        therapeutic_message = message
        
        # Convert negative statements to probabilities
        negative_indicators = ['cannot', 'will not', 'impossible', 'failed']
        for indicator in negative_indicators:
            if indicator in therapeutic_message.lower():
                therapeutic_message = therapeutic_message.replace(
                    indicator, 
                    f"there's a possibility of challenges with"
                )
        
        # Strengthen positive statements
        positive_indicators = ['can', 'will', 'success', 'achieve']
        for indicator in positive_indicators:
            if indicator in therapeutic_message.lower():
                therapeutic_message = therapeutic_message.replace(
                    indicator,
                    f"{indicator} definitely"
                )
        
        return therapeutic_message
    
    def _ensure_positive_framing(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure interaction maintains positive framing
        Requirement 4.4: Maintain the most positive framing possible
        """
        # Add positive context to interactions
        if 'context' not in interaction:
            interaction['context'] = {}
        
        interaction['context']['positive_framing'] = True
        interaction['context']['growth_focused'] = True
        
        return interaction
    
    def _identify_growth_opportunities(self, decision: Dict[str, Any]) -> list:
        """Identify growth opportunities in the decision"""
        opportunities = []
        
        # Based on decision action, identify growth areas
        action = decision.get('action', '')
        
        if 'engagement' in action:
            opportunities.append('active_participation')
        if 'learning' in action:
            opportunities.append('knowledge_expansion')
        if 'challenge' in action:
            opportunities.append('skill_development')
        
        return opportunities
    
    def _add_growth_element(self, interaction: Dict[str, Any]) -> str:
        """Add growth element to interaction"""
        # Simple growth element based on interaction type
        interaction_type = interaction.get('type', 'general')
        
        growth_elements = {
            'task_assistance': 'building your productivity skills',
            'learning': 'expanding your knowledge base',
            'decision_support': 'strengthening your decision-making',
            'general': 'developing your capabilities'
        }
        
        return growth_elements.get(interaction_type, 'enhancing your growth')