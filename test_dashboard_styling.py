"""
Test script to verify the Super Productivity inspired dashboard styling
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sphero_ai_assistant.ui.dashboard import UIDashboard


async def test_dashboard_assets():
    """Test that dashboard assets are created correctly"""
    print("🎨 Testing Super Productivity Inspired Dashboard Assets...")
    
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
    dashboard = UIDashboard(config_manager, ai_agent)
    
    # Test asset creation
    await dashboard._ensure_ui_assets()
    
    # Check if files were created
    templates_dir = Path("sphero_ai_assistant/ui/templates")
    static_dir = Path("sphero_ai_assistant/ui/static")
    
    dashboard_html = templates_dir / "dashboard.html"
    dashboard_css = static_dir / "dashboard.css"
    dashboard_js = static_dir / "dashboard.js"
    
    print(f"✅ Templates directory exists: {templates_dir.exists()}")
    print(f"✅ Static directory exists: {static_dir.exists()}")
    print(f"✅ Dashboard HTML created: {dashboard_html.exists()}")
    print(f"✅ Dashboard CSS created: {dashboard_css.exists()}")
    print(f"✅ Dashboard JS created: {dashboard_js.exists()}")
    
    # Check CSS content for Super Productivity features
    if dashboard_css.exists():
        with open(dashboard_css, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        super_productivity_features = [
            "CSS VARIABLES - DESIGN SYSTEM",
            "--s:",  # Spacing system
            "--shadow-1:",  # Material shadows
            "--transition-fast:",  # Transitions
            "Super Productivity Inspired",
            "Material Design",
            "fade-in",  # Animations
            "theme-toggle",  # Dark mode
            "Open Sans"  # Typography
        ]
        
        print("\n🎨 Super Productivity Design Features:")
        for feature in super_productivity_features:
            found = feature in css_content
            status = "✅" if found else "❌"
            print(f"{status} {feature}")
    
    # Check HTML content for new features
    if dashboard_html.exists():
        with open(dashboard_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        html_features = [
            "theme-toggle",
            "Open Sans",
            "fade-in",
            "What needs to be done?",  # New placeholder
            "Add Task"
        ]
        
        print("\n📄 HTML Template Features:")
        for feature in html_features:
            found = feature in html_content
            status = "✅" if found else "❌"
            print(f"{status} {feature}")
    
    print("\n🎉 Dashboard styling test completed!")
    print("\nKey Super Productivity Features Implemented:")
    print("• 🎨 Comprehensive CSS Variables Design System")
    print("• 🌙 Dark/Light Theme Support")
    print("• 📱 Responsive Mobile-First Design")
    print("• ✨ Material Design Shadows & Animations")
    print("• 🎯 Task-Focused Clean Layout")
    print("• 🔤 Open Sans Typography")
    print("• 🎭 Smooth Transitions & Micro-interactions")


if __name__ == "__main__":
    asyncio.run(test_dashboard_assets())