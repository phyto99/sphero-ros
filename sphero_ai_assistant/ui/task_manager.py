"""
Task Manager - Daily task management interface with AI assistance highlighting
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass
class Task:
    """Task data model"""
    id: str
    title: str
    description: str
    priority: str  # low, medium, high
    completed: bool
    created_at: str
    updated_at: str
    ai_can_help: bool = False
    
    @classmethod
    def create_new(cls, title: str, description: str = "", priority: str = "medium") -> 'Task':
        """Create a new task"""
        now = datetime.now().isoformat()
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            priority=priority,
            completed=False,
            created_at=now,
            updated_at=now,
            ai_can_help=False
        )


class TaskManager:
    """
    Daily task management with AI assistance highlighting
    Requirements 1.4, 1.5: Task management interface with AI assistance
    """
    
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        self.logger = logging.getLogger(__name__)
        self.tasks_file = Path("config/daily_tasks.json")
        self.tasks_file.parent.mkdir(exist_ok=True)
        self._tasks: Dict[str, Task] = {}
        self._load_tasks()
    
    async def get_daily_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all daily tasks with AI assistance analysis
        Requirement 1.4: Daily task management interface
        """
        try:
            # Refresh AI assistance analysis for all tasks
            for task in self._tasks.values():
                if not task.completed:
                    task.ai_can_help = await self._analyze_ai_assistance(task)
            
            # Sort tasks by priority and completion status
            sorted_tasks = sorted(
                self._tasks.values(),
                key=lambda t: (t.completed, self._priority_order(t.priority), t.created_at)
            )
            
            return [asdict(task) for task in sorted_tasks]
            
        except Exception as e:
            self.logger.error(f"Failed to get daily tasks: {e}")
            return []
    
    async def add_task(self, title: str, description: str = "", priority: str = "medium") -> Dict[str, Any]:
        """
        Add a new task with AI assistance analysis
        Requirement 1.4: Add/edit functionality
        """
        try:
            task = Task.create_new(title, description, priority)
            
            # Analyze if AI can help with this task
            task.ai_can_help = await self._analyze_ai_assistance(task)
            
            self._tasks[task.id] = task
            await self._save_tasks()
            
            self.logger.info(f"Added new task: {title}")
            return asdict(task)
            
        except Exception as e:
            self.logger.error(f"Failed to add task: {e}")
            raise
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing task
        Requirement 1.4: Add/edit functionality
        """
        try:
            if task_id not in self._tasks:
                raise ValueError(f"Task {task_id} not found")
            
            task = self._tasks[task_id]
            
            # Update fields
            if "title" in updates:
                task.title = updates["title"]
            if "description" in updates:
                task.description = updates["description"]
            if "priority" in updates:
                task.priority = updates["priority"]
            if "completed" in updates:
                task.completed = updates["completed"]
            
            task.updated_at = datetime.now().isoformat()
            
            # Re-analyze AI assistance if task content changed
            if any(key in updates for key in ["title", "description"]):
                task.ai_can_help = await self._analyze_ai_assistance(task)
            
            await self._save_tasks()
            
            self.logger.info(f"Updated task: {task_id}")
            return asdict(task)
            
        except Exception as e:
            self.logger.error(f"Failed to update task: {e}")
            raise
    
    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task
        Requirement 1.4: Task management functionality
        """
        try:
            if task_id not in self._tasks:
                return False
            
            del self._tasks[task_id]
            await self._save_tasks()
            
            self.logger.info(f"Deleted task: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete task: {e}")
            return False
    
    async def analyze_task_for_ai_help(self, task_id: str) -> bool:
        """
        Analyze if AI can help with a specific task
        Requirement 1.5: AI assistance highlighting
        """
        try:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            can_help = await self._analyze_ai_assistance(task)
            
            # Update the task with the analysis result
            task.ai_can_help = can_help
            await self._save_tasks()
            
            return can_help
            
        except Exception as e:
            self.logger.error(f"Failed to analyze task for AI help: {e}")
            return False
    
    async def _analyze_ai_assistance(self, task: Task) -> bool:
        """
        Analyze if AI can help with a task using the AI agent
        Requirement 1.5: AI assistance highlighting
        """
        try:
            # Keywords that indicate AI can help
            ai_helpful_keywords = [
                "research", "analyze", "write", "draft", "plan", "organize",
                "calculate", "summarize", "review", "brainstorm", "design",
                "code", "program", "script", "automate", "optimize",
                "translate", "explain", "learn", "study", "compare"
            ]
            
            # Keywords that indicate AI cannot help (physical tasks)
            physical_keywords = [
                "buy", "purchase", "shop", "drive", "walk", "run", "exercise",
                "clean", "cook", "eat", "sleep", "meet", "call", "visit",
                "repair", "fix", "build", "install", "move", "travel"
            ]
            
            task_text = f"{task.title} {task.description}".lower()
            
            # Check for physical task keywords first
            if any(keyword in task_text for keyword in physical_keywords):
                return False
            
            # Check for AI-helpful keywords
            if any(keyword in task_text for keyword in ai_helpful_keywords):
                return True
            
            # Use AI agent for more sophisticated analysis if available
            if self.ai_agent and hasattr(self.ai_agent, 'analyze_task_assistance'):
                try:
                    analysis_result = await self.ai_agent.analyze_task_assistance(task_text)
                    return analysis_result.get('can_help', False)
                except Exception as e:
                    self.logger.warning(f"AI agent analysis failed, using keyword fallback: {e}")
            
            # Default to False for unknown tasks
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to analyze AI assistance: {e}")
            return False
    
    def _priority_order(self, priority: str) -> int:
        """Get numeric order for priority sorting"""
        priority_map = {"high": 0, "medium": 1, "low": 2}
        return priority_map.get(priority, 1)
    
    def _load_tasks(self):
        """Load tasks from file"""
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._tasks = {}
                for task_data in data.get('tasks', []):
                    task = Task(**task_data)
                    self._tasks[task.id] = task
                
                self.logger.info(f"Loaded {len(self._tasks)} tasks")
            else:
                self._tasks = {}
                self.logger.info("No existing tasks file found, starting with empty task list")
                
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}")
            self._tasks = {}
    
    async def _save_tasks(self):
        """Save tasks to file"""
        try:
            data = {
                'tasks': [asdict(task) for task in self._tasks.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")
            raise
    
    async def get_task_statistics(self) -> Dict[str, Any]:
        """Get task completion statistics"""
        try:
            total_tasks = len(self._tasks)
            completed_tasks = sum(1 for task in self._tasks.values() if task.completed)
            ai_assistable_tasks = sum(1 for task in self._tasks.values() if task.ai_can_help and not task.completed)
            
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': total_tasks - completed_tasks,
                'ai_assistable_tasks': ai_assistable_tasks,
                'completion_rate': round(completion_rate, 1)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get task statistics: {e}")
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'pending_tasks': 0,
                'ai_assistable_tasks': 0,
                'completion_rate': 0.0
            }