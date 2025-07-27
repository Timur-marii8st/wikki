import { useState } from 'react';
import { ArrowLeft, LogOut } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';

// Определяем тип для пропсов, чтобы передать функцию возврата назад
type SettingsPageProps = {
  onBack: () => void;
};

function SettingsPage({ onBack }: SettingsPageProps) {
  // Состояния для элементов управления
  const [isBrowserAllowed, setIsBrowserAllowed] = useState(false);
  const [isOsAllowed, setIsOsAllowed] =useState(true);
  const [isDarkMode, setIsDarkMode] = useState(true);

  const handleLogout = () => {
    invoke("end_app")
  };

  return (
    <div className="container settings-container">
      {/* --- Шапка с кнопкой "Назад" и заголовком --- */}
      <div className="settings-header">
        <button className="back-button" onClick={onBack}>
          <ArrowLeft size={24} />
        </button>
        <h2>Settings</h2>
      </div>

      {/* --- Основной блок с опциями --- */}
      <div className="settings-options">
        {/* Опция 1: Доступ к OS */}
        <div className="settings-option">
          <label htmlFor="os-access">OS Access</label>
          <input
            id="os-access"
            type="checkbox"
            checked={isOsAllowed}
            onChange={() => setIsOsAllowed(!isOsAllowed)}
          />
        </div>

        {/* Опция 2: Доступ к браузеру */}
        <div className="settings-option">
          <label htmlFor="browser-access">Browser Access</label>
          <input
            id="browser-access"
            type="checkbox"
            checked={isBrowserAllowed}
            onChange={() => setIsBrowserAllowed(!isBrowserAllowed)}
          />
        </div>

        {/* Опция 3: Переключатель темы */}
        <div className="settings-option">
          <label htmlFor="theme-toggle">Theme: {isDarkMode ? 'White' : 'Dark'}</label>
          <label className="switch">
            <input
              id="theme-toggle"
              type="checkbox"
              checked={isDarkMode}
              onChange={() => setIsDarkMode(!isDarkMode)}
            />
            <span className="slider round"></span>
          </label>
        </div>
      </div>

      {/* --- Кнопка выхода в самом низу --- */}
      <div className="settings-footer">
        <button className="logout-button" onClick={handleLogout}>
          <LogOut size={18} />
          <span>Shut down App</span>
        </button>
      </div>
    </div>
  );
}

export default SettingsPage;
