import { useState } from 'react';
import './App.css';
import WikkiImage from './images/wikki_shake_hand.png';
import { Settings, Send, Move, Minus } from 'lucide-react';
import { getCurrentWindow } from '@tauri-apps/api/window';

function App() {
  const [inputValue, setInputValue] = useState('');

  const handleSend = () => {
    console.log('Отправлено:', inputValue);
    // Здесь будет логика отправки запроса AI-агенту
    setInputValue(''); // Очистить поле ввода после отправки
  };

  const appWindow = getCurrentWindow();

  const handleSettingsClick = () => {
    // В реальном приложении здесь будет навигация на страницу настроек
    // Например, с использованием React Router: navigate('/settings');
    console.log('Переход на страницу настроек');
    alert('Будет страница настроек!'); // Временное уведомление
  };

  return (    
    <div className="container">
      <div className="titlebar">
        <Move size={22}/>
      </div>
      <div className="controls">
        <button onClick={() => appWindow.hide()}><Minus size={20}/></button>
      </div>

      {/* Кнопка настроек */}
      <button className="settings-button" onClick={handleSettingsClick}>
        <Settings /> {/* Иконка шестеренки */}
      </button>

      {/* Центральный блок приветствия */}
      <div className="greeting-section">
        <img src={WikkiImage} alt="Wikki" className="wikki-image" />
        <p className="wikki-text">Hi, I'm Wikki!
          We can talk or ask me to do something on your device</p>
      </div>

      {/* Нижняя строка ввода и кнопка отправки */}
      <div className="input-area">
        <input
          type="text"
          className="input-field"
          placeholder="Ask me something..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleSend();
            }
          }}
        />
        <button className="send-button" onClick={handleSend}>
          <Send size={25}/>
        </button>
      </div>
    </div>
  );
}

export default App;