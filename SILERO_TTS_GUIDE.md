# 🔊 Silero TTS Integration Guide

## Что изменилось

Wikki теперь использует Silero TTS вместо системного синтезатора!

### Преимущества Silero TTS:
- ✅ Качественный голос (нейросеть)
- ✅ Поддержка русского и английского
- ✅ SSML для эмоциональной речи
- ✅ Контроль высоты тона и скорости
- ✅ Работает оффлайн

## 🚀 Установка

### 1. Установите Python зависимости

```bash
cd src-tauri
pip install -r requirements.txt
```

Или с conda:
```bash
conda install pytorch torchaudio -c pytorch
pip install omegaconf
```

### 2. Скопируйте Python скрипт

При сборке `silero_tts_service.py` должен быть рядом с executable.

Для dev режима скрипт уже в `src-tauri/src/services/`

## 🎯 Архитектура

### Long-running Python Process

```
┌─────────────────────────────────────────┐
│         Tauri (Rust)                    │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  SileroTtsEngine                 │  │
│  │                                  │  │
│  │  - Manages Python process       │  │
│  │  - Sends JSON via stdin         │  │
│  │  - Receives JSON via stdout     │  │
│  └──────────┬───────────────────────┘  │
│             │                           │
└─────────────┼───────────────────────────┘
              │ JSON over stdin/stdout
              │
┌─────────────▼───────────────────────────┐
│    Python Process                       │
│    (silero_tts_service.py)              │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Silero Models                   │  │
│  │  - Russian (v5_ru)               │  │
│  │  - English (lj_16khz)            │  │
│  │  - Loaded once, kept in memory   │  │
│  └──────────────────────────────────┘  │
│                                         │
│  - Receives commands via stdin          │
│  - Generates audio                      │
│  - Returns base64 WAV via stdout        │
└─────────────────────────────────────────┘
```

### Почему такая архитектура?

**Проблема:** Загрузка модели Silero занимает 2-5 секунд

**Решение:** Long-running process
- Модель загружается один раз при старте
- Процесс живет все время работы приложения
- Последующие запросы быстрые (0.5-2 сек)

**Альтернативы рассмотренные:**
1. ❌ Subprocess каждый раз - слишком медленно
2. ❌ PyO3 - сложная сборка, проблемы с зависимостями
3. ❌ HTTP server - избыточная сложность
4. ✅ stdin/stdout - простой, надежный, быстрый

## 🎤 SSML Support

### Автоматическая эмоциональность

Wikki автоматически применяет SSML теги на основе эмоций:

```python
emotion_map = {
    'happy': {'pitch': 'high', 'rate': 'fast'},
    'excited': {'pitch': 'x-high', 'rate': 'fast'},
    'sad': {'pitch': 'low', 'rate': 'slow'},
    'thinking': {'pitch': 'medium', 'rate': 'slow'},
    'surprised': {'pitch': 'high', 'rate': 'medium'},
    'neutral': {'pitch': 'medium', 'rate': 'medium'}
}
```

### Пример SSML

**Входной текст:**
```
"That looks really interesting! I love watching you work!"
```

**С эмоцией "happy":**
```xml
<speak>
<prosody pitch="high" rate="fast">
That looks really interesting! I love watching you work!
</prosody>
</speak>
```

### LLM может генерировать SSML

Можно обновить system prompt чтобы LLM сама добавляла SSML:

```
You can use SSML tags to control your voice:
- <prosody pitch="high">text</prosody> - higher pitch
- <prosody rate="slow">text</prosody> - slower speech
- <break time="500ms"/> - pause for 500ms

Example: "I'm so <prosody pitch="x-high">excited</prosody>!"
```

## 🌍 Языки

### Поддерживаемые языки

- **Русский (ru)** - Speaker: 'baya' (женский голос)
- **Английский (en)** - Speaker: 'lj_16khz'

### Определение языка

**По умолчанию:** Английский

**Изменение через API:**
```typescript
await invoke('set_tts_language', { language: 'ru' });
```

**Получение текущего:**
```typescript
const lang = await invoke<string>('get_tts_language');
```

### Автоопределение (TODO)

Можно добавить определение по системному языку:

```rust
// В setup()
let system_lang = sys_locale::get_locale()
    .and_then(|l| l.split('-').next().map(String::from))
    .unwrap_or_else(|| "en".to_string());

tts.set_language(&system_lang)?;
```

## 📊 Производительность

### Использование ресурсов

| Компонент | RAM | CPU | Время |
|-----------|-----|-----|-------|
| Silero Model (loaded) | ~200MB | 0% idle | - |
| First synthesis | - | 50-100% | 2-5s |
| Subsequent synthesis | - | 50-100% | 0.5-2s |

### Оптимизация

