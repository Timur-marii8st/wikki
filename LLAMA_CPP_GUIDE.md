# 🦙 Llama.cpp Integration Guide

## Что изменилось

Wikki теперь поддерживает работу с llama.cpp server вместо Ollama!

### Преимущества llama.cpp:
- ✅ Прямой контроль над моделью
- ✅ Мультимодальность (текст + аудио + изображения)
- ✅ Меньше overhead
- ✅ Гибкая конфигурация

## 🚀 Быстрый старт

### 1. Скачайте llama.cpp

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
```

### 2. Соберите llama-server

**Windows:**
```bash
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

Бинарник будет в `build\bin\llama-server.exe`

### 3. Скачайте модель Gemma 3

Поместите вашу GGUF модель в папку `models/`

Например:
```
C:\Users\elkgo\llama.cpp\models\gemma-3n-E4B-it-absolute-heresy-MPOA-iQ4_NL.gguf
```

### 4. Запустите Wikki

```bash
pnpm tauri dev
```

### 5. Настройте пути в UI

1. Кликните на цветную точку в titlebar
2. Введите пути к executable и модели
3. Нажмите "Start Server"

## 🎯 Использование

### Запуск сервера

**Вариант A: Через UI Wikki**
- Кликните на status dot
- Введите пути
- Нажмите "Start Server"

**Вариант B: Вручную**
```bash
cd C:\Users\elkgo\llama.cpp
build\bin\llama-server.exe -m models\gemma-3n-E4B-it-absolute-heresy-MPOA-iQ4_NL.gguf -ngl 99 -sm none -mg 0 --mmap --host 127.0.0.1 --port 8080

build\bin\llama-server.exe -m models\gemma-3n-E4B-it-absolute-heresy-MPOA-iQ4_NL.gguf -ngl 99 -sm none -mg 0 --host 0.0.0.0 --port 8080
```

### Проверка статуса

Цветная точка в titlebar показывает статус:
- 🟢 Зеленый - сервер работает
- 🔴 Красный - сервер остановлен
- 🟡 Желтый - запускается/останавливается
- ⚪ Серый - статус неизвестен

### Голосовой ввод (STT)

1. Нажмите и держите кнопку микрофона (или Ctrl+Shift+V)
2. Говорите (макс 15 секунд)
3. Отпустите кнопку
4. Если аудио >15 сек, появится предупреждение:
   - "OK" - обрезать до 15 сек и отправить
   - "Cancel" - отменить

## 🎤 Работа с аудио

### Ограничения

- **Максимальная длительность:** 15 секунд
- **Формат:** WAV/WebM
- **Sample rate:** 16kHz
- **Channels:** Mono

### Почему 15 секунд?

Gemma 3 рекомендует максимум 15 секунд аудио для оптимальной работы.

### Что происходит при превышении?

1. Wikki определяет длительность
2. Показывает предупреждение
3. Предлагает обрезать или отменить
4. Если обрезать - отправляет первые 15 секунд

## 📸 Мультимодальность

### Текст + Изображение

Автоматические скриншоты уже работают!

### Текст + Аудио

Используйте голосовой ввод (Ctrl+Shift+V)

### Текст + Изображение + Аудио

Пока не реализовано, но архитектура готова.

## 🔧 Конфигурация

### Параметры llama-server

```bash
-m <path>      # Путь к модели
-ngl 99        # Offload всех слоев на GPU (если есть)
-sm none       # Disable split mode
-mg 0          # Main GPU
--mmap         # Use memory mapping
--host         # Bind address
--port         # Port number
```

### Изменение портов

По умолчанию: `http://127.0.0.1:8080`

Чтобы изменить, отредактируйте:
- `src-tauri/src/services/ollama.rs` - `DEFAULT_LLAMA_CPP_URL`
- `src-tauri/src/commands/llama.rs` - health check URL

## 🐛 Troubleshooting

### Сервер не запускается

**Проблема:** "Failed to start llama-server"

**Решения:**
1. Проверьте пути к executable и модели
2. Убедитесь что порт 8080 свободен
3. Проверьте права на запуск executable
4. Попробуйте запустить вручную в терминале

### Сервер запустился, но не отвечает

**Проблема:** Status показывает "stopped" хотя процесс запущен

**Решения:**
1. Подождите 2-3 секунды после запуска
2. Проверьте `http://127.0.0.1:8080/health` в браузере
3. Проверьте логи llama-server

### Аудио не транскрибируется

**Проблема:** "Transcription failed"

