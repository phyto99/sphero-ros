"""
Main entry point for Sphero AI Assistant
"""

import sys
import logging
import argparse
import asyncio
from pathlib import Path

from .config import ConfigManager
from .startup import AutoStartupService
from .core import AIAgent
from .ui.dashboard import UIDashboard


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('sphero_ai_assistant.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main():
    """
    Main entry point for Sphero AI Assistant
    Requirement 1.1: System auto-launch and initialization
    """
    parser = argparse.ArgumentParser(description="Sphero AI Assistant")
    parser.add_argument("--startup", action="store_true", help="Run in startup mode")
    parser.add_argument("--install-startup", action="store_true", help="Install startup service")
    parser.add_argument("--uninstall-startup", action="store_true", help="Uninstall startup service")
    parser.add_argument("--config-dir", default="config", help="Configuration directory")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Sphero AI Assistant...")
        
        # Initialize configuration manager
        config_manager = ConfigManager(args.config_dir)
        if not config_manager.initialize():
            logger.error("Failed to initialize configuration manager")
            return 1
        
        # Handle startup service installation/uninstallation
        if args.install_startup:
            startup_service = AutoStartupService(config_manager)
            if startup_service.install_startup_service():
                logger.info("Startup service installed successfully")
                return 0
            else:
                logger.error("Failed to install startup service")
                return 1
        
        if args.uninstall_startup:
            startup_service = AutoStartupService(config_manager)
            if startup_service.uninstall_startup_service():
                logger.info("Startup service uninstalled successfully")
                return 0
            else:
                logger.error("Failed to uninstall startup service")
                return 1
        
        # Initialize auto-startup service
        startup_service = AutoStartupService(config_manager)
        if not startup_service.initialize():
            logger.error("Failed to initialize startup service")
            return 1
        
        # Start all system components
        startup_status = startup_service.start_system()
        
        # Check system readiness
        readiness = startup_service.check_system_readiness()
        
        if readiness["ready"]:
            logger.info("System is ready for use!")
            
            # Initialize AI Agent
            ai_agent = AIAgent(config_manager)
            if await ai_agent.initialize():
                logger.info("AI Agent initialized successfully")
                
                # Initialize and start UI Dashboard
                ui_config = config_manager.get_ui_config()
                if ui_config.auto_startup_ui:
                    try:
                        dashboard = UIDashboard(config_manager, ai_agent)
                        await dashboard.start_dashboard()
                        logger.info("UI Dashboard started successfully")
                        
                        # Keep the system running
                        if args.startup:
                            logger.info("Running in startup mode - system will continue running")
                            # Keep the event loop running
                            try:
                                while True:
                                    await asyncio.sleep(1)
                            except KeyboardInterrupt:
                                logger.info("Shutdown requested")
                                await dashboard.stop_dashboard()
                                return 0
                        else:
                            logger.info("System initialized successfully - Dashboard running at http://127.0.0.1:8000")
                            # Keep the server running
                            try:
                                while True:
                                    await asyncio.sleep(1)
                            except KeyboardInterrupt:
                                logger.info("Shutdown requested")
                                await dashboard.stop_dashboard()
                                return 0
                    except Exception as e:
                        logger.error(f"Failed to start UI Dashboard: {e}")
                        return 1
                else:
                    logger.info("UI Dashboard auto-startup disabled")
                    return 0
            else:
                logger.error("Failed to initialize AI Agent")
                return 1
        else:
            logger.warning("System not fully ready")
            failed_components = [
                comp for comp, status in readiness["components"].items() 
                if not status
            ]
            logger.warning(f"Failed components: {failed_components}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))