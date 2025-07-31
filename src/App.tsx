import { useState, useRef, useEffect } from 'react';
import './App.css';
import WikkiImage from './images/wikki_shake_hand.png';
import { Settings, SendHorizonal, Move, Minus, History, ArrowLeft, PlusCircle, Edit, Trash2 } from 'lucide-react'; // Добавили Edit и Trash2
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
  title: string;
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
  const [editingChatId, setEditingChatId] = useState<string | null>(null); // Новое состояние для редактируемого чата
  const [newChatTitle, setNewChatTitle] = useState(''); // Новое состояние для нового названия чата
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // --- Функция для сохранения истории чатов в файл ---
  const saveHistory = async (chatsToSave: Chat[]) => {
    try {
      const dir = await appDataDir();
       const appSpecificDir = await join(dir, 'your_app_specific_subfolder_if_any'); // Например, если вы хотите подпапку
       if (!await exists(appSpecificDir)) {
         await mkdir(appSpecificDir, { recursive: true });
       }
      const filePath = await join(dir, HISTORY_FILE); // Путь к файлу в директории приложения
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
    // Сохраняем только если чаты не пустые и это не начальная загрузка
    if (chats.length > 0 || (chats.length === 0 && activeChatId === null)) { // Условие для сохранения пустого состояния, если все чаты удалены
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
    let historyForAgent: Message[] = [];

    // Оптимистичное обновление UI
    if (!currentChatId) {
        const newChatId = Date.now().toString();
        const newChat: Chat = {
            id: newChatId,
            title: promptToSend.substring(0, 40) + (promptToSend.length > 40 ? '...' : ''),
            messages: [userMessage], // Показываем пользователю его сообщение сразу
        };
        setChats(prevChats => [...prevChats, newChat]);
        setActiveChatId(newChatId);
        currentChatId = newChatId;
        // historyForAgent остается пустой для нового чата
    } else {
        // Находим историю ДО добавления нового сообщения
        historyForAgent = chats.find(c => c.id === currentChatId)!.messages;
        
        // Обновляем UI, чтобы пользователь сразу видел свое сообщение
        const updatedChats = chats.map(chat =>
            chat.id === currentChatId
                ? { ...chat, messages: [...chat.messages, userMessage] }
                : chat
        );
        setChats(updatedChats);
    }

    // --- Отправка данных на сервер ---
    const { history: authoritativeHistory } = await sendMessageToAgent(promptToSend, historyForAgent);

    // --- Обновление UI ответом от сервера ---
    setChats(prevChats =>
      prevChats.map(chat => {
          if (chat.id === currentChatId) {
              const modelMessage = authoritativeHistory[authoritativeHistory.length - 1];
              const updatedMessages = [...chat.messages, modelMessage];

              return { ...chat, messages: updatedMessages };
          }
          return chat;
      })
    );

    setIsLoading(false);
};

  const handleNewChat = () => {
    setActiveChatId(null);
    setIsSidebarOpen(false);
    setEditingChatId(null);
  }

  // --- Функции для редактирования и удаления чата ---
  const handleEditChatClick = (chat: Chat) => {
    setEditingChatId(chat.id);
    setNewChatTitle(chat.title); // Заполняем поле текущим названием
  };

  const handleRenameChat = () => {
    if (!newChatTitle.trim() || !editingChatId) return;

    setChats(prevChats =>
      prevChats.map(chat =>
        chat.id === editingChatId
          ? { ...chat, title: newChatTitle.trim() }
          : chat
      )
    );
    setEditingChatId(null); // Закрываем окно редактирования
    setNewChatTitle(''); // Очищаем поле
  };

  const handleDeleteChat = () => {
    if (!editingChatId) return;

    setChats(prevChats => prevChats.filter(chat => chat.id !== editingChatId));
    // Если удалили активный чат, сбрасываем активный чат
    if (activeChatId === editingChatId) {
      setActiveChatId(null);
    }
    setEditingChatId(null); // Закрываем окно редактирования
    setNewChatTitle(''); // Очищаем поле
  };

  const appWindow = getCurrentWindow();
  const activeChat = chats.find(chat => chat.id === activeChatId);

  if (showSettings) {
    return <SettingsPage onBack={() => setShowSettings(false)} />;
  }

  return (
    <div className="container">
      {/*--- Боковое меню --- */}
      <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="menu-button" onClick={() => setIsSidebarOpen(false)}>
          <ArrowLeft />
        </div>
        <h2 className="sidebar-title">History</h2>
        <ul className="chat-list">
          {chats.map(chat => (
            <li
              key={chat.id}
              className={`chat-item ${chat.id === activeChatId ? 'active' : ''}`}
            >
              <span
                onClick={() => {
                  setActiveChatId(chat.id);
                  setIsSidebarOpen(false);
                  setEditingChatId(null); // Закрываем редактирование, если переключаемся на другой чат
                }}
                className="chat-title-text" // класс для стилизации текста
              >
                {chat.title}
              </span>
              <button
                className="edit-chat-button"
                onClick={(e) => {
                  e.stopPropagation(); // Предотвращаем срабатывание onClick родительского li
                  handleEditChatClick(chat);
                }}
              >
                <Edit size={16} />
              </button>
            </li>
          ))}
        </ul>
        <button className="new-chat-button" onClick={handleNewChat}>
          <PlusCircle size={18} /> New Chat
        </button>
      </div>

      {/* --- Модальное окно редактирования чата --- */}
      {editingChatId && (
        <div className="edit-chat-modal-overlay" onClick={() => setEditingChatId(null)}>
          <div className="edit-chat-modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Chat</h3>
            <input
              type="text"
              value={newChatTitle}
              onChange={(e) => setNewChatTitle(e.target.value)}
              placeholder="New chat title"
              className="edit-title-input"
            />
            <div className="modal-actions">
              <button className="rename-button" onClick={handleRenameChat}>Rename</button>
              <button className="delete-button" onClick={handleDeleteChat}>
                <Trash2 size={16} /> Delete
              </button>
              <button className="cancel-button" onClick={() => setEditingChatId(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}


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