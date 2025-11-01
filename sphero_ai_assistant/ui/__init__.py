"""
UI Module - Perfect UI Dashboard with Task Management
"""

# Import classes only when needed to avoid circular imports
def get_dashboard():
    from .dashboard import UIDashboard
    return UIDashboard

def get_task_manager():
    from .task_manager import TaskManager
    return TaskManager

def get_status_display():
    from .status_display import StatusDisplay
    return StatusDisplay

# For backward compatibility
UIDashboard = None
TaskManager = None
StatusDisplay = None

def __getattr__(name):
    if name == 'UIDashboard':
        from .dashboard import UIDashboard
        return UIDashboard
    elif name == 'TaskManager':
        from .task_manager import TaskManager
        return TaskManager
    elif name == 'StatusDisplay':
        from .status_display import StatusDisplay
        return StatusDisplay
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")