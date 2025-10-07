# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DouDou (豆豆) is a modern desktop voice assistant built with Flet framework, designed specifically for Chinese users. It provides real-time speech recognition using FunASR (Alibaba's Paraformer model) with advanced AI text correction and translation capabilities. The project has completed its modularization refactoring and now features a clean, maintainable package-based architecture.

**Project Status**: Active Development | Modular Architecture ✅ | Production Ready

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Main application (recommended)
python main.py

# Direct source launch (development)
cd src && python flet_app.py

# Windows convenience scripts (from project root)
run.bat              # Quick launch
run_as_admin.bat     # Administrator privileges (for audio driver issues)
启动DouDou.bat       # Smart launcher with auto-setup (recommended for first-time users)
```

### FunASR Model Management
```bash
# Download required models (run once)
python download_models.py

# Models are cached at:
# Windows: C:\Users\<username>\.cache\modelscope\hub\models\damo\
# Linux/macOS: ~/.cache/modelscope/hub/models/damo/
```

### Testing
```bash
# Run specific tests
python -m pytest tests/test_vad_system.py
python -m pytest tests/test_audio_engine.py

# Run with audio device testing
python -m pytest tests/test_audio_backends.py -v
```

### Logging
Application logs are stored in:
- Windows: `%TEMP%\doudou_logs\doudou_YYYY-MM-DD_HH-MM-SS_SESSIONID.log`
- Linux/macOS: `/tmp/doudou_logs/doudou_YYYY-MM-DD_HH-MM-SS_SESSIONID.log`

Each application session creates a unique log file with session ID for debugging.

## Architecture Overview

### Modular Architecture (Current State ✅)

The project uses a clean modular architecture with clear separation of concerns:

```
src/
├── flet_app.py              # Main application entry (800 lines)
├── core/                    # Core functionality modules
│   ├── audio_engine.py          # Audio processing engine
│   ├── audio_recorder.py        # Recording management
│   ├── continuous_recorder.py   # Real-time recording
│   ├── vad_system.py            # Voice activity detection
│   ├── direct_funasr.py         # FunASR integration
│   ├── ai_integration.py        # AI processor
│   ├── transcription_handler.py # Transcription logic
│   ├── recognition_pipeline.py  # Recognition workflow
│   ├── task_manager.py          # Task management (old system)
│   ├── task_adapter.py          # Task system adapter
│   ├── unified_task_manager.py  # Unified task system
│   └── task_processors/         # Task processor modules
│       ├── base_processor.py        # Base processor class
│       ├── correction_processor.py  # AI correction
│       └── translation_processor.py # AI translation
├── ui/                      # User interface modules
│   ├── components.py            # Core UI components
│   ├── dialogs.py               # Dialog windows
│   ├── result_card_new.py       # Result display card
│   ├── task_monitor.py          # Task monitoring UI
│   └── enhanced_settings_dialog.py  # Settings interface
└── utils/                   # Utility modules
    ├── config_manager.py        # Configuration management
    └── logger.py                # Logging system
