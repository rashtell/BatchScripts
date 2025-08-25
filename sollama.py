#!/usr/bin/env python3
"""
Ollama TTS Assistant - Python Version with Memory
Direct API calls to ollama server with text-to-speech and conversation memory

INSTALLATION REQUIREMENTS:
1. Ollama (AI model server)
2. Python TTS library (pyttsx3 or pywin32)

OLLAMA INSTALLATION:

Windows:
  1. Download from: https://ollama.ai/download/windows
  2. Run the installer (OllamaSetup.exe)
  3. Ollama will start automatically
  4. Open Command Prompt and run: ollama pull llama3.2
  
macOS:
  1. Download from: https://ollama.ai/download/mac
  2. Drag Ollama.app to Applications folder
  3. Run Ollama from Applications
  4. Open Terminal and run: ollama pull llama3.2
  
Linux:
  1. Run: curl -fsSL https://ollama.ai/install.sh | sh
  2. Start service: sudo systemctl start ollama
  3. Pull model: ollama pull llama3.2

PYTHON TTS INSTALLATION:
  Windows: pip install pyttsx3
  Linux/Mac: pip install pyttsx3

VERIFY INSTALLATION:
  1. Check Ollama: ollama --version
  2. Test model: ollama run llama3.2
  3. Check server: curl http://localhost:11434/api/tags

TROUBLESHOOTING:
  - If "connection refused": Run 'ollama serve' manually
  - If no TTS: Install with 'pip install pyttsx3'
  - If slow responses: Try smaller model like 'llama3.2:1b'

COMMAND LINE USAGE:

Basic Usage:
  python ollama_tts.py

Common Options:
  python ollama_tts.py --model llama3.2:1b --volume 0.5
  python ollama_tts.py --mute --system-prompt "You are a coding expert"
  python ollama_tts.py --load-memory my_session.json

All Command Line Arguments:
  -m, --model MODEL           Ollama model (default: llama3.2)
  -u, --url URL              Server URL (default: http://localhost:11434)
  -r, --rate RATE            Speech rate 50-300 (default: 175)
  -v, --volume VOLUME        Volume 0.0-1.0 (default: 1.0)
  --mute                     Start with audio muted
  -s, --save                 Save conversation to timestamped file
  -sp, --system-prompt TEXT  Custom system prompt for assistant
  -mm, --max-memory NUM      Max conversation exchanges (default: 50)
  -lm, --load-memory FILE    Load previous conversation memory

Examples:
  python ollama_tts.py --volume 0.3 --rate 200
  python ollama_tts.py --mute --model mistral
  python ollama_tts.py --system-prompt "You are a creative writing coach"
  python ollama_tts.py --load-memory conversation_20240825.json

NEW FEATURES:
  - Conversation memory: Assistant remembers previous exchanges
  - System prompts: Configure assistant personality/behavior  
  - Memory management: Clear, save, and load conversation history
  - Enhanced audio: Mute, precise volume control, command line audio settings
  - Enhanced context: Better multi-turn conversations

INTERACTIVE COMMANDS:
  exit/quit/bye         - Exit the program
  clear/new/reset       - Clear conversation memory
  memory                - Show memory status
  system <prompt>       - Set system prompt
  save_memory [file]    - Save conversation memory
  load_memory <file>    - Load conversation memory
  models                - List available models
  model <name>          - Switch to different model
  repeat                - Repeat last response
  test_tts              - Test TTS functionality
  voice                 - List available voices
  voice <number>        - Switch to voice number
  faster/slower         - Adjust speech speed
  louder/quieter        - Adjust volume by 0.1
  volume <0.0-1.0>      - Set specific volume level
  mute/unmute           - Mute or unmute audio
  stream                - Toggle streaming mode on/off
  live_tts              - Toggle live TTS during streaming
  help                  - Show interactive help
  <question>            - Ask ollama a question
"""

import requests
import json
import argparse
import sys
import time
import threading
import queue
import re
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Try to import TTS libraries
TTS_ENGINE = None
try:
    import pyttsx3
    TTS_ENGINE = "pyttsx3"
except ImportError:
    try:
        import win32com.client
        TTS_ENGINE = "sapi"
    except ImportError:
        print("No TTS library found. Install with: pip install pyttsx3")
        print("Or on Windows: pip install pywin32")

