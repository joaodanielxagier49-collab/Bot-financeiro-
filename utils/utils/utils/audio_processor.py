import speech_recognition as sr
import io
from pydub import AudioSegment
import tempfile
import os

class AudioProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def convert_audio_format(self, audio_data):
        """Converte áudio para formato WAV se necessário"""
        try:
            # Tentar carregar como MP3
            audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
        except:
            try:
                # Tentar carregar como OGG
                audio = AudioSegment.from_ogg(io.BytesIO(audio_data))
            except:
                # Assumir que já está em WAV
                return audio_data
        
        # Converter para WAV
        wav_io = io.BytesIO()
        audio.export(wav_io, format='wav')
        return wav_io.getvalue()
    
    def speech_to_text(self, audio_data):
        """Converte áudio para texto"""
        try:
            # Converter formato se necessário
            wav_data = self.convert_audio_format(audio_data)
            
            # Usar arquivo temporário
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(wav_data)
                temp_file.flush()
                
                # Reconhecer speech
                with sr.AudioFile(temp_file.name) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio, language='pt-BR')
                
                # Limpar arquivo temporário
                os.unlink(temp_file.name)
                
                return text
        
        except Exception as e:
            print(f"Erro no processamento de áudio: {e}")
            return ""
