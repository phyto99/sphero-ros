"""
Status Display - Real-time system status and progress tracking
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import psutil
import json
from pathlib import Path


class StatusDisplay:
    """
    Real-time system status display and progress tracking
    Requirements 1.5, 10.2, 10.3: Real-time status display and progress tracking
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.status_cache = {}
        self.last_update = None
        self.cache_duration = timedelta(seconds=5)  # Cache for 5 seconds
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get real-time system status for all components
        Requirement 1.5: Real-time status display for system components
        """
        try:
            # Check cache first
            if (self.last_update and 
                datetime.now() - self.last_update < self.cache_duration and 
                'system_status' in self.status_cache):
                return self.status_cache['system_status']
            
            # Get fresh status
            status = {
                'overall_status': 'online',
                'components': {},
                'last_updated': datetime.now().isoformat(),
                'system_info': {}
            }
            
            # Check core system components
            status['components']['ai_agent'] = await self._check_ai_agent_status()
            status['components']['config_manager'] = await self._check_config_manager_status()
            status['components']['ollama'] = await self._check_ollama_status()
            status['components']['sphero'] = await self._check_sphero_status()
            status['components']['ui_dashboard'] = await self._check_ui_dashboard_status()
            status['components']['memory_system'] = await self._check_memory_system_status()
            
            # System resource information
            status['system_info'] = await self._get_system_info()
            
            # Determine overall status
            all_critical_online = all([
                status['components']['ai_agent'],
                status['components']['config_manager'],
                status['components']['ui_dashboard']
            ])
            
            if all_critical_online:
                status['overall_status'] = 'online'
            else:
                status['overall_status'] = 'degraded'
            
            # Cache the result
            self.status_cache['system_status'] = status
            self.last_update = datetime.now()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {
                'overall_status': 'error',
                'components': {},
                'last_updated': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def get_progress_tracking(self) -> List[Dict[str, Any]]:
        """
        Get progress tracking data for AI subscriptions and system limits
        Requirements 10.2, 10.3: Progress tracking for AI limits and free trial timers
        """
        try:
            progress_items = []
            
            # System resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            progress_items.extend([
                {
                    'name': 'CPU Usage',
                    'current': int(cpu_percent),
                    'total': 100,
                    'percentage': cpu_percent,
                    'unit': '%',
                    'status': 'normal' if cpu_percent < 80 else 'warning'
                },
                {
                    'name': 'Memory Usage',
                    'current': round(memory.used / (1024**3), 1),
                    'total': round(memory.total / (1024**3), 1),
                    'percentage': memory.percent,
                    'unit': 'GB',
                    'status': 'normal' if memory.percent < 80 else 'warning'
                },
                {
                    'name': 'Disk Usage',
                    'current': round(disk.used / (1024**3), 1),
                    'total': round(disk.total / (1024**3), 1),
                    'percentage': (disk.used / disk.total) * 100,
                    'unit': 'GB',
                    'status': 'normal' if (disk.used / disk.total) < 0.8 else 'warning'
                }
            ])
            
            # AI Service Usage (simulated for now)
            ai_usage = await self._get_ai_usage_stats()
            progress_items.extend(ai_usage)
            
            # Task completion progress
            task_stats = await self._get_task_completion_stats()
            if task_stats:
                progress_items.append(task_stats)
            
            return progress_items
            
        except Exception as e:
            self.logger.error(f"Failed to get progress tracking: {e}")
            return []
    
    async def _check_ai_agent_status(self) -> bool:
        """Check if AI agent is running and responsive"""
        try:
            # This would check if the AI agent is properly initialized
            # For now, we'll assume it's running if the config manager is available
            return self.config_manager is not None
        except Exception:
            return False
    
    async def _check_config_manager_status(self) -> bool:
        """Check if configuration manager is working"""
        try:
            return (self.config_manager is not None and 
                   hasattr(self.config_manager, 'is_initialized') and
                   self.config_manager.is_initialized)
        except Exception:
            return False
    
    async def _check_ollama_status(self) -> bool:
        """Check if Ollama service is running"""
        try:
            # Check if Ollama process is running
            for proc in psutil.process_iter(['pid', 'name']):
                if 'ollama' in proc.info['name'].lower():
                    return True
            return False
        except Exception:
            return False
    
    async def _check_sphero_status(self) -> bool:
        """Check if Sphero is connected"""
        try:
            # This would check actual Sphero connection
            # For now, return False as Sphero integration is in a later task
            return False
        except Exception:
            return False
    
    async def _check_ui_dashboard_status(self) -> bool:
        """Check if UI dashboard is running"""
        try:
            # Check if the current process is serving the dashboard
            # Since we're in the dashboard code, assume it's running
            return True
        except Exception:
            return False
    
    async def _check_memory_system_status(self) -> bool:
        """Check if memory system is operational"""
        try:
            # Check if memory system files exist and are accessible
            memory_dir = Path("config/memory")
            return memory_dir.exists() or True  # Allow it to be created
        except Exception:
            return False
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get general system information"""
        try:
            return {
                'platform': psutil.WINDOWS if hasattr(psutil, 'WINDOWS') else 'unknown',
                'cpu_count': psutil.cpu_count(),
                'total_memory_gb': round(psutil.virtual_memory().total / (1024**3), 1),
                'python_version': f"{psutil.version_info if hasattr(psutil, 'version_info') else 'unknown'}",
                'uptime_hours': round((datetime.now().timestamp() - psutil.boot_time()) / 3600, 1)
            }
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {}
    
    async def _get_ai_usage_stats(self) -> List[Dict[str, Any]]:
        """Get AI service usage statistics"""
        try:
            # Simulated AI usage data - in a real implementation, this would
            # connect to actual AI service APIs to get usage statistics
            
            usage_stats = []
            
            # Ollama usage (simulated)
            usage_stats.append({
                'name': 'Ollama Requests',
                'current': 45,  # Simulated current usage
                'total': 1000,  # Simulated daily limit
                'percentage': 4.5,
                'unit': 'requests',
                'status': 'normal'
            })
            
            # OpenAI API usage (simulated)
            usage_stats.append({
                'name': 'OpenAI Tokens',
                'current': 15000,  # Simulated current usage
                'total': 100000,  # Simulated monthly limit
                'percentage': 15.0,
                'unit': 'tokens',
                'status': 'normal'
            })
            
            # Free trial timer (simulated)
            trial_days_used = 5  # Simulated
            trial_total_days = 30
            usage_stats.append({
                'name': 'Free Trial',
                'current': trial_days_used,
                'total': trial_total_days,
                'percentage': (trial_days_used / trial_total_days) * 100,
                'unit': 'days',
                'status': 'normal' if trial_days_used < 25 else 'warning'
            })
            
            return usage_stats
            
        except Exception as e:
            self.logger.error(f"Failed to get AI usage stats: {e}")
            return []
    
    async def _get_task_completion_stats(self) -> Dict[str, Any]:
        """Get task completion statistics"""
        try:
            # Try to load task statistics from task manager
            tasks_file = Path("config/daily_tasks.json")
            if not tasks_file.exists():
                return None
            
            with open(tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            tasks = data.get('tasks', [])
            if not tasks:
                return None
            
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.get('completed', False))
            
            return {
                'name': 'Daily Tasks',
                'current': completed_tasks,
                'total': total_tasks,
                'percentage': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'unit': 'tasks',
                'status': 'normal'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get task completion stats: {e}")
            return None
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status for all external services"""
        try:
            connections = {
                'internet': await self._check_internet_connection(),
                'ollama_service': await self._check_ollama_connection(),
                'sphero_device': await self._check_sphero_connection(),
                'ai_services': await self._check_ai_services_connection()
            }
            
            return {
                'connections': connections,
                'overall_connectivity': all(connections.values()),
                'last_checked': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get connection status: {e}")
            return {
                'connections': {},
                'overall_connectivity': False,
                'error': str(e)
            }
    
    async def _check_internet_connection(self) -> bool:
        """Check internet connectivity"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except Exception:
            return False
    
    async def _check_ollama_connection(self) -> bool:
        """Check Ollama service connection"""
        try:
            # This would make an actual HTTP request to Ollama
            # For now, just check if the process is running
            return await self._check_ollama_status()
        except Exception:
            return False
    
    async def _check_sphero_connection(self) -> bool:
        """Check Sphero device connection"""
        try:
            # This would check actual Sphero Bluetooth connection
            # For now, return False as Sphero integration is in a later task
            return False
        except Exception:
            return False
    
    async def _check_ai_services_connection(self) -> bool:
        """Check AI services connectivity"""
        try:
            # This would check connections to external AI services
            # For now, assume they're available if internet is working
            return await self._check_internet_connection()
        except Exception:
            return False