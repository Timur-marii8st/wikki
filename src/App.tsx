import { useState, useRef, useEffect } from 'react';
import './App.css';
import WikkiImage from './images/wikki_shake_hand.png';
import { Settings, SendHorizonal, Move, Minus, History, ArrowLeft, PlusCircle } from 'lucide-react';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { invoke } from '@tauri-apps/api/core';
import { readTextFile, writeTextFile, mkdir, exists } from '@tauri-apps/plugin-fs';
import { appDataDir } from '@tauri-apps/api/path';
import { join } from '@tauri-apps/api/path';
import SettingsPage from './SettingsPage.tsx';

// --- Типы данных ---
type Message = {
  role: string;
  content: string;
};

type Chat = {
  id: string;
  title:string;
  messages: Message[];
};

// --- Имя файла для сохранения истории ---
const HISTORY_FILE = 'chat_history.json';


function App() {
  // --- Состояния ---
  const [inputValue, setInputValue] = useState('');
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // --- Функция для сохранения истории чатов в файл ---
  const saveHistory = async (chatsToSave: Chat[]) => {
    try {
      const dir = await appDataDir();
      if (!await exists(dir)) {
        await mkdir(dir, { recursive: true });
      }
      const filePath = await join(dir, HISTORY_FILE);
      await writeTextFile(filePath, JSON.stringify(chatsToSave, null, 2));
    } catch (error) {
      console.error('Failed to save chat history:', error);
    }
  };

  // --- Загрузка истории чатов при первом рендере ---
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const dir = await appDataDir();
        const filePath = await join(dir, HISTORY_FILE);
        if (await exists(filePath)) {
          const content = await readTextFile(filePath);
          const loadedChats = JSON.parse(content) as Chat[];
          setChats(loadedChats);
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
        setChats([]); // В случае ошибки начинаем с чистого листа
      }
    };
    loadHistory();
  }, []);

  // --- Автоматическое сохранение при изменении чатов ---
  useEffect(() => {
    if (chats.length > 0) { // Не сохраняем пустое начальное состояние
      saveHistory(chats);
    }
  }, [chats]);


  // --- Прокрутка чата вниз при новом сообщении ---
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [activeChatId, chats]); // Перезапускаем при смене чата или сообщений


  // --- Функция для общения с FastAPI ---
  async function sendMessageToAgent(prompt: string, history: Message[]): Promise<{ response: string, history: Message[] }> {
    try {
      const res = await fetch('http://127.0.0.1:5000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, history }),
      });
      if (!res.ok) throw new Error('Ошибка соединения с сервером');
      return await res.json();
    } catch (e: any) {
      return { response: 'Ошибка соединения с сервером: ' + e.message, history };
    }
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: inputValue };
    const promptToSend = inputValue;
    setInputValue('');
    setIsLoading(true);

    let currentChatId = activeChatId;
    let historyForAgent: Message[];

    // Если нет активного чата - создаем новый
    if (!currentChatId) {
      const newChatId = Date.now().toString();
      const newChat: Chat = {
        id: newChatId,
        title: promptToSend.substring(0, 40) + (promptToSend.length > 40 ? '...' : ''), // Заголовок из первого сообщения
        messages: [userMessage],
      };
      setChats(prevChats => [...prevChats, newChat]);
      setActiveChatId(newChatId);
      currentChatId = newChatId;
      historyForAgent = newChat.messages;
    } else {
      // Иначе добавляем сообщение в существующий чат
      const updatedChats = chats.map(chat =>
        chat.id === currentChatId
          ? { ...chat, messages: [...chat.messages, userMessage] }
          : chat
      );
      setChats(updatedChats);
      historyForAgent = updatedChats.find(c => c.id === currentChatId)!.messages;
    }
    
    // Отправляем на сервер актуальную историю
    const { history: updatedHistory } = await sendMessageToAgent(promptToSend, historyForAgent);

    // Обновляем чат авторитетным состоянием от сервера
    setChats(prevChats =>
      prevChats.map(chat =>
        chat.id === currentChatId
          ? { ...chat, messages: updatedHistory }
          : chat
      )
    );

    setIsLoading(false);
  };
  
  const handleNewChat = () => {
    setActiveChatId(null);
    setIsSidebarOpen(false); // Закрываем боковое меню при создании нового чата
  }

  const appWindow = getCurrentWindow();
  const activeChat = chats.find(chat => chat.id === activeChatId);

  if (showSettings) {
    return <SettingsPage onBack={() => setShowSettings(false)} />;
  }

  return (
    <div className="container">
      {/*--- Боковое меню --- */}
      <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className='menu-button' onClick={() => setIsSidebarOpen(false)}>
          <ArrowLeft />
        </div>
        <h2 className="sidebar-title">History</h2>
        <ul className="chat-list">
          {chats.map(chat => (
             <li 
               key={chat.id} 
               className={`chat-item ${chat.id === activeChatId ? 'active' : ''}`}
               onClick={() => {
                 setActiveChatId(chat.id);
                 setIsSidebarOpen(false);
               }}
             >
               {chat.title}
             </li>
          ))}
        </ul>
        <button className="new-chat-button" onClick={handleNewChat}>
          <PlusCircle size={18} /> New Chat
        </button>
      </div>

      <div className="titlebar" data-tauri-drag-region>
        <Move size={22} />
      </div>
      <div className="controls">
        <button onClick={() => { appWindow.hide(); invoke('show_assistant_window') }}><Minus size={20} /></button>
      </div>

      <button className="menu-button" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
        <History />
      </button>

      <button className="settings-button" onClick={() => setShowSettings(true)}>
        <Settings />
      </button>

      {!activeChat ? (
        <div className="greeting-section">
          <img src={WikkiImage} alt="Wikki" className="wikki-image" />
          <p className="wikki-text">Hi, I'm Wikki!
            We can talk or ask me to do something on your device</p>
        </div>
      ) : (
        <div className="chat-window" ref={chatContainerRef}>
          {activeChat.messages
            .filter(msg => msg.role !== 'system')
            .map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-content">{msg.content}</div>
              </div>
            ))}
          {isLoading && (
            <div className="message model">
              <div className="message-content typing-indicator">...</div>
            </div>
          )}
        </div>
      )}

      <div className="input-area">
        <input
          type="text"
          className="input-field"
          placeholder="Ask me something..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !isLoading) {
              handleSend();
            }
          }}
          disabled={isLoading}
        />
        <button className="send-button" onClick={handleSend} disabled={isLoading}>
          <SendHorizonal size={25} />
        </button>
      </div>
    </div>
  );
}

export default App;