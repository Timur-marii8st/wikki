<div align="center">

# 🌸 Wikki v2.0 - AI Desktop Companion

**[ 🇷🇺 Русский ](#-русский) | [ 🇬🇧 English ](#-english)**

</div>

---

## 🇬🇧 English

> A cute AI companion with a 3D avatar that lives on your desktop and can talk to you.

### ✨ Features

- 💬 **Chat with AI** - Talk to Gemma 3 via llama.cpp.
- 🎭 **3D Avatar** - A living character with emotions and animations.
- 🔊 **Text-to-Speech** - Wikki voices her responses.
- 🎤 **Voice Input (STT)** - Speak to Wikki (Ctrl+Shift+V).
- 📸 **Auto-screenshots** - Wikki sees what you are doing and comments on it.
- 🪟 **Dual Windows** - Avatar is always on top; chat window appears on demand.
- 🦙 **Llama.cpp** - Manage the server directly from the application.

### 🚀 Quick Start

#### Requirements
- [Rust](https://rustup.rs/)
- [llama.cpp](https://github.com/ggerganov/llama.cpp) with the Gemma 3 model
- Node.js + pnpm

#### Installation
```bash
# 1. Build llama.cpp and download the model
# See LLAMA_CPP_GUIDE.md

# 2. Install dependencies
pnpm install

# 3. Run development mode
pnpm tauri dev

# 4. Click on the status dot in the UI to start the llama-server
```

More details: [LLAMA_CPP_GUIDE.md](LLAMA_CPP_GUIDE.md)

### 📖 Documentation

- [LLAMA_CPP_GUIDE.md](LLAMA_CPP_GUIDE.md) - Working with llama.cpp
- [SILERO_TTS_GUIDE.md](SILERO_TTS_GUIDE.md) - Silero TTS Setup
- [QUICK_3D_SETUP.md](QUICK_3D_SETUP.md) - Quick 3D model setup
- [3D_MODEL_GUIDE.md](3D_MODEL_GUIDE.md) - Full guide on 3D models
- [QUICKSTART.md](QUICKSTART.md) - Quick Start
- [SETUP.md](SETUP.md) - Detailed Installation
- [ROADMAP.md](ROADMAP.md) - Development Plan
- [CHANGES.md](CHANGES.md) - Changelog

### 🎯 Project Status

#### ✅ Implemented
- Basic chat with llama.cpp
- 3D Avatar (simple geometry)
- TTS (System synthesizer)
- **STT (Transcription via Gemma 3)** 🆕
- Automatic screenshots
- Voice recording (15s limit)
- **Control llama-server from UI** 🆕
- **Multimodality (text + audio + images)** 🆕

#### 🚧 In Progress
- High-quality 3D model (GLB)
- Settings UI

#### 📋 Planned
- System tray menu
- History export
- Multi-language support
- Plugins

### 🏗️ Architecture

```
Wikki v2.0
├── Frontend (React + Three.js)
│   ├── Chat UI
│   └── 3D Avatar
└── Backend (Rust + Tauri)
    ├── Ollama Client
    ├── TTS Engine
    ├── Screenshot Service
    └── Window Management
```

**Technologies:**
- Tauri 2.0 - Desktop framework
- React 18 - UI
- Three.js - 3D graphics
- Zustand - State management
- Ollama - Local LLM
- Rust - Backend

### 💡 Why Wikki?

- **Privacy** - Everything runs locally.
- **Free** - No API costs.
- **Lightweight** - ~4.5GB RAM at peak.
- **Customizable** - Open Source.

### 📝 License

MIT

### 🙏 Acknowledgements

- [Ollama](https://ollama.ai/) - Local LLM runtime
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Local LLM inference
- [Silero TTS](https://github.com/snakers4/silero-models) - Neural TTS
- [Gemma 3](https://ai.google.dev/) - The model that powers Wikki
- [Tauri](https://tauri.app/) - Desktop framework
- [Three.js](https://threejs.org/) - 3D library
- [React Three Fiber](https://docs.pmnd.rs/react-three-fiber) - React renderer for Three.js

---

## 🇷🇺 Русский

> Милый AI компаньон с 3D аватаром, который живет на вашем рабочем столе и с которым можно говорить.

### ✨ Возможности

- 💬 **Чат с AI** - общайтесь с Gemma 3 через llama.cpp
- 🎭 **3D Аватар** - живой персонаж с эмоциями и анимациями
- 🔊 **Text-to-Speech** - Wikki озвучивает свои ответы
- 🎤 **Голосовой ввод (STT)** - говорите с Wikki (Ctrl+Shift+V)
- 📸 **Автоскриншоты** - Wikki видит, что вы делаете, и комментирует
- 🪟 **Два окна** - аватар всегда поверх, чат по требованию
- 🦙 **Llama.cpp** - управление сервером прямо из приложения

### 🚀 Быстрый старт

#### Требования
- [Rust](https://rustup.rs/)
- [llama.cpp](https://github.com/ggerganov/llama.cpp) с моделью Gemma 3
- Node.js + pnpm

#### Установка
```bash
# 1. Соберите llama.cpp и скачайте модель
# См. LLAMA_CPP_GUIDE.md

# 2. Установите зависимости
pnpm install

# 3. Запустите
pnpm tauri dev

# 4. В UI кликните на status dot и запустите llama-server
```

Подробнее: [LLAMA_CPP_GUIDE.md](LLAMA_CPP_GUIDE.md)

### 📖 Документация

- [LLAMA_CPP_GUIDE.md](LLAMA_CPP_GUIDE.md) - Работа с llama.cpp
- [SILERO_TTS_GUIDE.md](SILERO_TTS_GUIDE.md) - Настройка Silero TTS
- [QUICK_3D_SETUP.md](QUICK_3D_SETUP.md) - Быстрая настройка 3D модели
- [3D_MODEL_GUIDE.md](3D_MODEL_GUIDE.md) - Полное руководство по 3D моделям
- [QUICKSTART.md](QUICKSTART.md) - Быстрый старт
- [SETUP.md](SETUP.md) - Детальная установка
- [ROADMAP.md](ROADMAP.md) - План развития
- [CHANGES.md](CHANGES.md) - Список изменений

### 🎯 Статус проекта

#### ✅ Реализовано
- Базовый чат с llama.cpp
- 3D аватар (простая геометрия)
- TTS (системный синтезатор)
- **STT (транскрипция через Gemma 3)** 🆕
- Автоматические скриншоты
- Голосовая запись с ограничением 15 сек
- **Управление llama-server из UI** 🆕
- **Мультимодальность (текст + аудио + изображения)** 🆕

#### 🚧 В разработке
- Качественная 3D модель (GLB)
- UI настроек

#### 📋 Планируется
- System tray меню
- Экспорт истории
- Мультиязычность
- Плагины

### 🏗️ Архитектура

```
Wikki v2.0
├── Frontend (React + Three.js)
│   ├── Chat UI
│   └── 3D Avatar
└── Backend (Rust + Tauri)
    ├── Ollama Client
    ├── TTS Engine
    ├── Screenshot Service
    └── Window Management
```

**Технологии:**
- Tauri 2.0 - Desktop framework
- React 18 - UI
- Three.js - 3D graphics
- Zustand - State management
- Ollama - Local LLM
- Rust - Backend

### 💡 Почему Wikki?

- **Приватность** - все работает локально
- **Бесплатно** - нет API costs
- **Легковесно** - ~4.5GB RAM в пике
- **Кастомизируемо** - открытый исходный код

### 📝 Лицензия

MIT

### 🙏 Благодарности

- [Ollama](https://ollama.ai/) - Local LLM runtime
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Local LLM inference
- [Silero TTS](https://github.com/snakers4/silero-models) - Neural TTS
- [Gemma 3](https://ai.google.dev/) - The model that powers Wikki
- [Tauri](https://tauri.app/) - Desktop framework
- [Three.js](https://threejs.org/) - 3D library
- [React Three Fiber](https://docs.pmnd.rs/react-three-fiber) - React renderer for Three.js

---

Made with ❤️