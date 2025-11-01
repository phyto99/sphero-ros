"""
Tests for Core System Foundation and Auto-Startup (Task 1)
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from sphero_ai_assistant.config import ConfigManager
from sphero_ai_assistant.startup import AutoStartupService
from sphero_ai_assistant.core import AIAgent, DecisionEngine


class TestCoreFoundation(unittest.TestCase):
    """Test core system foundation components"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.test_dir) / "config"
        self.config_manager = ConfigManager(str(self.config_dir))
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization"""
        # Test initialization
        self.assertTrue(self.config_manager.initialize())
        self.assertTrue(self.config_manager.is_initialized)
        
        # Test config files are created
        self.assertTrue((self.config_dir / "system.json").exists())
        self.assertTrue((self.config_dir / "ui.json").exists())
        self.assertTrue((self.config_dir / "sphero.json").exists())
        self.assertTrue((self.config_dir / "user_preferences.json").exists())
    
    def test_system_config_management(self):
        """Test system configuration management"""
        self.config_manager.initialize()
        
        # Test getting system config
        system_config = self.config_manager.get_system_config()
        self.assertTrue(system_config.auto_startup)
        self.assertTrue(system_config.ollama_auto_init)
        
        # Test updating system config
        self.assertTrue(self.config_manager.update_system_config(auto_startup=False))
        updated_config = self.config_manager.get_system_config()
        self.assertFalse(updated_config.auto_startup)
    
    def test_startup_config(self):
        """Test startup configuration retrieval"""
        self.config_manager.initialize()
        
        startup_config = self.config_manager.get_startup_config()
        
        self.assertIn("auto_startup", startup_config)
        self.assertIn("ollama_auto_init", startup_config)
        self.assertIn("sphero_auto_connect", startup_config)
        self.assertIn("ui_auto_startup", startup_config)
        self.assertIn("monitoring_enabled", startup_config)
    
    def test_auto_startup_service_initialization(self):
        """Test auto-startup service initialization"""
        startup_service = AutoStartupService(self.config_manager)
        
        # Test initialization
        self.assertTrue(startup_service.initialize())
        self.assertTrue(startup_service.is_initialized)
    
    def test_ai_agent_initialization(self):
        """Test AI agent initialization"""
        self.config_manager.initialize()
        ai_agent = AIAgent(self.config_manager)
        
        # Test initialization
        self.assertTrue(ai_agent.initialize())
        self.assertTrue(ai_agent.is_initialized)
    
    def test_decision_engine_initialization(self):
        """Test decision engine initialization"""
        decision_engine = DecisionEngine()
        
        # Test initialization
        self.assertTrue(decision_engine.initialize())
        self.assertTrue(decision_engine.is_initialized)
    
    def test_autonomous_decision_making(self):
        """Test autonomous decision-making capability"""
        self.config_manager.initialize()
        ai_agent = AIAgent(self.config_manager)
        ai_agent.initialize()
        
        # Test decision making
        situation = {
            "current_task": "test_task",
            "user_attention_level": 0.8,
            "sphero_battery_level": 75.0,
            "user_emotional_state": "positive"
        }
        
        decision = ai_agent.make_autonomous_decision(situation)
        
        self.assertIn("action", decision)
        self.assertIn("priority", decision)
        self.assertIn("resource_allocation", decision)
        self.assertIn("rationale", decision)
    
    def test_config_validation(self):
        """Test configuration validation"""
        self.config_manager.initialize()
        
        validation_results = self.config_manager.validate_config()
        
        self.assertIn("system_config", validation_results)
        self.assertIn("ui_config", validation_results)
        self.assertIn("sphero_config", validation_results)
        self.assertIn("user_preferences", validation_results)
        
        # All should be valid with default configs
        self.assertTrue(all(validation_results.values()))


if __name__ == "__main__":
    unittest.main()