**Preload модели при старте:**
```typescript
await invoke('preload_tts_model', { language: 'en' });
await invoke('preload_tts_model', { language: 'ru' });
```

**Кэширование (TODO):**
- Сохранять часто используемые фразы
- Использовать hash текста как ключ

## 🔧 API Reference

### Tauri Commands

#### `synthesize_speech`
```typescript
await invoke('synthesize_speech', {
  text: 'Hello, world!',
  emotion: 'happy'
});
```

**Параметры:**
- `text: string` - Текст для озвучивания
- `emotion: string` - Эмоция (happy, sad, excited, thinking, surprised, neutral)

#### `stop_speech`
```typescript
await invoke('stop_speech');
```

Останавливает текущее воспроизведение.

#### `set_tts_language`
```typescript
await invoke('set_tts_language', { language: 'ru' });
```

**Параметры:**
- `language: string` - Код языка ('ru' или 'en')

#### `get_tts_language`
```typescript
const lang = await invoke<string>('get_tts_language');
console.log('Current language:', lang);
```

#### `preload_tts_model`
```typescript
await invoke('preload_tts_model', { language: 'ru' });
```

Загружает модель заранее для быстрого первого синтеза.

### Python Service Protocol

**Request format (stdin):**
```json
{
  "command": "synthesize",
  "text": "Hello, world!",
  "language": "en",
  "emotion": "happy",
  "use_ssml": true
}
```

**Response format (stdout):**
```json
{
  "success": true,
  "audio_base64": "UklGRiQAAABXQVZFZm10...",
  "sample_rate": 48000,
  "duration": 1.5
}
```

**Commands:**
- `synthesize` - Generate speech
- `load_model` - Preload model
- `ping` - Health check
- `shutdown` - Graceful shutdown

## 🐛 Troubleshooting

### Python process не запускается

**Проблема:** "Failed to start Python TTS service"

**Решения:**
1. Проверьте что Python установлен: `python --version`
2. Установите зависимости: `pip install -r requirements.txt`
3. Проверьте путь к скрипту
4. Попробуйте запустить вручную: `python silero_tts_service.py`

### Модель не загружается

**Проблема:** "Error loading model"

**Решения:**
1. Проверьте интернет (первая загрузка скачивает модель)
2. Проверьте место на диске (~500MB на модель)
3. Очистите кэш torch: `rm -rf ~/.cache/torch/hub`

### Медленный синтез

**Проблема:** Каждый синтез занимает 5+ секунд

**Решения:**
1. Убедитесь что процесс не перезапускается каждый раз
2. Preload модели при старте
3. Используйте CPU с AVX2 support

### Нет звука

**Проблема:** Синтез работает, но звука нет

**Решения:**
1. Проверьте громкость системы
2. Проверьте что rodio может воспроизводить звук
3. Попробуйте другой audio backend

## 🔮 Будущие улучшения

- [ ] Кэширование синтезированных фраз
- [ ] Поддержка других языков (de, fr, es)
- [ ] Выбор голоса (male/female)
- [ ] Streaming audio (начать воспроизведение до окончания синтеза)
- [ ] GPU acceleration
- [ ] Настройка параметров через UI

## 📝 Примеры

### Пример 1: Простой синтез

```typescript
import { invoke } from '@tauri-apps/api/core';

async function speak(text: string) {
  try {
    await invoke('synthesize_speech', {
      text,
      emotion: 'neutral'
    });
  } catch (error) {
    console.error('TTS failed:', error);
  }
}

speak('Hello, I am Wikki!');
```

### Пример 2: С эмоциями

```typescript
async function speakWithEmotion(text: string, emotion: string) {
  await invoke('synthesize_speech', { text, emotion });
}

speakWithEmotion('I am so happy to see you!', 'happy');
speakWithEmotion('Oh no, something went wrong...', 'sad');
speakWithEmotion('Wow, that is amazing!', 'excited');
```

### Пример 3: Смена языка

```typescript
async function speakInRussian(text: string) {
  // Switch to Russian
  await invoke('set_tts_language', { language: 'ru' });
  
  // Speak
  await invoke('synthesize_speech', {
    text,
    emotion: 'neutral'
  });
  
  // Switch back to English
  await invoke('set_tts_language', { language: 'en' });
}

speakInRussian('Привет! Меня зовут Викки!');
```

### Пример 4: Preload для быстрого старта

```typescript
// При инициализации приложения
async function initTTS() {
  console.log('Preloading TTS models...');
  
  await invoke('preload_tts_model', { language: 'en' });
  await invoke('preload_tts_model', { language: 'ru' });
  
  console.log('TTS ready!');
}

initTTS();
```

---

**Версия:** 0.2.0  
**Дата:** 2026-02-01  
**Статус:** ✅ Реализовано
