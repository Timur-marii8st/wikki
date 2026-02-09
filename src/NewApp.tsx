import { useEffect, useRef, useState } from 'react';
import { listen } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';
import { useAppStore } from './stores/appStore';
import { Send, Mic, MicOff, Move, Minimize, Play, Square, AlertCircle } from 'lucide-react';
import './App.css';

function App() {
  const {
    messages,
    isLoading,
    isRecording,
    audioInfo,
    serverStatus,
    serverError,
    sendMessage,
    transcribeAndSend,
    setRecording,
    setAudioInfo,
    checkServerStatus,
    startServer,
    stopServer,
  } = useAppStore();

  const [inputValue, setInputValue] = useState('');
  const [showServerPanel, setShowServerPanel] = useState(false);
  const [serverPaths, setServerPaths] = useState({
    exe: 'C:\\Users\\elkgo\\llama.cpp\\build\\bin\\llama-server.exe',
    model: 'C:\\Users\\elkgo\\llama.cpp\\models\\gemma-3n-E4B-it-absolute-heresy-MPOA-iQ4_NL.gguf',
  });
  
  const chatRef = useRef<HTMLDivElement>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  // Auto-scroll
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  // Check server status on mount
  useEffect(() => {
    checkServerStatus();
    const interval = setInterval(checkServerStatus, 5000);
    return () => clearInterval(interval);
  }, [checkServerStatus]);

  // Voice input hotkey listener
  useEffect(() => {
    const unlistenVoice = listen('voice-input-toggle', () => {
      if (isRecording) {
        stopRecording();
      } else {
        startRecording();
      }
    });

    // Screenshot request listener
    const unlistenScreenshot = listen<{ prompt: string }>('screenshot-request', async (event) => {
      try {
        const image = await invoke<string>('capture_screen');
        await sendMessage(event.payload.prompt, image);
      } catch (e) {
        console.error('Screenshot failed:', e);
      }
    });

    return () => {
      unlistenVoice.then(fn => fn());
      unlistenScreenshot.then(fn => fn());
    };
  }, [isRecording, sendMessage]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      });
      
      mediaRecorder.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
      });
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (e) => {
        audioChunks.current.push(e.data);
      };

      mediaRecorder.current.onstop = async () => {
        const blob = new Blob(audioChunks.current, { type: 'audio/webm' });
        const arrayBuffer = await blob.arrayBuffer();
        const base64 = btoa(
          new Uint8Array(arrayBuffer).reduce((data, byte) =>
            data + String.fromCharCode(byte), ''
          )
        );

        // Get audio info
        try {
          const info = await invoke<{
            duration_secs: number;
            size_kb: number;
            exceeds_limit: boolean;
            max_duration_secs: number;
          }>('get_audio_info', { audioBase64: base64 });
          
          setAudioInfo(info);

          if (info.exceeds_limit) {
            const shouldTrim = window.confirm(
              `Audio duration (${info.duration_secs.toFixed(1)}s) exceeds maximum (${info.max_duration_secs}s).\n\n` +
              `Do you want to trim it to ${info.max_duration_secs}s and send?`
            );
            
            if (shouldTrim) {
              await transcribeAndSend(base64, true);
            }
          } else {
            await transcribeAndSend(base64, false);
          }
        } catch (e) {
          console.error('Audio processing failed:', e);
        }

        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.current.start();
      setRecording(true);
    } catch (e) {
      console.error('Failed to start recording:', e);
      alert('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setRecording(false);
    }
  };

  const handleSend = () => {
    if (!inputValue.trim() || isLoading) return;
    sendMessage(inputValue);
    setInputValue('');
  };

  const handleMinimize = async () => {
    await invoke('hide_chat_window');
  };

  const handleStartServer = async () => {
    await startServer(serverPaths.exe, serverPaths.model);
  };

  const handleStopServer = async () => {
    await stopServer();
  };

  const getServerStatusColor = () => {
    switch (serverStatus) {
      case 'running': return '#4ade80';
      case 'stopped': return '#ef4444';
      case 'starting': return '#fbbf24';
      case 'stopping': return '#fbbf24';
      default: return '#6b7280';
    }
  };

  return (
    <div className="container">
      <div className="titlebar" data-tauri-drag-region>
        <Move size={18} />
        <span className="title">Wikki</span>
        <button 
          className="server-status-btn" 
          onClick={() => setShowServerPanel(!showServerPanel)}
          style={{ color: getServerStatusColor() }}
          title={`Server: ${serverStatus}`}
        >
          <div className="status-dot" style={{ backgroundColor: getServerStatusColor() }} />
        </button>
        <button className="minimize-btn" onClick={handleMinimize}>
          <Minimize size={16} />
        </button>
      </div>

      {showServerPanel && (
        <div className="server-panel">
          <h3>Llama Server</h3>
          <div className="server-status">
            Status: <span style={{ color: getServerStatusColor() }}>{serverStatus}</span>
          </div>
          {serverError && (
            <div className="server-error">
              <AlertCircle size={16} />
              {serverError}
            </div>
          )}
          <div className="server-paths">
            <label>
              Executable:
              <input
                type="text"
                value={serverPaths.exe}
                onChange={(e) => setServerPaths({ ...serverPaths, exe: e.target.value })}
                disabled={serverStatus === 'running'}
              />
            </label>
            <label>
              Model:
              <input
                type="text"
                value={serverPaths.model}
                onChange={(e) => setServerPaths({ ...serverPaths, model: e.target.value })}
                disabled={serverStatus === 'running'}
              />
            </label>
          </div>
          <div className="server-actions">
            {serverStatus === 'running' ? (
              <button onClick={handleStopServer} className="btn-danger">
                <Square size={16} /> Stop Server
              </button>
            ) : (
              <button onClick={handleStartServer} className="btn-primary" disabled={serverStatus === 'starting'}>
                <Play size={16} /> {serverStatus === 'starting' ? 'Starting...' : 'Start Server'}
              </button>
            )}
          </div>
        </div>
      )}

      <div className="chat-window" ref={chatRef}>
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>Hi! I'm Wikki, your desktop companion! 💕</p>
            <p>Press <kbd>Ctrl+Shift+V</kbd> to talk to me!</p>
            {serverStatus !== 'running' && (
              <p className="warning">
                ⚠️ Llama server is not running. Click the status dot to start it.
              </p>
            )}
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-content">{msg.content}</div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message assistant">
            <div className="message-content typing">...</div>
          </div>
        )}
      </div>

      <div className="input-area">
        <button
          className={`voice-btn ${isRecording ? 'recording' : ''}`}
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          title="Hold to record (or Ctrl+Shift+V)"
          disabled={serverStatus !== 'running'}
        >
          {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
        </button>

        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message..."
          disabled={isLoading || serverStatus !== 'running'}
        />

        <button 
          className="send-btn" 
          onClick={handleSend} 
          disabled={isLoading || serverStatus !== 'running'}
        >
          <Send size={20} />
        </button>
      </div>

      {audioInfo && audioInfo.exceeds_limit && (
        <div className="audio-warning">
          ⚠️ Audio: {audioInfo.duration_secs.toFixed(1)}s (max: {audioInfo.max_duration_secs}s)
        </div>
      )}
    </div>
  );
}

export default App;