class ConversationMemory:
    """Manages conversation history and system prompts"""
    
    def __init__(self, system_prompt: str = None, max_history: int = 50):
        self.system_prompt = system_prompt or self.get_default_system_prompt()
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = max_history
        self.memory_file = None
        self.conversation_start_time = datetime.now()
    
    @staticmethod
    def get_default_system_prompt() -> str:
        """Default system prompt for the assistant"""
        return """You are a helpful AI assistant with text-to-speech capabilities. You provide clear, concise, and engaging responses. When speaking, you use natural conversational language that sounds good when read aloud. You remember previous parts of our conversation and can reference them when relevant."""
    
    def add_exchange(self, user_message: str, assistant_response: str):
        """Add a user-assistant exchange to memory"""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        self.conversation_history.append({
            "role": "assistant", 
            "content": assistant_response
        })
        
        # Trim history if too long (keep system prompt + recent exchanges)
        if len(self.conversation_history) > self.max_history:
            # Remove oldest user-assistant pair
            self.conversation_history = self.conversation_history[2:]
    
    def get_full_context(self) -> List[Dict[str, str]]:
        """Get full conversation context including system prompt"""
        context = [{"role": "system", "content": self.system_prompt}]
        context.extend(self.conversation_history)
        return context
    
    def clear_history(self):
        """Clear conversation history but keep system prompt"""
        self.conversation_history = []
        self.conversation_start_time = datetime.now()
        print("🧹 Conversation memory cleared")
    
    def set_system_prompt(self, new_prompt: str):
        """Update the system prompt"""
        self.system_prompt = new_prompt
        print("🎭 System prompt updated")
    
    def get_memory_summary(self) -> str:
        """Get a summary of current memory state"""
        exchanges = len(self.conversation_history) // 2
        duration = datetime.now() - self.conversation_start_time
        
        summary = f"Memory: {exchanges} exchanges"
        if exchanges > 0:
            summary += f", {duration.total_seconds()/60:.1f}min session"
        
        return summary
    
    def save_memory(self, filepath: str):
        """Save current memory to file"""
        try:
            memory_data = {
                "system_prompt": self.system_prompt,
                "conversation_history": self.conversation_history,
                "conversation_start_time": self.conversation_start_time.isoformat(),
                "saved_at": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Memory saved to: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save memory: {e}")
            return False
    
    def load_memory(self, filepath: str):
        """Load memory from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
            
            self.system_prompt = memory_data.get("system_prompt", self.get_default_system_prompt())
            self.conversation_history = memory_data.get("conversation_history", [])
            
            # Try to parse the start time
            try:
                self.conversation_start_time = datetime.fromisoformat(
                    memory_data.get("conversation_start_time", datetime.now().isoformat())
                )
            except:
                self.conversation_start_time = datetime.now()
            
            exchanges = len(self.conversation_history) // 2
            print(f"📁 Memory loaded: {exchanges} previous exchanges")
            return True
            
        except FileNotFoundError:
            print(f"❌ Memory file not found: {filepath}")
            return False
        except Exception as e:
            print(f"❌ Failed to load memory: {e}")
            return False

class OllamaTTS:
    def __init__(self, model="llama3.2", ollama_url="http://localhost:11434", 
                 speech_rate=175, volume=1.0, save_responses=False,
                 system_prompt=None, max_memory=50):
        self.model = model
        self.ollama_url = ollama_url
        self.save_responses = save_responses
        self.last_response = ""
        self.question_count = 0
        self.conversation_file = None
        
        # Initialize conversation memory
        self.memory = ConversationMemory(system_prompt, max_memory)
        
        # Initialize TTS settings
        self.speech_rate = speech_rate
        self.volume = volume
        self.current_voice_id = None
        self.tts_available = (TTS_ENGINE is not None)
        self.use_streaming = True  # Default to streaming mode
        self.speak_while_streaming = True  # New option for real-time TTS
        self.tts_queue = queue.Queue()
        self.tts_thread = None
        self.tts_stop_event = threading.Event()
        
        # Test TTS availability and get voice info
        if TTS_ENGINE == "pyttsx3":
            try:
                # Test with a temporary engine
                test_engine = pyttsx3.init()
                voices = test_engine.getProperty('voices')
                print("Available TTS voices:")
                for i, voice in enumerate(voices[:5]):  # Show first 5
                    print(f"  {i}: {voice.name}")
                test_engine.stop()
                del test_engine
                print("✅ TTS (pyttsx3) is available")
                    
            except Exception as e:
                print(f"TTS initialization test failed: {e}")
                self.tts_available = False
                
        elif TTS_ENGINE == "sapi":
            try:
                test_engine = win32com.client.Dispatch("SAPI.SpVoice")
                print("✅ TTS (SAPI) is available")
            except Exception as e:
                print(f"SAPI TTS test failed: {e}")
                self.tts_available = False
        
        # Setup conversation logging
        if save_responses:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.conversation_file = f"ollama_conversation_{timestamp}.txt"
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                f.write(f"Ollama Conversation - {datetime.now()}\n")
                f.write(f"Server: {self.ollama_url}\n")
                f.write(f"Model: {self.model}\n")
                f.write(f"System Prompt: {self.memory.system_prompt}\n")
                f.write("=" * 50 + "\n\n")
    
    def check_ollama_installation(self):
        """Check if Ollama is installed and provide installation instructions"""
        import subprocess
        import platform
        
        try:
            # Check if ollama command exists
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Ollama is installed")
                return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Ollama not found, show installation instructions
        print("❌ Ollama is not installed or not in PATH")
        print("\n" + "="*60)
        print("OLLAMA INSTALLATION INSTRUCTIONS")
        print("="*60)
        
        system = platform.system().lower()
        
        if system == "windows":
            print("\n🪟 WINDOWS INSTALLATION:")
            print("1. Download from: https://ollama.ai/download/windows")
            print("2. Run OllamaSetup.exe installer")
            print("3. Ollama will start automatically in system tray")
            print("4. Open Command Prompt or PowerShell and run:")
            print("   ollama pull llama3.2")
            print("\nAlternative (if you have winget):")
            print("   winget install Ollama.Ollama")
            
        elif system == "darwin":
            print("\n🍎 MACOS INSTALLATION:")
            print("1. Download from: https://ollama.ai/download/mac")
            print("2. Drag Ollama.app to Applications folder")
            print("3. Launch Ollama from Applications")
            print("4. Open Terminal and run:")
            print("   ollama pull llama3.2")
            print("\nAlternative (if you have Homebrew):")
            print("   brew install ollama")
            
        else:  # Linux
            print("\n🐧 LINUX INSTALLATION:")
            print("1. Run the installation script:")
            print("   curl -fsSL https://ollama.ai/install.sh | sh")
            print("2. Start the service:")
            print("   sudo systemctl start ollama")
            print("   sudo systemctl enable ollama")
            print("3. Pull a model:")
            print("   ollama pull llama3.2")
            print("\nAlternative (manual):")
            print("   # Download binary from https://github.com/ollama/ollama/releases")
            print("   # Place in /usr/local/bin or /usr/bin")
        
        print("\n📋 AFTER INSTALLATION:")
        print("1. Verify installation: ollama --version")
        print("2. Test the model: ollama run llama3.2")
        print("3. Check API server: curl http://localhost:11434/api/tags")
        print("\n💡 RECOMMENDED MODELS TO TRY:")
        print("   ollama pull llama3.2        # Good balance (4.3GB)")
        print("   ollama pull llama3.2:1b     # Fastest, smaller (1.3GB)")
        print("   ollama pull mistral         # Alternative model (4.1GB)")
        print("   ollama pull codellama       # For coding tasks (3.8GB)")
        
        print("\n🔧 TROUBLESHOOTING:")
        print("- If 'connection refused': Run 'ollama serve' manually")
        print("- If slow responses: Try 'llama3.2:1b' model")
        print("- Check if running: netstat -an | grep 11434")
        print("- Windows: Check system tray for Ollama icon")
        
        print("="*60)
        return False
    
    def test_connection(self):
        """Test connection to ollama server"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Cannot connect to ollama server: {e}")
    
    def get_models(self):
        """Get list of available models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            response.raise_for_status()
            return response.json().get('models', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error getting models: {e}")
    
    def ask_ollama_with_context(self, prompt: str) -> str:
        """Send prompt with full conversation context to ollama API"""
        # Get full conversation context
        messages = self.memory.get_full_context()
        messages.append({"role": "user", "content": prompt})
        
        # For Ollama, we need to format this as a single prompt with context
        formatted_prompt = self.format_messages_for_ollama(messages)
        
        request_data = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": self.use_streaming
        }
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=request_data,
                timeout=120,
                stream=self.use_streaming
            )
            response.raise_for_status()
            
            if self.use_streaming:
                # Handle streaming response with real-time TTS
                full_response = ""
                text_buffer = ""
                print(f"\n🤖 Ollama ({self.model}) - {self.memory.get_memory_summary()}:")
                
                # Start TTS thread if speaking while streaming
                if self.speak_while_streaming and self.tts_available:
                    self.start_tts_thread()
                    print("🔊 Speaking as stream arrives...")
                
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            
                            # Get the response text from this chunk
                            if 'response' in chunk:
                                text_chunk = chunk['response']
                                full_response += text_chunk
                                text_buffer += text_chunk
                                
                                # Print chunk immediately for real-time display
                                print(text_chunk, end='', flush=True)
                                
                                # Extract and speak complete sentences
                                if self.speak_while_streaming and self.tts_available:
                                    sentences, text_buffer = self.extract_sentences(text_buffer)
                                    for sentence in sentences:
                                        if sentence.strip():
                                            self.speak_text_immediate(sentence)
                            
                            # Check if this is the final chunk
                            if chunk.get('done', False):
                                # Speak any remaining text
                                if self.speak_while_streaming and self.tts_available and text_buffer.strip():
                                    self.speak_text_immediate(text_buffer)
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"\nError parsing JSON chunk: {e}")
                            continue
                
                print()  # New line after streaming is complete
                
                # Wait for TTS to finish if we were speaking during streaming
                if self.speak_while_streaming and self.tts_available:
                    # Wait a moment for TTS queue to finish
                    self.tts_queue.join()
                    self.stop_tts_thread()
                    print("✅ Streaming and speaking complete!")
                
                return full_response.strip()
            else:
                # Handle non-streaming response
                result = response.json()
                full_response = result.get('response', '')
                print(f"\n🤖 Ollama ({self.model}) - {self.memory.get_memory_summary()}:")
                print(full_response)
                return full_response
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def format_messages_for_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation messages for Ollama's prompt format"""
        formatted_parts = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                formatted_parts.append(f"System: {content}")
            elif role == "user":
                formatted_parts.append(f"Human: {content}")
            elif role == "assistant":
                formatted_parts.append(f"Assistant: {content}")
        
        # Add prompt for the assistant to respond
        formatted_parts.append("Assistant:")
        
        return "\n\n".join(formatted_parts)
    
    def ask_ollama(self, prompt):
        """Legacy method - redirects to context-aware version"""
        return self.ask_ollama_with_context(prompt)
    
    def speak_text_immediate(self, text):
        """Speak text immediately in a separate thread"""
        if not self.tts_available or not text.strip():
            return
            
        # Check if muted
        if hasattr(self, 'muted') and self.muted:
            return
            
        # Add text to TTS queue
        self.tts_queue.put(text.strip())
    
    def tts_worker(self):
        """Worker thread that processes TTS queue"""
        while not self.tts_stop_event.is_set():
            try:
                # Get text from queue with timeout
                text = self.tts_queue.get(timeout=0.1)
                if text and text.strip():
                    self._speak_text_engine(text)
                self.tts_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS worker error: {e}")
    
    def start_tts_thread(self):
        """Start the TTS worker thread"""
        if self.tts_thread is None or not self.tts_thread.is_alive():
            self.tts_stop_event.clear()
            self.tts_thread = threading.Thread(target=self.tts_worker, daemon=True)
            self.tts_thread.start()
    
    def stop_tts_thread(self):
        """Stop the TTS worker thread and clear queue"""
        self.tts_stop_event.set()
        # Clear the queue
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except queue.Empty:
                break
        if self.tts_thread and self.tts_thread.is_alive():
            self.tts_thread.join(timeout=1.0)
    
    def _speak_text_engine(self, text):
        """Internal method to actually speak text using TTS engine"""
        if TTS_ENGINE != "pyttsx3" and TTS_ENGINE != "sapi":
            return
            
        if TTS_ENGINE == "pyttsx3":
            tts_engine = None
            try:
                tts_engine = pyttsx3.init()
                tts_engine.setProperty('rate', self.speech_rate)
                tts_engine.setProperty('volume', self.volume)
                
                if hasattr(self, 'current_voice_id') and self.current_voice_id:
                    try:
                        tts_engine.setProperty('voice', self.current_voice_id)
                    except:
                        pass
                
                tts_engine.say(text)
                tts_engine.runAndWait()
                
            except Exception as e:
                pass  # Silently fail to avoid interrupting stream
            finally:
                if tts_engine:
                    try:
                        tts_engine.stop()
                        del tts_engine
                    except:
                        pass
                        
        elif TTS_ENGINE == "sapi":
            try:
                sapi_engine = win32com.client.Dispatch("SAPI.SpVoice")
                sapi_engine.Speak(text)
            except Exception as e:
                pass  # Silently fail
    
    def speak_text(self, text):
        """Speak the given text using TTS - reinitialize engine each time for reliability"""
        if TTS_ENGINE != "pyttsx3" and TTS_ENGINE != "sapi":
            print("⚠️ TTS not available")
            return
            
        # Check if muted
        if hasattr(self, 'muted') and self.muted:
            print("🔇 Audio is muted")
            return
            
        # Clean the text for better TTS
        cleaned_text = text.strip()
        if not cleaned_text:
            return
            
        print("🔊 Speaking response...")
        self._speak_text_engine(cleaned_text)
        print("✅ Finished speaking")
    
    def extract_sentences(self, text_buffer):
        """Extract complete sentences from text buffer"""
        # Simple sentence boundary detection
        sentences = []
        sentence_endings = re.finditer(r'[.!?]+[\s\n]*', text_buffer)
        
        last_end = 0
        for match in sentence_endings:
            sentence = text_buffer[last_end:match.end()].strip()
            if sentence:
                sentences.append(sentence)
            last_end = match.end()
        
        # Return sentences and remaining text
        remaining = text_buffer[last_end:].strip()
        return sentences, remaining
    
    def save_conversation(self, question, answer):
        """Save Q&A to file if enabled"""
        if self.conversation_file:
            try:
                with open(self.conversation_file, 'a', encoding='utf-8') as f:
                    f.write(f"Q{self.question_count}: {question}\n")
                    f.write(f"A{self.question_count}: {answer}\n\n")
            except Exception as e:
                print(f"Error saving conversation: {e}")
    
    def handle_command(self, input_text):
        """Handle special commands"""
        input_lower = input_text.lower().strip()
        
        if input_lower in ['exit', 'quit', 'bye']:
            return 'exit'
        
        elif input_lower in ['clear', 'new', 'reset']:
            self.memory.clear_history()
            return 'continue'
        
        elif input_lower == 'memory':
            exchanges = len(self.memory.conversation_history) // 2
            print(f"\n🧠 Memory Status:")
            print(f"   Exchanges: {exchanges}")
            print(f"   Max history: {self.memory.max_history}")
            print(f"   System prompt: {len(self.memory.system_prompt)} chars")
            if exchanges > 0:
                duration = datetime.now() - self.memory.conversation_start_time
                print(f"   Session time: {duration.total_seconds()/60:.1f} minutes")
            return 'continue'
        
        elif input_lower.startswith('system '):
            new_prompt = input_text[7:].strip()
            if new_prompt:
                self.memory.set_system_prompt(new_prompt)
                print(f"System prompt set to: {new_prompt[:100]}{'...' if len(new_prompt) > 100 else ''}")
            else:
                print(f"Current system prompt: {self.memory.system_prompt}")
            return 'continue'
        
        elif input_lower.startswith('save_memory '):
            filename = input_text[12:].strip()
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ollama_memory_{timestamp}.json"
            self.memory.save_memory(filename)
            return 'continue'
        
        elif input_lower.startswith('load_memory '):
            filename = input_text[12:].strip()
            if filename:
                self.memory.load_memory(filename)
            else:
                print("Please specify a filename: load_memory filename.json")
            return 'continue'
        
        elif input_lower == 'models':
            try:
                models = self.get_models()
                print("\nAvailable models:")
                for model in models:
                    name = model.get('name', 'Unknown')
                    if name == self.model:
                        print(f"  • {name} (current)")
                    else:
                        print(f"  • {name}")
            except Exception as e:
                print(f"Error: {e}")
            return 'continue'
        
        elif input_lower.startswith('model '):
            new_model = input_text[6:].strip()
            print(f"Switching to model: {new_model}")
            self.model = new_model
            return 'continue'
        
        elif input_lower == 'repeat':
            if self.last_response:
                print("\nRepeating last response...")
                print(f"🤖 Ollama ({self.model}):")
                print(self.last_response)
                print("="*50)
                self.speak_text(self.last_response)
            else:
                print("No previous response to repeat")
            return 'continue'
        
        elif input_lower == 'test_tts':
            print("Testing TTS with sample text...")
            self.speak_text("This is a test of the text to speech system. Testing one, two, three.")
            return 'continue'
        
        elif input_lower == 'voice':
            if TTS_ENGINE == "pyttsx3":
                try:
                    # Create temporary engine to list voices
                    temp_engine = pyttsx3.init()
                    voices = temp_engine.getProperty('voices')
                    print("\nAvailable voices:")
                    for i, voice in enumerate(voices):
                        marker = " (current)" if voice.id == self.current_voice_id else ""
                        print(f"  {i}: {voice.name}{marker}")
                    temp_engine.stop()
                    del temp_engine
                except Exception as e:
                    print(f"Error listing voices: {e}")
            return 'continue'
        
        elif input_lower.startswith('voice '):
            try:
                voice_num = int(input_text[6:].strip())
                if TTS_ENGINE == "pyttsx3":
                    # Get voice list and set the voice ID
                    temp_engine = pyttsx3.init()
                    voices = temp_engine.getProperty('voices')
                    if 0 <= voice_num < len(voices):
                        self.current_voice_id = voices[voice_num].id
                        print(f"Changed to voice: {voices[voice_num].name}")
                    else:
                        print(f"Invalid voice number. Use 0-{len(voices)-1}")
                    temp_engine.stop()
                    del temp_engine
            except ValueError:
                print("Invalid voice number")
            except Exception as e:
                print(f"Error changing voice: {e}")
            return 'continue'
        
        elif input_lower in ['faster', 'slower']:
            if input_lower == 'faster':
                self.speech_rate = min(300, self.speech_rate + 25)
            else:
                self.speech_rate = max(50, self.speech_rate - 25)
            print(f"Speech rate: {self.speech_rate}")
            return 'continue'
        
        elif input_lower in ['louder', 'quieter']:
            if input_lower == 'louder':
                self.volume = min(1.0, self.volume + 0.1)
            else:
                self.volume = max(0.0, self.volume - 0.1)
            print(f"Volume: {self.volume:.1f}")
            return 'continue'
        
        elif input_lower in ['mute', 'unmute']:
            if not hasattr(self, 'muted'):
                self.muted = False
                self.volume_before_mute = self.volume
            
            if input_lower == 'mute':
                if not self.muted:
                    self.volume_before_mute = self.volume
                    self.volume = 0.0
                    self.muted = True
                    print("🔇 Audio muted")
                else:
                    print("🔇 Already muted")
            else:  # unmute
                if self.muted:
                    self.volume = getattr(self, 'volume_before_mute', 1.0)
                    self.muted = False
                    print(f"🔊 Audio unmuted - Volume: {self.volume:.1f}")
                else:
                    print("🔊 Audio not muted")
            return 'continue'
        
        elif input_lower.startswith('volume '):
            try:
                volume_str = input_text[7:].strip()
                new_volume = float(volume_str)
                if 0.0 <= new_volume <= 1.0:
                    self.volume = new_volume
                    if hasattr(self, 'muted') and self.muted:
                        self.muted = False
                        print(f"🔊 Volume set to {self.volume:.1f} (unmuted)")
                    else:
                        print(f"🔊 Volume set to {self.volume:.1f}")
                else:
                    print("❌ Volume must be between 0.0 and 1.0")
            except ValueError:
                print("❌ Invalid volume value. Use: volume 0.5")
            return 'continue'
        
        elif input_lower == 'stream':
            self.use_streaming = not self.use_streaming
            mode = "enabled" if self.use_streaming else "disabled"
            print(f"Streaming mode {mode}")
            return 'continue'
        
        elif input_lower == 'live_tts':
            self.speak_while_streaming = not self.speak_while_streaming
            mode = "enabled" if self.speak_while_streaming else "disabled"
            print(f"Live TTS (speak while streaming) {mode}")
            return 'continue'
        
        elif input_lower == 'help':
            self.show_help()
            return 'continue'
        
        return 'process'
    
    def show_help(self):
        """Show available commands and features"""
        print("\n" + "="*70)
        print("                    OLLAMA TTS ASSISTANT HELP")
        print("="*70)
        
        print("\n🗣️  CONVERSATION COMMANDS:")
        print("  <question>            - Ask ollama a question with memory context")
        print("  exit/quit/bye         - Exit the program")
        print("  repeat                - Repeat last response with TTS")
        
        print("\n🧠  MEMORY MANAGEMENT:")
        print("  memory                - Show current memory status")
        print("  clear/new/reset       - Clear conversation memory (start fresh)")
        print("  system <prompt>       - Set/view system prompt for assistant personality")
        print("  save_memory [file]    - Save conversation memory to JSON file")
        print("  load_memory <file>    - Load conversation memory from JSON file")
        
        print("\n🤖  MODEL MANAGEMENT:")
        print("  models                - List all available Ollama models")
        print("  model <name>          - Switch to different model (e.g., llama3.2:1b)")
        print("  stream                - Toggle streaming/non-streaming mode")
        
        print("\n🔊  AUDIO CONTROLS:")
        print("  test_tts              - Test TTS with sample text")
        print("  mute/unmute           - Instantly mute/unmute all audio")
        print("  volume <0.0-1.0>      - Set exact volume (e.g., volume 0.5)")
        print("  louder/quieter        - Adjust volume by ±0.1")
        print("  faster/slower         - Adjust speech rate by ±25")
        print("  live_tts              - Toggle real-time TTS during streaming")
        
        print("\n🎭  VOICE CONTROLS:")
        print("  voice                 - List all available TTS voices")
        print("  voice <number>        - Switch to voice by number (e.g., voice 2)")
        
        print("\n💡  COMMAND LINE USAGE:")
        print("  Start with custom settings:")
        print("    python ollama_tts.py --volume 0.5 --mute")
        print("    python ollama_tts.py --model llama3.2:1b --rate 200")
        print("    python ollama_tts.py --system-prompt 'You are a coding expert'")
        print("    python ollama_tts.py --load-memory session.json")
        
        print("\n📊  MEMORY FEATURES:")
        print("  • Assistant remembers your entire conversation")
        print("  • References previous questions and responses")
        print("  • Maintains context across multiple exchanges")
        print("  • Configurable memory limit (default: 50 exchanges)")
        print("  • Persistent memory save/load functionality")
        
        print("\n🎵  AUDIO FEATURES:")
        print("  • Real-time TTS during streaming responses")
        print("  • Multiple TTS engine support (pyttsx3, SAPI)")
        print("  • Voice selection and customization")
        print("  • Precise volume and rate control")
        print("  • Smart mute system with volume memory")
        print("  • Command line audio configuration")
        
        print("\n" + "="*70)
    
    def run(self):
        """Main conversation loop"""
        print("=" * 70)
        print("      Ollama TTS Assistant with Memory - Python Version")
        print("=" * 70)
        print(f"Server: {self.ollama_url}")
        print(f"Model: {self.model}")
        print(f"Memory: Max {self.memory.max_history} exchanges")
        print(f"System prompt: {len(self.memory.system_prompt)} chars")
        
        # Display audio status
        if not self.tts_available:
            print("⚠️  TTS not available - responses will be text-only")
        else:
            if hasattr(self, 'muted') and self.muted:
                print(f"🔇 TTS muted (volume was {getattr(self, 'volume_before_mute', 1.0):.1f})")
            else:
                print(f"🔊 TTS volume: {self.volume:.1f}")
        
        # First check if Ollama is installed at all
        print("\nChecking Ollama installation...")
        if not self.check_ollama_installation():
            print("\nPlease install Ollama first, then run this script again.")
            return
        
        # Test connection to ollama server
        print("\nTesting connection to ollama server...")
        try:
            server_info = self.test_connection()
            print("✅ Connected to ollama server")
            
            # Show available models
            models = server_info.get('models', [])
            if not models:
                print("\n⚠️  No models found! You need to pull a model first.")
                print("Run: ollama pull llama3.2")
                return
                
            print("\nAvailable models:")
            for model in models:
                name = model.get('name', 'Unknown')
                if name == self.model:
                    print(f"  • {name} (selected)")
                else:
                    print(f"  • {name}")
                    
        except ConnectionError as e:
            print(f"❌ {e}")
            print("\nOllama is installed but not running.")
            print("Please run: ollama serve")
            print("Then try this script again.")
            return
        
        print("\n🧠 Memory Features:")
        print("  • Conversation context is preserved across questions")
        print("  • Use 'clear' to start fresh conversation")
        print("  • Use 'memory' to check current memory status")
        print("  • Use 'system <prompt>' to set assistant personality")
        print("  • Use 'save_memory' / 'load_memory' for persistence")
        
        print("\nType 'help' for all commands or start asking questions!")
        print("Type 'test_tts' to test text-to-speech")
        print("Type 'exit' to quit")
        print("=" * 70)
        
        # Main conversation loop
        try:
            while True:
                try:
                    user_input = input("\nYou: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle commands
                    command_result = self.handle_command(user_input)
                    
                    if command_result == 'exit':
                        break
                    elif command_result == 'continue':
                        continue
                    
                    # Process as question with memory context
                    self.question_count += 1
                    mode_text = "streaming" if self.use_streaming else "non-streaming"
                    print(f"\n🤔 Asking ollama ({mode_text})...")
                    
                    try:
                        response = self.ask_ollama_with_context(user_input)
                        
                        if response and response.strip():
                            # Add exchange to memory
                            self.memory.add_exchange(user_input, response)
                            
                            # Save conversation to file
                            self.save_conversation(user_input, response)
                            
                            # Store for repeat function
                            self.last_response = response
                            
                            # Speak response if not already spoken during streaming
                            if not (self.use_streaming and self.speak_while_streaming and self.tts_available):
                                print("\n" + "="*50)
                                if self.tts_available:
                                    self.speak_text(response)
                                else:
                                    print("⚠️ TTS not available for this response")
                            
                        else:
                            print("❌ Empty response from ollama")
                            
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        print("Make sure ollama server is running: ollama serve")
                
                except KeyboardInterrupt:
                    print("\n\nInterrupted by user")
                    break
                except EOFError:
                    break
                    
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        finally:
            # Clean up TTS thread
            self.stop_tts_thread()
            print("\n🎉 Session ended. Thank you!")
            if self.conversation_file:
                print(f"💾 Conversation saved to: {self.conversation_file}")
            
            # Offer to save memory
            if len(self.memory.conversation_history) > 0:
                try:
                    save_choice = input("Save conversation memory? (y/N): ").lower().strip()
                    if save_choice in ['y', 'yes']:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        memory_file = f"ollama_memory_{timestamp}.json"
                        self.memory.save_memory(memory_file)
                except (KeyboardInterrupt, EOFError):
                    print("\n👋 Goodbye!")


def main():
    parser = argparse.ArgumentParser(description="Ollama TTS Assistant with Memory")
    parser.add_argument("--model", "-m", default="llama3.2", 
                       help="Ollama model to use (default: llama3.2)")
    parser.add_argument("--url", "-u", default="http://localhost:11434",
                       help="Ollama server URL (default: http://localhost:11434)")
    parser.add_argument("--rate", "-r", type=int, default=175,
                       help="Speech rate (default: 175)")
    parser.add_argument("--volume", "-v", type=float, default=1.0,
                       help="Speech volume 0.0-1.0 (default: 1.0)")
    parser.add_argument("--mute", action="store_true",
                       help="Start with audio muted")
    parser.add_argument("--save", "-s", action="store_true",
                       help="Save conversation to file")
    parser.add_argument("--system-prompt", "-sp", type=str,
                       help="Custom system prompt for the assistant")
    parser.add_argument("--max-memory", "-mm", type=int, default=50,
                       help="Maximum conversation exchanges to remember (default: 50)")
    parser.add_argument("--load-memory", "-lm", type=str,
                       help="Load conversation memory from file")
    
    args = parser.parse_args()
    
    # Validate volume range
    if not (0.0 <= args.volume <= 1.0):
        print("❌ Error: Volume must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Create the assistant
    assistant = OllamaTTS(
        model=args.model,
        ollama_url=args.url,
        speech_rate=args.rate,
        volume=args.volume,
        save_responses=args.save,
        system_prompt=args.system_prompt,
        max_memory=args.max_memory
    )
    
    # Set mute state if requested
    if args.mute:
        assistant.volume_before_mute = args.volume
        assistant.volume = 0.0
        assistant.muted = True
        print("🔇 Started with audio muted")
    
    # Load memory if specified
    if args.load_memory:
        assistant.memory.load_memory(args.load_memory)
    
    assistant.run()


if __name__ == "__main__":
    main()