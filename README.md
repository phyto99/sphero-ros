# Sphero AI Assistant (not complete)
<img width="3339" height="1632" alt="image" src="https://github.com/user-attachments/assets/836389bd-daee-4e78-9629-a588520c8155" />

A low-maintenance, productivity-focused AI assistant that uses Sphero Bolt as a dynamic expression and input device. The system provides multilingual communication, psychological optimization for user growth, and comprehensive productivity management.

## Features

- **Auto-Startup**: Automatically launches on system boot and initializes all components
- **Perfect UI**: Intuitive dashboard optimized for daily productivity
- **Autonomous AI**: Intelligent decision-making for Sphero usage and system behavior
- **Multilingual Communication**: Strategic language selection for optimal learning
- **Comprehensive Monitoring**: Screen, task, and browser activity tracking with AI summaries
- **Dynamic Tool Creation**: AI creates input devices on-the-fly (volume knob, controller, etc.)
- **Therapeutic Personality**: Growth-oriented communication with positive framing

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sphero-ai-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install startup service (optional):
```bash
python -m sphero_ai_assistant.main --install-startup
```

## Usage

### Manual Start
```bash
python -m sphero_ai_assistant.main
```

### Startup Mode (for auto-startup)
```bash
python -m sphero_ai_assistant.main --startup
```

### Configuration
Configuration files are stored in the `config/` directory:
- `system.json`: System-wide settings
- `ui.json`: UI configuration
- `sphero.json`: Sphero-specific settings
- `user_preferences.json`: User preferences and restrictions

## Architecture

The system is built with a modular architecture:

- **Core**: AI Agent, Decision Engine, Personality Core, Memory System
- **Config**: Configuration management for all system settings
- **Startup**: Auto-startup service and Ollama initialization
- **UI**: Perfect dashboard interface (Task 2)
- **Sphero**: Dynamic Sphero integration (Task 3)
- **Communication**: Multilingual and dual-channel communication (Tasks 10-11)
- **Monitoring**: Comprehensive activity tracking (Tasks 7-8)

## Requirements Implemented

### Task 1: Core System Foundation and Auto-Startup
- ✅ Modular project structure for all system components
- ✅ Auto-startup service that launches on system boot
- ✅ Ollama AI initialization
- ✅ Basic configuration management system
- ✅ Visual feedback on initialization progress

## Development

The project follows a spec-driven development approach with detailed requirements, design, and implementation tasks defined in `.kiro/specs/sphero-ai-assistant/`.

## License

[License information to be added]
