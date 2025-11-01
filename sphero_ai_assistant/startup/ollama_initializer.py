"""
Ollama Initializer - Handles Ollama AI system initialization
"""

import subprocess
import time
import logging
import requests
from typing import Optional, Dict, Any


class OllamaInitializer:
    """
    Handles initialization and management of Ollama AI system
    Requirement 1.1: Initialize Ollama AI system on startup
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ollama_process: Optional[subprocess.Popen] = None
        self.ollama_url = "http://localhost:11434"
        self.is_ready = False
        
    def initialize_ollama(self) -> bool:
        """
        Initialize Ollama AI system
        Requirement 1.1: Initialize all components including Ollama AI
        """
        try:
            self.logger.info("Initializing Ollama AI system...")
            
            # Check if Ollama is already running
            if self._check_ollama_running():
                self.logger.info("Ollama is already running")
                self.is_ready = True
                return True
            
            # Try to start Ollama service
            if self._start_ollama_service():
                # Wait for Ollama to be ready
                if self._wait_for_ollama_ready():
                    self.logger.info("Ollama initialized successfully")
                    self.is_ready = True
                    return True
                else:
                    self.logger.error("Ollama failed to become ready within timeout")
                    return False
            else:
                self.logger.error("Failed to start Ollama service")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama: {e}")
            return False
    
    def is_ollama_ready(self) -> bool:
        """
        Check if Ollama is ready for use
        Requirement 1.3: System ready for immediate use
        """
        if not self.is_ready:
            self.is_ready = self._check_ollama_running()
        return self.is_ready
    
    def get_ollama_status(self) -> Dict[str, Any]:
        """Get detailed Ollama status information"""
        status = {
            "running": False,
            "ready": False,
            "url": self.ollama_url,
            "models": [],
            "version": None
        }
        
        try:
            if self._check_ollama_running():
                status["running"] = True
                status["ready"] = True
                
                # Get version info
                version_info = self._get_ollama_version()
                if version_info:
                    status["version"] = version_info
                
                # Get available models
                models = self._get_available_models()
                if models:
                    status["models"] = models
                    
        except Exception as e:
            self.logger.error(f"Error getting Ollama status: {e}")
        
        return status
    
    def ensure_model_available(self, model_name: str = "llama2") -> bool:
        """
        Ensure a specific model is available in Ollama
        Requirement 1.1: Ollama ready for AI operations
        """
        try:
            if not self.is_ollama_ready():
                self.logger.error("Ollama not ready")
                return False
            
            # Check if model is already available
            available_models = self._get_available_models()
            if model_name in available_models:
                self.logger.info(f"Model {model_name} is already available")
                return True
            
            # Pull the model
            self.logger.info(f"Pulling model {model_name}...")
            if self._pull_model(model_name):
                self.logger.info(f"Model {model_name} pulled successfully")
                return True
            else:
                self.logger.error(f"Failed to pull model {model_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error ensuring model availability: {e}")
            return False
    
    def shutdown_ollama(self) -> bool:
        """Shutdown Ollama service gracefully"""
        try:
            if self.ollama_process:
                self.logger.info("Shutting down Ollama process...")
                self.ollama_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.ollama_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Ollama didn't shutdown gracefully, forcing...")
                    self.ollama_process.kill()
                
                self.ollama_process = None
            
            self.is_ready = False
            self.logger.info("Ollama shutdown complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Error shutting down Ollama: {e}")
            return False
    
    def _check_ollama_running(self) -> bool:
        """Check if Ollama service is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def _start_ollama_service(self) -> bool:
        """Start Ollama service"""
        try:
            # Try to start Ollama using the ollama command
            self.logger.info("Starting Ollama service...")
            
            # First try: ollama serve (if ollama is in PATH)
            try:
                self.ollama_process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                
                # Give it a moment to start
                time.sleep(2)
                
                # Check if process is still running
                if self.ollama_process.poll() is None:
                    self.logger.info("Ollama service started successfully")
                    return True
                else:
                    self.logger.warning("Ollama process exited immediately")
                    return False
                    
            except FileNotFoundError:
                self.logger.warning("Ollama command not found in PATH")
                
                # Try alternative: check if Ollama is installed as a service
                try:
                    # On Windows, try to start the Ollama service
                    result = subprocess.run(
                        ["sc", "start", "Ollama"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        self.logger.info("Ollama Windows service started")
                        return True
                    else:
                        self.logger.warning(f"Failed to start Ollama service: {result.stderr}")
                        
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    self.logger.warning("Could not start Ollama as Windows service")
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting Ollama service: {e}")
            return False
    
    def _wait_for_ollama_ready(self, timeout: int = 30) -> bool:
        """Wait for Ollama to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self._check_ollama_running():
                return True
            
            time.sleep(1)
            self.logger.debug("Waiting for Ollama to be ready...")
        
        return False
    
    def _get_ollama_version(self) -> Optional[str]:
        """Get Ollama version information"""
        try:
            response = requests.get(f"{self.ollama_url}/api/version", timeout=5)
            if response.status_code == 200:
                return response.json().get("version")
        except requests.RequestException:
            pass
        return None
    
    def _get_available_models(self) -> list:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except requests.RequestException:
            pass
        return []
    
    def _pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry"""
        try:
            # Use ollama pull command
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout for model download
            )
            
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Error pulling model {model_name}: {e}")
            return False