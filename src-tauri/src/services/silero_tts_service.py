#!/usr/bin/env python3
"""
Silero TTS Service - Long-running process for text-to-speech
Communicates via stdin/stdout using JSON protocol
"""

import sys
import json
import torch
import torchaudio
import io
import base64
import os
from pathlib import Path

class SileroTTSService:
    def __init__(self):
        self.device = torch.device('cpu')
        self.models = {}
        self.sample_rate = 48000
        
        # Default speakers
        self.speakers = {
            'ru': 'baya',  # Female voice
            'en': 'lj_16khz'
        }
        
        self.current_language = None
        self.log("Silero TTS Service initialized")
    
    def log(self, message):
        """Log to stderr (stdout is for JSON responses)"""
        print(f"[TTS] {message}", file=sys.stderr, flush=True)
    
    def load_model(self, language):
        """Load TTS model for specified language"""
        if language in self.models:
            self.log(f"Model for {language} already loaded")
            return
        
        self.log(f"Loading model for {language}...")
        
        try:
            if language == 'ru':
                model, _ = torch.hub.load(
                    repo_or_dir='snakers4/silero-models',
                    model='silero_tts',
                    language='ru',
                    speaker='v5_ru',
                    force_reload=False
                )
            elif language == 'en':
                model, example_text = torch.hub.load(
                    repo_or_dir='snakers4/silero-models',
                    model='silero_tts',
                    language='en',
                    speaker='v3_en',
                    force_reload=False
                )
            else:
                raise ValueError(f"Unsupported language: {language}")
            
            model.to(self.device)
            self.models[language] = model
            self.current_language = language
            
            self.log(f"Model for {language} loaded successfully")
        except Exception as e:
            self.log(f"Error loading model: {e}")
            raise
    
    def apply_ssml_emotion(self, text, emotion):
        """Apply SSML tags based on emotion if text doesn't have them"""
        # Check if text already has SSML
        if '<speak>' in text or '<prosody>' in text:
            return text
        
        # Map emotions to SSML parameters
        emotion_map = {
            'happy': {'pitch': 'high', 'rate': 'fast'},
            'excited': {'pitch': 'x-high', 'rate': 'fast'},
            'sad': {'pitch': 'low', 'rate': 'slow'},
            'thinking': {'pitch': 'medium', 'rate': 'slow'},
            'surprised': {'pitch': 'high', 'rate': 'medium'},
            'neutral': {'pitch': 'medium', 'rate': 'medium'}
        }
        
        params = emotion_map.get(emotion, emotion_map['neutral'])
        
        # Wrap text in SSML with emotion-based prosody
        ssml = f"""<speak>
<prosody pitch="{params['pitch']}" rate="{params['rate']}">
{text}
</prosody>
</speak>"""
        
        return ssml
    
    def synthesize(self, text, language, emotion='neutral', use_ssml=True):
        """Synthesize speech from text"""
        try:
            # Load model if needed
            if language not in self.models:
                self.load_model(language)
            
            model = self.models[language]
            speaker = self.speakers[language]
            
            # Apply emotion-based SSML if enabled
            if use_ssml and language == 'ru':
                text = self.apply_ssml_emotion(text, emotion)
            
            # Generate audio
            if language == 'ru':
                # Russian model supports SSML
                if '<speak>' in text:
                    audio = model.apply_tts(
                        ssml_text=text,
                        speaker=speaker,
                        sample_rate=self.sample_rate
                    )
                else:
                    audio = model.apply_tts(
                        text=text,
                        speaker=speaker,
                        sample_rate=self.sample_rate,
                        put_accent=True,
                        put_yo=True
                    )
            elif language == 'en':
                # English model
                
                audio = model.apply_tts(
                    text=text,
                    speaker=model,
                    sample_rate=self.sample_rate
                )
            
            # Convert to WAV bytes
            buffer = io.BytesIO()
            torchaudio.save(buffer, audio.unsqueeze(0), self.sample_rate, format='wav')
            wav_bytes = buffer.getvalue()
            
            # Encode to base64
            audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
            
            return {
                'success': True,
                'audio_base64': audio_base64,
                'sample_rate': self.sample_rate,
                'duration': len(audio) / self.sample_rate
            }
            
        except Exception as e:
            self.log(f"Error synthesizing: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_request(self, request):
        """Handle incoming JSON request"""
        try:
            command = request.get('command')
            
            if command == 'synthesize':
                text = request.get('text', '')
                language = request.get('language', 'en')
                emotion = request.get('emotion', 'neutral')
                use_ssml = request.get('use_ssml', True)
                
                return self.synthesize(text, language, emotion, use_ssml)
            
            elif command == 'load_model':
                language = request.get('language', 'en')
                self.load_model(language)
                return {'success': True, 'message': f'Model {language} loaded'}
            
            elif command == 'ping':
                return {'success': True, 'message': 'pong'}
            
            elif command == 'shutdown':
                return {'success': True, 'message': 'shutting down'}
            
            else:
                return {'success': False, 'error': f'Unknown command: {command}'}
                
        except Exception as e:
            self.log(f"Error handling request: {e}")
            return {'success': False, 'error': str(e)}
    
    def run(self):
        """Main loop - read JSON from stdin, write JSON to stdout"""
        self.log("Service started, waiting for commands...")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    
                    # Write response to stdout
                    print(json.dumps(response), flush=True)
                    
                    # Check for shutdown
                    if request.get('command') == 'shutdown':
                        self.log("Shutdown requested")
                        break
                        
                except json.JSONDecodeError as e:
                    self.log(f"Invalid JSON: {e}")
                    error_response = {'success': False, 'error': 'Invalid JSON'}
                    print(json.dumps(error_response), flush=True)
                    
        except KeyboardInterrupt:
            self.log("Interrupted")
        except Exception as e:
            self.log(f"Fatal error: {e}")
        finally:
            self.log("Service stopped")

if __name__ == '__main__':
    service = SileroTTSService()
    service.run()