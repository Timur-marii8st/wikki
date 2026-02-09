import { useState, useEffect } from 'react';
import { listen } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { Avatar3D } from './components/Avatar3D/Avatar3D';
import { Menu, X } from 'lucide-react';
import './styles/avatar.css';

export function AvatarApp() {
  const [emotion, setEmotion] = useState('neutral');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  useEffect(() => {
    // Listen for emotion updates from main window
    const unlistenEmotion = listen<string>('set-emotion', (event) => {
      setEmotion(event.payload);
    });

    const unlistenSpeaking = listen<boolean>('set-speaking', (event) => {
      setIsSpeaking(event.payload);
    });

    // Setup drag region
    const dragRegion = document.getElementById('avatar-drag-region');
    if (dragRegion) {
      const handleMouseDown = (e: MouseEvent) => {
        if (e.button === 0) { // Left mouse button
          e.preventDefault();
          console.log('Starting drag...');
          getCurrentWindow().startDragging().catch(err => {
            console.error('Failed to start dragging:', err);
          });
        }
      };
      
      dragRegion.addEventListener('mousedown', handleMouseDown);
      
      return () => {
        unlistenEmotion.then(fn => fn());
        unlistenSpeaking.then(fn => fn());
        dragRegion.removeEventListener('mousedown', handleMouseDown);
      };
    }

    return () => {
      unlistenEmotion.then(fn => fn());
      unlistenSpeaking.then(fn => fn());
    };
  }, []);

  const handleShowChat = async () => {
    try {
      await invoke('show_chat_window');
      const avatarWindow = getCurrentWindow();
      await avatarWindow.hide();
      setShowMenu(false);
    } catch (error) {
      console.error('Failed to show chat:', error);
    }
  };

  const handleHideAvatar = async () => {
    try {
      await invoke('toggle_avatar', { visible: false });
      setShowMenu(false);
    } catch (error) {
      console.error('Failed to hide avatar:', error);
    }
  };

  return (
    <div className="avatar-wrapper">
      <div id="avatar-drag-region" className="avatar-drag-region" />
      <div className="avatar-container">
        <Avatar3D emotion={emotion} isSpeaking={isSpeaking} />
      </div>
      
      <button 
        className="avatar-menu-button"
        onClick={(e) => {
          e.stopPropagation();
          setShowMenu(!showMenu);
        }}
      >
        {showMenu ? <X size={18} /> : <Menu size={18} />}
      </button>
      
      {showMenu && (
        <div className="avatar-menu">
          <button onClick={handleShowChat}>Open Chat</button>
          <button onClick={handleHideAvatar}>Hide Avatar</button>
        </div>
      )}
    </div>
  );
}
