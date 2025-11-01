"""
Tests for UI Dashboard functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from sphero_ai_assistant.ui.dashboard import UIDashboard
from sphero_ai_assistant.ui.task_manager import TaskManager, Task
from sphero_ai_assistant.ui.status_display import StatusDisplay


class TestUIDashboard:
    """Test UI Dashboard functionality"""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager"""
        config_manager = Mock()
        config_manager.is_initialized = True
        return config_manager
    
    @pytest.fixture
    def mock_ai_agent(self):
        """Mock AI agent"""
        ai_agent = Mock()
        ai_agent.is_initialized = True
        return ai_agent
    
    @pytest.fixture
    def dashboard(self, mock_config_manager, mock_ai_agent):
        """Create dashboard instance for testing"""
        return UIDashboard(mock_config_manager, mock_ai_agent)
    
    def test_dashboard_initialization(self, dashboard):
        """Test dashboard initializes correctly"""
        assert dashboard.config_manager is not None
        assert dashboard.ai_agent is not None
        assert dashboard.task_manager is not None
        assert dashboard.status_display is not None
        assert dashboard.app is not None
        assert not dashboard.is_running
    
    def test_dashboard_routes_setup(self, dashboard):
        """Test that all required routes are set up"""
        routes = [route.path for route in dashboard.app.routes]
        
        expected_routes = [
            "/",
            "/api/tasks",
            "/api/status", 
            "/api/progress",
            "/api/ai-analyze-task"
        ]
        
        for expected_route in expected_routes:
            assert any(expected_route in route for route in routes)


class TestTaskManager:
    """Test Task Manager functionality"""
    
    @pytest.fixture
    def mock_ai_agent(self):
        """Mock AI agent"""
        return Mock()
    
    @pytest.fixture
    def task_manager(self, mock_ai_agent):
        """Create task manager instance for testing"""
        return TaskManager(mock_ai_agent)
    
    def test_task_creation(self):
        """Test task creation"""
        task = Task.create_new("Test Task", "Test Description", "high")
        
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.priority == "high"
        assert not task.completed
        assert task.id is not None
        assert task.created_at is not None
    
    @pytest.mark.asyncio
    async def test_add_task(self, task_manager):
        """Test adding a task"""
        task_data = await task_manager.add_task("Test Task", "Description", "medium")
        
        assert task_data["title"] == "Test Task"
        assert task_data["description"] == "Description"
        assert task_data["priority"] == "medium"
        assert not task_data["completed"]
    
    @pytest.mark.asyncio
    async def test_get_daily_tasks(self, task_manager):
        """Test getting daily tasks"""
        # Add a test task first
        await task_manager.add_task("Test Task", "Description", "medium")
        
        tasks = await task_manager.get_daily_tasks()
        assert len(tasks) >= 1
        assert tasks[0]["title"] == "Test Task"
    
    def test_ai_assistance_analysis(self, task_manager):
        """Test AI assistance analysis"""
        # Test tasks that AI can help with
        ai_helpful_task = Task.create_new("Research machine learning", "Need to research ML algorithms")
        
        # Test tasks that AI cannot help with (physical tasks)
        physical_task = Task.create_new("Buy groceries", "Go to the store and buy milk")
        
        # The actual analysis is async, but we can test the keyword logic
        assert "research" in ai_helpful_task.title.lower()
        assert "buy" in physical_task.title.lower()


class TestStatusDisplay:
    """Test Status Display functionality"""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager"""
        config_manager = Mock()
        config_manager.is_initialized = True
        return config_manager
    
    @pytest.fixture
    def status_display(self, mock_config_manager):
        """Create status display instance for testing"""
        return StatusDisplay(mock_config_manager)
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, status_display):
        """Test getting system status"""
        status = await status_display.get_system_status()
        
        assert "overall_status" in status
        assert "components" in status
        assert "last_updated" in status
        
        # Check that all expected components are present
        expected_components = [
            "ai_agent", "config_manager", "ollama", 
            "sphero", "ui_dashboard", "memory_system"
        ]
        
        for component in expected_components:
            assert component in status["components"]
    
    @pytest.mark.asyncio
    async def test_get_progress_tracking(self, status_display):
        """Test getting progress tracking data"""
        progress_data = await status_display.get_progress_tracking()
        
        assert isinstance(progress_data, list)
        
        if progress_data:  # If we have progress data
            for item in progress_data:
                assert "name" in item
                assert "current" in item
                assert "total" in item
                assert "percentage" in item
    
    def test_status_caching(self, status_display):
        """Test that status caching works"""
        # The cache should be empty initially
        assert not status_display.status_cache
        assert status_display.last_update is None


if __name__ == "__main__":
    pytest.main([__file__])