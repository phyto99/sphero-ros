"""
Auto-Startup Service - Launches system on boot and initializes all components
"""

import os
import sys
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..config import ConfigManager
from .ollama_initializer import OllamaInitializer


class AutoStartupService:
    """
    Auto-startup service that launches on system boot and initializes Ollama
    Requirement 1.1: System automatically launches and initializes all components including Ollama AI
    Requirement 1.3: Auto-startup service configuration
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.ollama_initializer = OllamaInitializer()
        self.logger = logging.getLogger(__name__)
        self.startup_status = {
            "config_manager": False,
            "ollama": False,
            "ui": False,
            "sphero": False,
            "monitoring": False
        }
        self.is_initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize auto-startup service
        Requirement 1.1: System auto-launch and initialization
        """
        try:
            self.logger.info("Initializing Auto-Startup Service...")
            
            # Initialize configuration manager first
            if not self.config_manager.initialize():
                self.logger.error("Failed to initialize configuration manager")
                return False
            
            self.startup_status["config_manager"] = True
            self.is_initialized = True
            
            self.logger.info("Auto-Startup Service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Auto-Startup Service: {e}")
            return False
    
    def start_system(self) -> Dict[str, bool]:
        """
        Start all system components in proper order
        Requirement 1.1: Auto-launch and initialize all components
        Requirement 1.3: Visual feedback on initialization progress
        """
        if not self.is_initialized:
            raise RuntimeError("Auto-Startup Service not initialized")
        
        self.logger.info("Starting Sphero AI Assistant system...")
        
        startup_config = self.config_manager.get_startup_config()
        
        # Start components in dependency order
        startup_sequence = [
            ("ollama", self._start_ollama, startup_config.get("ollama_auto_init", True)),
            ("ui", self._start_ui, startup_config.get("ui_auto_startup", True)),
            ("sphero", self._start_sphero, startup_config.get("sphero_auto_connect", True)),
            ("monitoring", self._start_monitoring, startup_config.get("monitoring_enabled", True))
        ]
        
        for component_name, start_func, should_start in startup_sequence:
            if should_start:
                self.logger.info(f"Starting {component_name}...")
                try:
                    success = start_func()
                    self.startup_status[component_name] = success
                    
                    if success:
                        self.logger.info(f"{component_name} started successfully")
                    else:
                        self.logger.warning(f"Failed to start {component_name}")
                        
                except Exception as e:
                    self.logger.error(f"Error starting {component_name}: {e}")
                    self.startup_status[component_name] = False
            else:
                self.logger.info(f"Skipping {component_name} (disabled in config)")
        
        # Log final startup status
        successful_components = sum(1 for status in self.startup_status.values() if status)
        total_components = len(self.startup_status)
        
        self.logger.info(f"System startup complete: {successful_components}/{total_components} components started")
        
        return self.startup_status.copy()
    
    def get_startup_status(self) -> Dict[str, bool]:
        """
        Get current startup status of all components
        Requirement 1.3: Visual feedback on initialization progress
        """
        return self.startup_status.copy()
    
    def install_startup_service(self) -> bool:
        """
        Install system startup service (Windows)
        Requirement 1.1: Auto-startup service that launches on system boot
        """
        try:
            # Create startup script for Windows
            startup_script = self._create_windows_startup_script()
            
            if startup_script:
                self.logger.info("Startup service installed successfully")
                return True
            else:
                self.logger.error("Failed to install startup service")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to install startup service: {e}")
            return False
    
    def uninstall_startup_service(self) -> bool:
        """Remove system startup service"""
        try:
            startup_folder = Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            startup_file = startup_folder / "SpheroAIAssistant.bat"
            
            if startup_file.exists():
                startup_file.unlink()
                self.logger.info("Startup service uninstalled successfully")
                return True
            else:
                self.logger.info("Startup service was not installed")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to uninstall startup service: {e}")
            return False
    
    def check_system_readiness(self) -> Dict[str, Any]:
        """
        Check if system is ready for immediate use
        Requirement 1.3: Ready for immediate use after startup
        """
        readiness_checks = {
            "config_loaded": self.startup_status.get("config_manager", False),
            "ollama_ready": self._check_ollama_readiness(),
            "ui_responsive": self._check_ui_readiness(),
            "sphero_connected": self._check_sphero_readiness(),
            "monitoring_active": self._check_monitoring_readiness()
        }
        
        overall_ready = all(readiness_checks.values())
        
        return {
            "ready": overall_ready,
            "components": readiness_checks,
            "startup_time": self._calculate_startup_time()
        }
    
    def _start_ollama(self) -> bool:
        """
        Start Ollama AI system
        Requirement 1.1: Initialize Ollama AI
        """
        try:
            return self.ollama_initializer.initialize_ollama()
        except Exception as e:
            self.logger.error(f"Failed to start Ollama: {e}")
            return False
    
    def _start_ui(self) -> bool:
        """
        Start UI dashboard
        Requirement 1.2: Perfect UI auto-startup
        """
        try:
            # For now, just mark as started - actual UI implementation in later tasks
            self.logger.info("UI startup placeholder - will be implemented in Task 2")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start UI: {e}")
            return False
    
    def _start_sphero(self) -> bool:
        """
        Start Sphero connection
        Requirement 2.1: Establish connection with Sphero Bolt
        """
        try:
            # For now, just mark as started - actual Sphero implementation in later tasks
            self.logger.info("Sphero startup placeholder - will be implemented in Task 3")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start Sphero: {e}")
            return False
    
    def _start_monitoring(self) -> bool:
        """
        Start monitoring systems
        Requirement 5.1: Screen monitoring startup
        """
        try:
            # For now, just mark as started - actual monitoring implementation in later tasks
            self.logger.info("Monitoring startup placeholder - will be implemented in Task 7")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return False
    
    def _create_windows_startup_script(self) -> bool:
        """Create Windows startup script"""
        try:
            # Get current Python executable and script path
            python_exe = sys.executable
            script_path = Path(__file__).parent.parent / "main.py"
            
            # Create startup folder path
            startup_folder = Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            startup_folder.mkdir(parents=True, exist_ok=True)
            
            # Create batch file content
            batch_content = f'''@echo off
cd /d "{script_path.parent}"
"{python_exe}" "{script_path}" --startup
'''
            
            # Write batch file
            batch_file = startup_folder / "SpheroAIAssistant.bat"
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            self.logger.info(f"Created startup script: {batch_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create Windows startup script: {e}")
            return False
    
    def _check_ollama_readiness(self) -> bool:
        """Check if Ollama is ready"""
        return self.ollama_initializer.is_ollama_ready()
    
    def _check_ui_readiness(self) -> bool:
        """Check if UI is ready"""
        # Placeholder - will be implemented with actual UI
        return self.startup_status.get("ui", False)
    
    def _check_sphero_readiness(self) -> bool:
        """Check if Sphero is ready"""
        # Placeholder - will be implemented with actual Sphero integration
        return self.startup_status.get("sphero", False)
    
    def _check_monitoring_readiness(self) -> bool:
        """Check if monitoring is ready"""
        # Placeholder - will be implemented with actual monitoring
        return self.startup_status.get("monitoring", False)
    
    def _calculate_startup_time(self) -> float:
        """Calculate total startup time"""
        # Placeholder - would track actual startup timing
        return 0.0