**Решения:**
1. Убедитесь что сервер запущен
2. Проверьте что модель поддерживает аудио
3. Проверьте формат аудио (должен быть WAV/WebM)
4. Попробуйте записать короче (5-10 секунд)

### Высокое использование памяти

**Проблема:** Приложение использует много RAM

**Решения:**
1. Используйте меньшую квантизацию модели (Q4 вместо Q8)
2. Уменьшите context size в llama-server
3. Закройте другие приложения

## 📊 Производительность

### Использование ресурсов

| Компонент | RAM | CPU |
|-----------|-----|-----|
| Gemma 3 4B (Q4) | ~4GB | Зависит от запроса |
| llama-server | ~100MB | Idle: 0%, Active: 50-100% |
| Wikki app | ~200MB | Idle: 1%, Active: 5% |
| **Всего** | **~4.5GB** | **Зависит от нагрузки** |

### Скорость

- **Текстовый ответ:** 1-5 секунд
- **Транскрипция аудио:** 2-10 секунд
- **Анализ изображения:** 3-8 секунд

## 🔄 Миграция с Ollama

### Что изменилось

1. **URL:** `localhost:11434` → `127.0.0.1:8080`
2. **API:** `/api/chat` → `/v1/chat/completions`
3. **Запуск:** Автоматический → Ручной/UI

### Совместимость

Wikki поддерживает оба варианта:
- Ollama (по умолчанию)
- llama.cpp (через `.with_llama_cpp()`)

Текущая конфигурация: **llama.cpp**

Чтобы вернуться на Ollama:
```rust
// src-tauri/src/lib.rs
let ollama = services::ollama::OllamaClient::new(); // Без .with_llama_cpp()
```

## 📝 API Reference

### Tauri Commands

#### `start_llama_server`
```typescript
await invoke('start_llama_server', {
  exePath: 'C:\\path\\to\\llama-server.exe',
  modelPath: 'C:\\path\\to\\model.gguf'
});
```

#### `stop_llama_server`
```typescript
await invoke('stop_llama_server');
```

#### `get_llama_server_status`
```typescript
const status = await invoke<string>('get_llama_server_status');
// Returns: "running" | "stopped"
```

#### `check_llama_server_health`
```typescript
const isHealthy = await invoke<boolean>('check_llama_server_health');
```

#### `get_audio_info`
```typescript
const info = await invoke<{
  duration_secs: number;
  size_kb: number;
  exceeds_limit: boolean;
  max_duration_secs: number;
}>('get_audio_info', { audioBase64: '...' });
```

#### `transcribe_audio`
```typescript
const result = await invoke<{
  text: string;
  audio_info: AudioInfo;
  was_trimmed: boolean;
}>('transcribe_audio', {
  input: {
    audio_base64: '...',
    format: 'wav'
  },
  trimIfNeeded: true
});
```

## 🎓 Примеры

### Пример 1: Запуск сервера программно

```typescript
import { invoke } from '@tauri-apps/api/core';

async function startServer() {
  try {
    await invoke('start_llama_server', {
      exePath: 'C:\\llama.cpp\\build\\bin\\llama-server.exe',
      modelPath: 'C:\\llama.cpp\\models\\gemma-3n.gguf'
    });
    
    // Wait for server to start
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Check health
    const isHealthy = await invoke('check_llama_server_health');
    console.log('Server healthy:', isHealthy);
  } catch (error) {
    console.error('Failed to start server:', error);
  }
}
```

### Пример 2: Транскрипция с обработкой ошибок

```typescript
async function transcribeAudio(audioBase64: string) {
  try {
    // Check audio info first
    const info = await invoke('get_audio_info', { audioBase64 });
    
    if (info.exceeds_limit) {
      const shouldTrim = confirm(
        `Audio is ${info.duration_secs}s (max ${info.max_duration_secs}s). Trim?`
      );
      
      if (!shouldTrim) return;
    }
    
    // Transcribe
    const result = await invoke('transcribe_audio', {
      input: { audio_base64: audioBase64, format: 'wav' },
      trimIfNeeded: true
    });
    
    console.log('Transcribed:', result.text);
    if (result.was_trimmed) {
      console.warn('Audio was trimmed');
    }
  } catch (error) {
    console.error('Transcription failed:', error);
  }
}
```

## 🔮 Будущие улучшения

- [ ] Автоматический запуск сервера при старте Wikki
- [ ] Настройки llama-server через UI
- [ ] Поддержка нескольких моделей
- [ ] Streaming responses
- [ ] Batch processing для длинных аудио
- [ ] Кэширование транскрипций

---

**Версия:** 0.2.0  
**Дата:** 2026-02-01  
**Статус:** ✅ Работает
