# Random Short Story Generator - Premium Edition

A sophisticated GUI application that generates complex, original short stories using local Ollama language models. Features batch generation, story comparison, model management, and comprehensive analytics.

**Version:** 1.0.0
**Author:** Random Story Generator Team

## Configuration

The application can be configured using the `config.ini` file:

```ini
[DEFAULTS]
default_word_count = 500
default_max_chars = 280
rapid_mode_word_count = 300
thread_post_interval_minutes = 10

[UI]
spinbox_min_words = 100
spinbox_max_words = 2000

[LOGGING]
level = INFO
```

## Features

✨ **Single Story Generation**
- Generate stories with customizable genre, tone, and word count
- Support for custom prompts and story templates
- Real-time streaming generation
- Easy-to-use interface with dark/light themes

⚡ **Batch Generation & Comparison**
- Generate multiple stories at once with variety modes
- Use multiple models simultaneously for comparison
- Automatic best-story selection based on content quality
- Rapid mode for faster generation with shorter stories

🔧 **Model Management**
- View all available Ollama models
- Pull new models directly from the app
- Switch between models easily
- Support for popular models (llama2, mistral, neural-chat, etc.)

💾 **Story Management**
- Save stories as markdown files with metadata
- Browse and organize saved stories with ratings and favorites
- Copy stories to clipboard
- Export to PDF, DOCX, and TXT formats
- Delete old stories safely

📊 **Analytics & Statistics**
- Comprehensive story metrics (readability, word variety, etc.)
- Model performance tracking
- Genre and tone analytics
- Timeline charts and engagement metrics

🎯 **Content Scheduling**
- Queue stories for future posting
- Thread formatting for social media
- Automated scheduling with customizable intervals

⚙️ **Presets System**
- Save and reuse generation settings
- Quick access to favorite configurations
- Template management for consistent results

## Prerequisites

1. **Install Ollama**: Download and install Ollama from [ollama.ai](https://ollama.ai)
2. **Pull at least one model**: 
   ```
   ollama pull llama2
   ```
3. **Start Ollama service**: 
   ```
   ollama serve
   ```

## Installation

1. Ensure you have Python 3.x installed
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### GUI Application (Recommended)
```
python gui_app.py
```

### Command-line
```
python main.py
```

## Application Tabs

1. **Generate Story** - Create individual stories with customization
2. **Batch Generate & Compare** - Generate multiple stories and find the best one
3. **Model Management** - View available models and pull new ones
4. **Saved Stories** - Browse and manage your generated stories

## Requirements

- Python 3.x
- Ollama installed and running
- At least one Ollama model pulled (e.g., llama2)
- Dependencies: `requests`

## File Structure

- `gui_app.py` - Main GUI application
- `story_generator.py` - Core story generation logic and model management
- `main.py` - Command-line interface
- `generated_stories/` - Directory where stories are saved as markdown files

## Changelog

### Version 1.0.0
- Complete codebase audit and optimization
- Enhanced error handling and logging
- Improved input validation and security
- Added comprehensive unit tests
- Constants-based configuration for maintainability
- Enhanced documentation and type hints
- Added configuration file support
- Improved user interface with better validation
- Added analytics and metrics dashboard
- Content scheduling and queue management
- Presets system for saving generation settings
- Export functionality (PDF, DOCX, TXT)
- Thread formatting for social media
- Dark/light theme support
- Model performance tracking
- Story ratings and favorites system