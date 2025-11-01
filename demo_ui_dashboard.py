"""
Demo script to test UI Dashboard functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sphero_ai_assistant.config import ConfigManager
from sphero_ai_assistant.core import AIAgent
from sphero_ai_assistant.ui.dashboard import UIDashboard
from sphero_ai_assistant.ui.task_manager import TaskManager
from sphero_ai_assistant.ui.status_display import StatusDisplay


async def demo_task_manager():
    """Demo task manager functionality"""
    print("=== Task Manager Demo ===")
    
    # Create mock AI agent
    class MockAIAgent:
        def __init__(self):
            self.is_initialized = True
    
    ai_agent = MockAIAgent()
    task_manager = TaskManager(ai_agent)
    
    # Add some demo tasks
    print("Adding demo tasks...")
    task1 = await task_manager.add_task("Research AI algorithms", "Study machine learning techniques", "high")
    task2 = await task_manager.add_task("Buy groceries", "Go to store and buy milk", "medium")
    task3 = await task_manager.add_task("Write documentation", "Document the API endpoints", "low")
    
    print(f"Added task 1: {task1['title']} (AI can help: {task1['ai_can_help']})")
    print(f"Added task 2: {task2['title']} (AI can help: {task2['ai_can_help']})")
    print(f"Added task 3: {task3['title']} (AI can help: {task3['ai_can_help']})")
    
    # Get all tasks
    tasks = await task_manager.get_daily_tasks()
    print(f"\nTotal tasks: {len(tasks)}")
    
    # Update a task
    updated_task = await task_manager.update_task(task1['id'], {"completed": True})
    print(f"Marked task as completed: {updated_task['title']}")
    
    # Get statistics
    stats = await task_manager.get_task_statistics()
    print(f"Task statistics: {stats}")
    
    print("Task Manager demo completed successfully!\n")


async def demo_status_display():
    """Demo status display functionality"""
    print("=== Status Display Demo ===")
    
    # Create mock config manager
    class MockConfigManager:
        def __init__(self):
            self.is_initialized = True
    
    config_manager = MockConfigManager()
    status_display = StatusDisplay(config_manager)
    
    # Get system status
    print("Getting system status...")
    status = await status_display.get_system_status()
    print(f"Overall status: {status['overall_status']}")
    print("Component status:")
    for component, is_online in status['components'].items():
        print(f"  {component}: {'✓' if is_online else '✗'}")
    
    # Get progress tracking
    print("\nGetting progress tracking...")
    progress_data = await status_display.get_progress_tracking()
    print("Progress items:")
    for item in progress_data:
        print(f"  {item['name']}: {item['current']}/{item['total']} ({item['percentage']:.1f}%)")
    
    print("Status Display demo completed successfully!\n")


async def demo_dashboard_creation():
    """Demo dashboard creation"""
    print("=== Dashboard Creation Demo ===")
    
    # Create mock dependencies
    class MockConfigManager:
        def __init__(self):
            self.is_initialized = True
    
    class MockAIAgent:
        def __init__(self):
            self.is_initialized = True
    
    config_manager = MockConfigManager()
    ai_agent = MockAIAgent()
    
    # Create dashboard
    print("Creating UI Dashboard...")
    dashboard = UIDashboard(config_manager, ai_agent)
    
    print(f"Dashboard created successfully!")
    print(f"FastAPI app: {dashboard.app}")
    print(f"Task manager: {dashboard.task_manager}")
    print(f"Status display: {dashboard.status_display}")
    
    # Check routes
    routes = [route.path for route in dashboard.app.routes if hasattr(route, 'path')]
    print(f"Available routes: {routes}")
    
    print("Dashboard creation demo completed successfully!\n")


async def main():
    """Run all demos"""
    print("Starting UI Dashboard Demo...\n")
    
    try:
        await demo_task_manager()
        await demo_status_display()
        await demo_dashboard_creation()
        
        print("🎉 All UI Dashboard demos completed successfully!")
        print("\nTo start the actual dashboard, run:")
        print("python -m sphero_ai_assistant.main")
        print("Then visit: http://127.0.0.1:8000")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))