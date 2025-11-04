# AI Job Bidder - Automated Job Application System

An intelligent job application automation system that uses AI to tailor resumes and fill out application forms automatically.

## 🏗️ Architecture

### Project Structure

```
alphajob/
├── src/                          # Source code
│   ├── config/                   # Configuration management
│   ├── models/                   # Data models
│   ├── services/                 # Business logic services
│   ├── handlers/                 # Form and field handlers
│   ├── utils/                    # Utility functions
├── data/                         # Runtime data (gitignored)
├── scripts/                      # Utility scripts
├── tests/                        # Test suite
```

## 🚀 Features

- **AI-Powered Resume Tailoring**: Automatically customizes resumes for each job using Ollama LLM
- **Intelligent Form Filling**: Smart form field detection and filling with context-aware responses
- **Browser Automation**: Automated application submission using Playwright
- **Multi-Format Support**: Handles DOCX and TXT resume formats
- **Configuration Management**: Centralized configuration with environment variable support
- **Modular Architecture**: Clean separation of concerns for easy maintenance and testing

## 📋 Prerequisites

- Python 3.9+
- Ollama installed and running locally
- Playwright browsers installed

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cloudhighfive/alphajob.git
   cd alphajob
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # OR
   venv\\Scripts\\activate    # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install
   ```

5. **Setup configuration**
   ```bash
   cp config.json.example config.json
   cp .env.example .env
   ```
   
   Edit `config.json` with your information:
   - Personal details
   - Work experience
   - Skills
   - Preferences

## 🎯 Usage

### Basic Usage

```bash
python main.py
```

### Using the Refactored Architecture

```python
from src.config import get_settings
from src.services import AIService, BrowserService, ResumeService

# Load configuration
settings = get_settings()

# Initialize services
ai_service = AIService(settings)
browser_service = BrowserService(settings)
resume_service = ResumeService(settings)

# Use services
tailored_resume = resume_service.tailor_for_job(job_description, job_title, company)
```

## 📝 Configuration

### config.json

The main configuration file contains:

```json
{
  "user_info": {
    "personal_info": {...},
    "links": {...},
    "work_authorization": {...},
    "demographics": {...},
    "background": {...},
    "preferences": {...},
    "files": {...}
  },
  "ai_settings": {
    "model": "llama3.1",
    "temperature": 0.7,
    "tone": "professional and enthusiastic"
  },
  "prompts": {...}
}
```

### Environment Variables (.env)

```env
DEBUG=false
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT=30
```

## 🏛️ Architecture Principles

### Separation of Concerns

- **Config Layer**: Centralized configuration management
- **Model Layer**: Data structures and validation
- **Service Layer**: Business logic and external integrations
- **Handler Layer**: Request/response handling
- **Utility Layer**: Shared helper functions

### Design Patterns

- **Dependency Injection**: Services receive dependencies via constructor
- **Factory Pattern**: Configuration factory for creating settings
- **Repository Pattern**: Data access abstraction
- **Strategy Pattern**: Multiple strategies for form field handling

### Best Practices

1. **Type Hints**: All functions have type annotations
2. **Pydantic Models**: Strong validation for configuration and data
3. **Logging**: Centralized logging with proper levels
4. **Error Handling**: Comprehensive error handling with meaningful messages
5. **Documentation**: Docstrings for all public functions and classes
6. **Testing**: Unit tests for critical components

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_ai_service.py
```

## 🔄 Migration from Legacy Code

The project has been refactored from a monolithic 2359-line script to a modular architecture. Key changes:

1. **Configuration**: Moved from manual dict loading to Pydantic models with validation
2. **AI Integration**: Extracted into `AIService` with clean interface
3. **Browser Automation**: Isolated in `BrowserService` with proper encapsulation
4. **Resume Handling**: Centralized in `ResumeService`
5. **Form Handling**: Modularized into handler classes

### Backwards Compatibility

The legacy `ai_job_bidder.py` is still available but deprecated. New code should use the modular `src/` structure.

## 📦 Dependencies

Key dependencies:
- `pydantic` - Data validation and settings management
- `pydantic-settings` - Settings from environment variables
- `ollama` - AI/LLM integration
- `playwright` - Browser automation
- `python-docx` - DOCX file handling
- `beautifulsoup4` - HTML parsing
- `python-dotenv` - Environment variable management

## 🤝 Contributing

1. Follow the established architecture patterns
2. Add tests for new features
3. Update documentation
4. Use type hints
5. Follow PEP 8 style guide

---

> **Note:** This README was generated by AI to provide a quick overview of the project.
