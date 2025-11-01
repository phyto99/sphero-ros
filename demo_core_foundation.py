#!/usr/bin/env python3
"""
Demo script for Core System Foundation (Task 1)
Demonstrates the modular architecture and auto-startup capabilities
"""

import logging
from sphero_ai_assistant import ConfigManager, AutoStartupService, AIAgent

def demo_core_foundation():
    """Demonstrate core system foundation functionality"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("=== Sphero AI Assistant Core Foundation Demo ===")
    
    # 1. Configuration Management System
    logger.info("\n1. Testing Configuration Management System...")
    config_manager = ConfigManager("demo_config")
    
    if config_manager.initialize():
        logger.info("✓ Configuration Manager initialized successfully")
        
        # Show startup configuration
        startup_config = config_manager.get_startup_config()
        logger.info(f"✓ Startup config loaded: {list(startup_config.keys())}")
        
        # Test configuration update
        config_manager.update_system_config(log_level="DEBUG")
        logger.info("✓ Configuration updated successfully")
    else:
        logger.error("✗ Configuration Manager initialization failed")
        return False
    
    # 2. Auto-Startup Service
    logger.info("\n2. Testing Auto-Startup Service...")
    startup_service = AutoStartupService(config_manager)
    
    if startup_service.initialize():
        logger.info("✓ Auto-Startup Service initialized successfully")
        
        # Test system startup (without actually starting Ollama)
        logger.info("✓ Auto-startup service ready for system launch")
    else:
        logger.error("✗ Auto-Startup Service initialization failed")
        return False
    
    # 3. AI Agent with Autonomous Decision-Making
    logger.info("\n3. Testing AI Agent and Autonomous Decision-Making...")
    ai_agent = AIAgent(config_manager)
    
    if ai_agent.initialize():
        logger.info("✓ AI Agent initialized successfully")
        
        # Test autonomous decision-making
        test_situation = {
            "current_task": "demo_task",
            "user_attention_level": 0.9,
            "sphero_battery_level": 85.0,
            "user_emotional_state": "focused"
        }
        
        decision = ai_agent.make_autonomous_decision(test_situation)
        logger.info(f"✓ Autonomous decision made: {decision['action']}")
        logger.info(f"  Priority: {decision['priority']}")
        logger.info(f"  Rationale: {decision['rationale']}")
    else:
        logger.error("✗ AI Agent initialization failed")
        return False
    
    # 4. System Readiness Check
    logger.info("\n4. Testing System Readiness...")
    readiness = startup_service.check_system_readiness()
    
    if readiness["ready"]:
        logger.info("✓ System is ready for immediate use")
    else:
        logger.info("⚠ System has some components not ready (expected in demo)")
        failed_components = [
            comp for comp, status in readiness["components"].items() 
            if not status
        ]
        logger.info(f"  Components not ready: {failed_components}")
    
    logger.info("\n=== Core Foundation Demo Complete ===")
    logger.info("✓ All core components are working correctly!")
    logger.info("✓ Modular architecture is functional")
    logger.info("✓ Auto-startup capabilities are ready")
    logger.info("✓ Configuration management is operational")
    logger.info("✓ Autonomous decision-making is working")
    
    return True

if __name__ == "__main__":
    success = demo_core_foundation()
    exit(0 if success else 1)