```

### Core Components

#### 1. Audio Processing Pipeline
The application uses a sophisticated audio processing chain:

**Multi-backend Audio Support**:
- PyAudioWPatch (preferred for Windows WASAPI)
- Standard PyAudio (fallback)
- sounddevice (backup option)

**Hybrid VAD (Voice Activity Detection)**:
- Energy-based detection with adaptive thresholds
- Zero-crossing rate analysis
- Time window constraints (0.5s min, 8s max speech segments)
- Confidence scoring with temporal smoothing
- Implemented in `core/vad_system.py`

**Real-time Processing Pipeline**:
- Continuous audio buffering
- VAD-driven speech segmentation
- Automatic recognition triggering
- AI text correction and translation integration

#### 2. Task Management System
The project uses a **mainline + parallel task pools** architecture:

**Mainline Task**: Speech Recognition
- Single task queue for audio recognition
- Managed by `core/task_manager.py` (old system)

**Parallel Task Pools**:
- **AI Correction Pool**: Processes recognized text for improvements
- **AI Translation Pool**: Translates corrected text to target language
- Both pools update the same UI message block

**Key Features**:
- Non-blocking parallel processing
- Task processor registry for extensibility
- Future-based async task handling
- UI updates via thread-safe dispatch

#### 3. Speech Recognition
- **FunASR Integration**: Uses Alibaba's Paraformer model for Chinese
- **Local Processing**: All speech data processed locally for privacy
- **Model Management**: Automatic download and caching
- **Three Models**:
  - speech_paraformer-large: Main ASR model
  - speech_fsmn_vad: Voice activity detection
  - punc_ct-transformer: Punctuation restoration

#### 4. AI Integration
**Smart Content Extraction**:
- `_filter_ai_thinking_content()`: Basic XML tag filtering
- `_extract_correction_result()`: Smart correction extraction with scoring
- `_extract_translation_result()`: Smart translation extraction with language detection

**Filtered Content**:
- `<think>`, `<thinking>`, `<reasoning>`, `<analysis>` tags
- `<step>`, `<process>`, `<思考>` tags
- Dialog markers (Human:/Assistant:)
- Analysis descriptions and explanations

**Applied To**:
- AI correction results
- AI translation results
- AI summary reports

#### 5. UI Architecture (Flet-based)
- **Material Design 3**: Modern UI with Flet framework
- **2-Column Layout**: 900x650 window with controls and results
- **Real-time Visualization**: Waveform and volume display
- **Message Block System**: Original text + correction + translation in one block
- **Task Monitoring**: Real-time status and progress display

### Key Technical Decisions

#### Audio Driver Compatibility
Addresses Windows audio driver compatibility issues:
- PyAudioWPatch for WASAPI support (resolves Error -9999)
- Multiple fallback audio backends
- Device detection and testing utilities
- Admin privilege support for driver access

#### Chinese Language Optimization
- FunASR Paraformer model trained for Chinese
- 16kHz sampling rate optimized for speech recognition
- AI text correction for recognition errors
- Chinese punctuation and grammar support

#### Privacy-First Design
- All processing happens locally
- No cloud dependencies for core functionality
- AI integration only for optional text enhancement
- Configurable OpenAI-compatible API support

## Configuration

### Settings Management
Settings are stored in `docs/config/doudou_settings.json`:

```json
{
  "ai_services": {
    "default": {
      "api_key": "your-api-key",
      "base_url": "http://localhost:11434/v1",
      "model_name": "qwen3:0.6b"
    },
    "translation": {
      "target_language": "ja",
      "api_key": "your-api-key",
      "base_url": "http://localhost:11434/v1",
      "model_name": "qwen3:0.6b"
    }
  },
  "language": "zh",
  "use_vad": true,
  "use_punc": true,
  "enable_ai_optimization": true,
  "enable_translation": true,
  "realtime_mode": false
}
```

### Audio Configuration
Critical audio parameters in `core/audio_engine.py`:
- `CHUNK = 1024`: Audio buffer size
- `RATE = 16000`: Sampling rate (optimized for FunASR)
- `CHANNELS = 1`: Mono recording
- `FORMAT = pyaudio.paInt16`: 16-bit audio format

## Development Patterns

### Error Handling Strategy
Comprehensive error handling throughout the application:
- Audio device testing with multiple backend fallbacks
- Graceful degradation when audio systems fail
- Detailed logging for troubleshooting
- User-friendly error messages and recovery suggestions

### Threading Architecture
- **Main UI Thread**: Flet interface updates
- **Background Threads**: Audio processing and VAD
- **Task Pools**: Parallel correction and translation processing
- **Thread-safe Communication**: UI dispatch mechanism

### State Management
- Central application state in `QuQuFletApp` class (flet_app.py)
- Real-time mode toggles and status tracking
- Audio buffer management with timestamps
- Recognition result queuing and processing
- UI message block updates

### Logging System
Session-based logging with unique identifiers:
- Format: `doudou_YYYY-MM-DD_HH-MM-SS_UUID.log`
- Location: System temp directory (`/tmp/doudou_logs/`)
- Features: Automatic rotation, debug and error level separation
- Implemented in `utils/logger.py`

## Platform-Specific Considerations

### Windows Specifics
- PyAudioWPatch integration for WASAPI support
- Audio driver permission requirements
- Admin privilege batch scripts for audio access
- Windows-specific audio device enumeration

### Audio Device Management
- Automatic device detection and enumeration
- WASAPI and Loopback device identification
- Multi-configuration testing (44.1kHz, 48kHz, 16kHz)
- Device-specific error handling and recovery

## Recent Major Updates

### October 2025
1. **AI Smart Extractors** (Oct 7)
   - Intelligent translation result extraction with language detection
   - Smart correction result extraction with scoring mechanism
   - Applied to all AI functions (correction, translation, summary)
   - Comprehensive filtering of thinking content and dialog markers

2. **Task System Architecture** (Oct 7)
   - Implemented mainline + parallel task pool architecture
   - Fixed task system integration (recognition → correction → translation)
   - UI message block updates for correction and translation results
   - Proper record_id handling and control data binding

3. **Logging System Refactor** (Oct 7)
   - Changed project name from QuQu to DouDou
   - Session-based log file naming with UUID
   - Independent log files for each application startup

4. **UI Integration Enhancements** (Oct 5-7)
   - Fixed ResultCard control updates and data binding
   - Implemented message block display (original + correction + translation)
   - Real-time UI updates for AI processing results

### Key Improvements
- ✅ Modular architecture completed
- ✅ Task system fully functional
- ✅ AI smart extraction implemented
- ✅ Logging system enhanced
- ✅ UI integration polished

## Development Guidelines

When working on this codebase:

1. **Maintain Modularity**: Keep modules focused and independent
2. **Follow Threading Rules**: Use UI dispatch for all Flet updates
3. **Test Audio Chain**: Verify audio pipeline after changes
4. **Update Documentation**: Keep CLAUDE.md and relevant docs in sync
5. **Session Logging**: Check logs in temp directory for debugging
6. **Respect Architecture**: Follow mainline + parallel pool pattern

### File Naming Conventions
- Core modules: lowercase with underscores (e.g., `audio_engine.py`)
- UI components: descriptive names (e.g., `result_card_new.py`)
- Utilities: functional names (e.g., `config_manager.py`)
- Tests: prefix with `test_` (e.g., `test_vad_system.py`)

### Code Organization
- Keep classes focused (single responsibility)
- Use type hints for better code clarity
- Document complex algorithms and decisions
- Maintain backward compatibility during refactoring

## Troubleshooting

### Common Issues

**Audio Device Error -9999 (Windows)**:
- Solution: Run with admin privileges using `run_as_admin.bat`

**Models Not Found**:
- Solution: Run `python download_models.py` once

**AI Functions Not Working**:
- Check AI service configuration in settings
- Verify API endpoint is accessible
- Review logs in temp directory

**Window Closing But Process Remains**:
- Normal behavior: Monitoring threads need cleanup time
- Force kill: `taskkill /F /IM python.exe` (Windows)

## Additional Resources

- Main README: `/README.md`
- Architecture Design: `/docs/architecture/`
- API Documentation: `/docs/development/`
- Setup Guides: `/docs/getting-started/`
- Issue Tracker: GitHub Issues

---

**Last Updated**: 2025-10-07
**Project Version**: v1.0.0
**Status**: Production Ready
