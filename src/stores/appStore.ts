import { create } from 'zustand';
import { invoke } from '@tauri-apps/api/core';
import { emit } from '@tauri-apps/api/event';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface OllamaMessage {
  role: string;
  content: string;
  images?: string[];
}

interface AudioInfo {
  duration_secs: number;
  size_kb: number;
  exceeds_limit: boolean;
  max_duration_secs: number;
}

interface AppState {
  // Chat
  messages: Message[];
  history: OllamaMessage[];
  isLoading: boolean;

  // Avatar
  emotion: string;
  isSpeaking: boolean;

  // Voice
  isRecording: boolean;
  audioInfo: AudioInfo | null;

  // Llama Server
  serverStatus: 'unknown' | 'running' | 'stopped' | 'starting' | 'stopping';
  serverError: string | null;

  // Actions
  sendMessage: (text: string, image?: string) => Promise<void>;
  transcribeAndSend: (audioBase64: string, trimIfNeeded: boolean) => Promise<void>;
  setRecording: (recording: boolean) => void;
  setAudioInfo: (info: AudioInfo | null) => void;
  clearChat: () => void;
  
  // Server actions
  checkServerStatus: () => Promise<void>;
  startServer: (exePath: string, modelPath: string) => Promise<void>;
  stopServer: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  messages: [],
  history: [],
  isLoading: false,
  emotion: 'neutral',
  isSpeaking: false,
  isRecording: false,
  audioInfo: null,
  serverStatus: 'unknown',
  serverError: null,

  sendMessage: async (text: string, image?: string) => {
    const { history, messages } = get();

    // Add user message immediately
    set({
      messages: [...messages, { role: 'user', content: text }],
      isLoading: true,
    });

    try {
      const result = await invoke<{
        response: string;
        emotion: string;
        updated_history: OllamaMessage[];
      }>('send_message', {
        input: {
          message: text,
          history,
          image,
        },
      });

      // Update state
      set({
        messages: [...get().messages, { role: 'assistant', content: result.response }],
        history: result.updated_history,
        emotion: result.emotion,
        isLoading: false,
      });

      // Emit to avatar window
      await emit('set-emotion', result.emotion);

      // Speak response
      set({ isSpeaking: true });
      await emit('set-speaking', true);

      await invoke('synthesize_speech', { 
        text: result.response,
        emotion: result.emotion 
      });

      set({ isSpeaking: false });
      await emit('set-speaking', false);

    } catch (error) {
      console.error('Chat error:', error);
      set({ 
        messages: [...get().messages, { 
          role: 'assistant', 
          content: 'Sorry, I encountered an error. Is the llama server running?' 
        }],
        isLoading: false 
      });
    }
  },

  transcribeAndSend: async (audioBase64: string, trimIfNeeded: boolean) => {
    set({ isLoading: true });

    try {
      const result = await invoke<{
        text: string;
        audio_info: AudioInfo;
        was_trimmed: boolean;
      }>('transcribe_audio', {
        input: {
          audio_base64: audioBase64,
          format: 'wav',
        },
        trimIfNeeded,
      });

      if (result.was_trimmed) {
        console.warn('Audio was trimmed to 15 seconds');
      }

      // Send transcribed text
      await get().sendMessage(result.text);

    } catch (error) {
      console.error('Transcription error:', error);
      set({ 
        messages: [...get().messages, { 
          role: 'assistant', 
          content: `Transcription failed: ${error}` 
        }],
        isLoading: false 
      });
    }
  },

  setRecording: (recording: boolean) => set({ isRecording: recording }),

  setAudioInfo: (info: AudioInfo | null) => set({ audioInfo: info }),

  clearChat: () => set({ messages: [], history: [] }),

  checkServerStatus: async () => {
    try {
      const isHealthy = await invoke<boolean>('check_llama_server_health');
      set({ 
        serverStatus: isHealthy ? 'running' : 'stopped',
        serverError: null 
      });
    } catch (error) {
      set({ 
        serverStatus: 'stopped',
        serverError: null 
      });
    }
  },

  startServer: async (exePath: string, modelPath: string) => {
    set({ serverStatus: 'starting', serverError: null });
    
    try {
      await invoke('start_llama_server', { exePath, modelPath });
      
      // Wait a bit for server to start
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      await get().checkServerStatus();
    } catch (error) {
      set({ 
        serverStatus: 'stopped',
        serverError: `Failed to start server: ${error}` 
      });
    }
  },

  stopServer: async () => {
    set({ serverStatus: 'stopping' });
    
    try {
      await invoke('stop_llama_server');
      set({ serverStatus: 'stopped', serverError: null });
    } catch (error) {
      set({ 
        serverError: `Failed to stop server: ${error}` 
      });
      await get().checkServerStatus();
    }
  },
}));
