"""
AI Memory System - Persistent memory for user preferences and learning
"""

from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class AIMemoryEntry:
    """Memory entry for storing AI learning and user preferences"""
    timestamp: str
    entry_type: str  # 'preference', 'restriction', 'learning', 'pattern'
    content: Dict[str, Any]
    importance_score: float
    user_confirmation: bool
    expiry_date: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIMemoryEntry':
        """Create memory entry from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory entry to dictionary"""
        return asdict(self)


@dataclass
class UserPreferences:
    """User preferences and settings"""
    communication_languages: List[str]
    learning_goals: List[str]
    productivity_priorities: List[str]
    sphero_usage_preferences: Dict[str, Any]
    ai_personality_settings: Dict[str, Any]
    restriction_rules: List[Dict[str, Any]]
    
    @classmethod
    def default(cls) -> 'UserPreferences':
        """Create default user preferences"""
        return cls(
            communication_languages=['English'],
            learning_goals=[],
            productivity_priorities=[],
            sphero_usage_preferences={},
            ai_personality_settings={'therapeutic_mode': True},
            restriction_rules=[]
        )


class AIMemorySystem:
    """
    Persistent AI memory system for storing user preferences and restrictions
    Requirement 11.1: Store user instructions in persistent memory
    Requirement 11.2: Enforce user restrictions in future interactions
    Requirement 11.3: Apply user preferences consistently
    """
    
    def __init__(self, memory_file: str = "ai_memory.json"):
        self.memory_file = Path(memory_file)
        self.memory_entries: List[AIMemoryEntry] = []
        self.user_preferences = UserPreferences.default()
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        
    def initialize(self) -> bool:
        """Initialize memory system and load existing data"""
        try:
            self.logger.info("Initializing AI Memory System...")
            self._load_memory_from_file()
            self._cleanup_expired_entries()
            self.is_initialized = True
            self.logger.info("AI Memory System initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Memory System: {e}")
            return False
    
    def store_user_instruction(self, instruction: str, instruction_type: str = "preference") -> bool:
        """
        Store user instruction in persistent memory
        Requirement 11.1: Store user instructions in persistent memory
        """
        if not self.is_initialized:
            raise RuntimeError("Memory System not initialized")
            
        try:
            entry = AIMemoryEntry(
                timestamp=datetime.now().isoformat(),
                entry_type=instruction_type,
                content={"instruction": instruction},
                importance_score=0.8,  # High importance for direct instructions
                user_confirmation=True
            )
            
            self.memory_entries.append(entry)
            self._save_memory_to_file()
            
            self.logger.info(f"Stored user instruction: {instruction_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store user instruction: {e}")
            return False
    
    def store_user_restriction(self, restriction: Dict[str, Any]) -> bool:
        """
        Store user restriction for future enforcement
        Requirement 11.2: Enforce user restrictions in future interactions
        """
        try:
            entry = AIMemoryEntry(
                timestamp=datetime.now().isoformat(),
                entry_type="restriction",
                content=restriction,
                importance_score=1.0,  # Maximum importance for restrictions
                user_confirmation=True
            )
            
            self.memory_entries.append(entry)
            
            # Also add to user preferences for quick access
            self.user_preferences.restriction_rules.append(restriction)
            
            self._save_memory_to_file()
            
            self.logger.info(f"Stored user restriction: {restriction.get('name', 'unnamed')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store user restriction: {e}")
            return False
    
    def store_decision_pattern(self, context: Any, decision: Dict[str, Any]) -> bool:
        """
        Store decision pattern for learning
        Requirement 11.5: Memory importance scoring for prioritization
        """
        try:
            # Calculate importance based on decision confidence and context
            importance = decision.get('confidence', 0.5) * 0.7  # Learning patterns less critical
            
            entry = AIMemoryEntry(
                timestamp=datetime.now().isoformat(),
                entry_type="pattern",
                content={
                    "context_summary": self._summarize_context(context),
                    "decision": decision,
                    "outcome": "pending"  # Will be updated based on results
                },
                importance_score=importance,
                user_confirmation=False,
                expiry_date=(datetime.now() + timedelta(days=30)).isoformat()  # Patterns expire
            )
            
            self.memory_entries.append(entry)
            self._save_memory_to_file()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store decision pattern: {e}")
            return False
    
    def get_user_restrictions(self) -> List[Dict[str, Any]]:
        """
        Get all active user restrictions
        Requirement 11.2: Enforce user restrictions in future interactions
        """
        restrictions = []
        
        # Get from memory entries
        for entry in self.memory_entries:
            if entry.entry_type == "restriction" and entry.user_confirmation:
                restrictions.append(entry.content)
        
        # Get from user preferences
        restrictions.extend(self.user_preferences.restriction_rules)
        
        return restrictions
    
    def get_user_preferences(self) -> UserPreferences:
        """
        Get current user preferences
        Requirement 11.3: Apply user preferences consistently
        """
        return self.user_preferences
    
    def update_preference(self, preference_type: str, value: Any) -> bool:
        """
        Update specific user preference
        Requirement 11.3: Apply user preferences consistently
        """
        try:
            if hasattr(self.user_preferences, preference_type):
                setattr(self.user_preferences, preference_type, value)
                
                # Also store as memory entry
                self.store_user_instruction(
                    f"Updated {preference_type} to {value}",
                    "preference_update"
                )
                
                self.logger.info(f"Updated preference: {preference_type}")
                return True
            else:
                self.logger.warning(f"Unknown preference type: {preference_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update preference: {e}")
            return False
    
    def load_preferences(self, preferences: Dict[str, Any]):
        """Load preferences from configuration"""
        try:
            for key, value in preferences.items():
                if hasattr(self.user_preferences, key):
                    setattr(self.user_preferences, key, value)
            
            self.logger.info("Loaded user preferences from configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to load preferences: {e}")
    
    def resolve_memory_conflicts(self) -> Dict[str, Any]:
        """
        Resolve conflicts between memory entries
        Requirement 11.5: Memory importance scoring for prioritization
        """
        conflicts = self._identify_conflicts()
        resolutions = {}
        
        for conflict_type, conflicting_entries in conflicts.items():
            # Sort by importance score and recency
            sorted_entries = sorted(
                conflicting_entries,
                key=lambda x: (x.importance_score, x.timestamp),
                reverse=True
            )
            
            # Keep the most important and recent entry
            winner = sorted_entries[0]
            resolutions[conflict_type] = winner.content
            
            self.logger.info(f"Resolved conflict for {conflict_type}")
        
        return resolutions
    
    def save_state(self):
        """Save current memory state to file"""
        self._save_memory_to_file()
    
    def _load_memory_from_file(self):
        """Load memory entries from file"""
        if not self.memory_file.exists():
            self.logger.info("No existing memory file found, starting fresh")
            return
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load memory entries
            if 'memory_entries' in data:
                self.memory_entries = [
                    AIMemoryEntry.from_dict(entry) 
                    for entry in data['memory_entries']
                ]
            
            # Load user preferences
            if 'user_preferences' in data:
                prefs_data = data['user_preferences']
                self.user_preferences = UserPreferences(**prefs_data)
            
            self.logger.info(f"Loaded {len(self.memory_entries)} memory entries")
            
        except Exception as e:
            self.logger.error(f"Failed to load memory from file: {e}")
    
    def _save_memory_to_file(self):
        """Save memory entries to file"""
        try:
            data = {
                'memory_entries': [entry.to_dict() for entry in self.memory_entries],
                'user_preferences': asdict(self.user_preferences),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Failed to save memory to file: {e}")
    
    def _cleanup_expired_entries(self):
        """Remove expired memory entries"""
        current_time = datetime.now()
        initial_count = len(self.memory_entries)
        
        self.memory_entries = [
            entry for entry in self.memory_entries
            if not entry.expiry_date or 
            datetime.fromisoformat(entry.expiry_date) > current_time
        ]
        
        removed_count = initial_count - len(self.memory_entries)
        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} expired memory entries")
    
    def _summarize_context(self, context: Any) -> Dict[str, Any]:
        """Create summary of context for storage"""
        if hasattr(context, '__dict__'):
            return {
                'user_attention': getattr(context, 'user_attention_level', 0.5),
                'battery_level': getattr(context, 'sphero_battery_level', 100.0),
                'emotional_state': getattr(context, 'user_emotional_state', 'neutral')
            }
        return {"context": str(context)}
    
    def _identify_conflicts(self) -> Dict[str, List[AIMemoryEntry]]:
        """Identify conflicting memory entries"""
        conflicts = {}
        
        # Group entries by type and look for conflicts
        by_type = {}
        for entry in self.memory_entries:
            if entry.entry_type not in by_type:
                by_type[entry.entry_type] = []
            by_type[entry.entry_type].append(entry)
        
        # Simple conflict detection - entries of same type with different content
        for entry_type, entries in by_type.items():
            if len(entries) > 1 and entry_type in ['preference', 'restriction']:
                conflicts[entry_type] = entries
        
        return conflicts