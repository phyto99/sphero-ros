"""
Configuration Manager - Handles user preferences and system settings
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class SystemConfig:
    """System configuration settings"""
    auto_startup: bool = True
    ollama_auto_init: bool = True
    ui_theme: str = "modern"
    log_level: str = "INFO"
    sphero_auto_connect: bool = True
    monitoring_enabled: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """Create system config from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class UIConfig:
    """UI configuration settings"""
    theme: str = "modern"
    auto_startup_ui: bool = True
    show_status_display: bool = True
    task_management_enabled: bool = True
    ai_assistance_highlighting: bool = True
    progress_tracking_visible: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIConfig':
        """Create UI config from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class SpheroConfig:
    """Sphero-specific configuration"""
    auto_connect: bool = True
    battery_monitoring: bool = True
    led_brightness: float = 0.8
    connection_timeout: int = 30
    autonomous_mode: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpheroConfig':
        """Create Sphero config from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class ConfigManager:
    """
    Configuration management system for user preferences and system settings
    Requirement 1.3: Basic configuration management system for user preferences and system settings
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.system_config_file = self.config_dir / "system.json"
        self.user_preferences_file = self.config_dir / "user_preferences.json"
        self.ui_config_file = self.config_dir / "ui.json"
        self.sphero_config_file = self.config_dir / "sphero.json"
        
        self.system_config = SystemConfig()
        self.ui_config = UIConfig()
        self.sphero_config = SpheroConfig()
        self.user_preferences = {}
        
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize configuration manager and load all configs
        Requirement 1.3: Configuration management system initialization
        """
        try:
            self.logger.info("Initializing Configuration Manager...")
            
            # Load all configuration files
            self._load_system_config()
            self._load_ui_config()
            self._load_sphero_config()
            self._load_user_preferences()
            
            # Create default configs if they don't exist
            self._ensure_default_configs()
            
            self.is_initialized = True
            self.logger.info("Configuration Manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Configuration Manager: {e}")
            return False
    
    def get_system_config(self) -> SystemConfig:
        """
        Get system configuration
        Requirement 1.1: Auto-startup configuration
        """
        return self.system_config
    
    def get_ui_config(self) -> UIConfig:
        """
        Get UI configuration
        Requirement 1.2: Perfect UI configuration
        """
        return self.ui_config
    
    def get_sphero_config(self) -> SpheroConfig:
        """Get Sphero configuration"""
        return self.sphero_config
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """
        Get user preferences
        Requirement 1.3: User preferences management
        """
        return self.user_preferences.copy()
    
    def update_system_config(self, **kwargs) -> bool:
        """
        Update system configuration
        Requirement 1.1: Auto-startup service configuration
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.system_config, key):
                    setattr(self.system_config, key, value)
                    self.logger.info(f"Updated system config: {key} = {value}")
            
            self._save_system_config()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update system config: {e}")
            return False
    
    def update_ui_config(self, **kwargs) -> bool:
        """
        Update UI configuration
        Requirement 1.2: Perfect UI configuration management
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.ui_config, key):
                    setattr(self.ui_config, key, value)
                    self.logger.info(f"Updated UI config: {key} = {value}")
            
            self._save_ui_config()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update UI config: {e}")
            return False
    
    def update_sphero_config(self, **kwargs) -> bool:
        """Update Sphero configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.sphero_config, key):
                    setattr(self.sphero_config, key, value)
                    self.logger.info(f"Updated Sphero config: {key} = {value}")
            
            self._save_sphero_config()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update Sphero config: {e}")
            return False
    
    def update_user_preference(self, key: str, value: Any) -> bool:
        """
        Update user preference
        Requirement 1.3: User preferences management
        """
        try:
            self.user_preferences[key] = value
            self._save_user_preferences()
            self.logger.info(f"Updated user preference: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update user preference: {e}")
            return False
    
    def get_startup_config(self) -> Dict[str, Any]:
        """
        Get configuration needed for system startup
        Requirement 1.1: Auto-startup service configuration
        """
        return {
            "auto_startup": self.system_config.auto_startup,
            "ollama_auto_init": self.system_config.ollama_auto_init,
            "sphero_auto_connect": self.sphero_config.auto_connect,
            "ui_auto_startup": self.ui_config.auto_startup_ui,
            "monitoring_enabled": self.system_config.monitoring_enabled
        }
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate all configuration settings"""
        validation_results = {
            "system_config": self._validate_system_config(),
            "ui_config": self._validate_ui_config(),
            "sphero_config": self._validate_sphero_config(),
            "user_preferences": self._validate_user_preferences()
        }
        
        all_valid = all(validation_results.values())
        self.logger.info(f"Configuration validation: {'PASSED' if all_valid else 'FAILED'}")
        
        return validation_results
    
    def reset_to_defaults(self, config_type: Optional[str] = None) -> bool:
        """Reset configuration to defaults"""
        try:
            if config_type is None or config_type == "system":
                self.system_config = SystemConfig()
                self._save_system_config()
            
            if config_type is None or config_type == "ui":
                self.ui_config = UIConfig()
                self._save_ui_config()
            
            if config_type is None or config_type == "sphero":
                self.sphero_config = SpheroConfig()
                self._save_sphero_config()
            
            if config_type is None or config_type == "user":
                self.user_preferences = {}
                self._save_user_preferences()
            
            self.logger.info(f"Reset {config_type or 'all'} configuration to defaults")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return False
    
    def _load_system_config(self):
        """Load system configuration from file"""
        if self.system_config_file.exists():
            try:
                with open(self.system_config_file, 'r') as f:
                    data = json.load(f)
                self.system_config = SystemConfig.from_dict(data)
                self.logger.info("Loaded system configuration")
            except Exception as e:
                self.logger.warning(f"Failed to load system config, using defaults: {e}")
    
    def _load_ui_config(self):
        """Load UI configuration from file"""
        if self.ui_config_file.exists():
            try:
                with open(self.ui_config_file, 'r') as f:
                    data = json.load(f)
                self.ui_config = UIConfig.from_dict(data)
                self.logger.info("Loaded UI configuration")
            except Exception as e:
                self.logger.warning(f"Failed to load UI config, using defaults: {e}")
    
    def _load_sphero_config(self):
        """Load Sphero configuration from file"""
        if self.sphero_config_file.exists():
            try:
                with open(self.sphero_config_file, 'r') as f:
                    data = json.load(f)
                self.sphero_config = SpheroConfig.from_dict(data)
                self.logger.info("Loaded Sphero configuration")
            except Exception as e:
                self.logger.warning(f"Failed to load Sphero config, using defaults: {e}")
    
    def _load_user_preferences(self):
        """Load user preferences from file"""
        if self.user_preferences_file.exists():
            try:
                with open(self.user_preferences_file, 'r') as f:
                    self.user_preferences = json.load(f)
                self.logger.info("Loaded user preferences")
            except Exception as e:
                self.logger.warning(f"Failed to load user preferences, using defaults: {e}")
    
    def _save_system_config(self):
        """Save system configuration to file"""
        try:
            with open(self.system_config_file, 'w') as f:
                json.dump(asdict(self.system_config), f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save system config: {e}")
    
    def _save_ui_config(self):
        """Save UI configuration to file"""
        try:
            with open(self.ui_config_file, 'w') as f:
                json.dump(asdict(self.ui_config), f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save UI config: {e}")
    
    def _save_sphero_config(self):
        """Save Sphero configuration to file"""
        try:
            with open(self.sphero_config_file, 'w') as f:
                json.dump(asdict(self.sphero_config), f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save Sphero config: {e}")
    
    def _save_user_preferences(self):
        """Save user preferences to file"""
        try:
            with open(self.user_preferences_file, 'w') as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save user preferences: {e}")
    
    def _ensure_default_configs(self):
        """Ensure all default configuration files exist"""
        if not self.system_config_file.exists():
            self._save_system_config()
        if not self.ui_config_file.exists():
            self._save_ui_config()
        if not self.sphero_config_file.exists():
            self._save_sphero_config()
        if not self.user_preferences_file.exists():
            self._save_user_preferences()
    
    def _validate_system_config(self) -> bool:
        """Validate system configuration"""
        try:
            # Check required fields exist and have valid types
            assert isinstance(self.system_config.auto_startup, bool)
            assert isinstance(self.system_config.ollama_auto_init, bool)
            assert self.system_config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
            return True
        except (AssertionError, AttributeError):
            return False
    
    def _validate_ui_config(self) -> bool:
        """Validate UI configuration"""
        try:
            assert isinstance(self.ui_config.auto_startup_ui, bool)
            assert isinstance(self.ui_config.show_status_display, bool)
            assert isinstance(self.ui_config.task_management_enabled, bool)
            return True
        except (AssertionError, AttributeError):
            return False
    
    def _validate_sphero_config(self) -> bool:
        """Validate Sphero configuration"""
        try:
            assert isinstance(self.sphero_config.auto_connect, bool)
            assert 0.0 <= self.sphero_config.led_brightness <= 1.0
            assert self.sphero_config.connection_timeout > 0
            return True
        except (AssertionError, AttributeError):
            return False
    
    def _validate_user_preferences(self) -> bool:
        """Validate user preferences"""
        try:
            # User preferences can be any valid JSON, so just check it's a dict
            assert isinstance(self.user_preferences, dict)
            return True
        except AssertionError:
            return False