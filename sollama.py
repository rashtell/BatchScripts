#!/usr/bin/env python3
"""
Ollama TTS Assistant - Python Version
Direct API calls to ollama server with text-to-speech

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
"""

import requests
import json
import argparse
import sys
import time
import threading
import queue
import re
from datetime import datetime

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

class OllamaTTS:
    def __init__(self, model="llama3.2", ollama_url="http://localhost:11434", 
                 speech_rate=175, volume=1.0, save_responses=False):
        self.model = model
        self.ollama_url = ollama_url
        self.save_responses = save_responses
        self.last_response = ""
        self.question_count = 0
        self.conversation_file = None
        
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
    
    def ask_ollama(self, prompt):
        """Send prompt to ollama API with optional streaming"""
        request_data = {
            "model": self.model,
            "prompt": prompt,
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
                print(f"\n🤖 Ollama ({self.model}):")
                
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
                print(f"\n🤖 Ollama ({self.model}):")
                print(full_response)
                return full_response
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def reinitialize_tts_if_needed(self):
        """Reinitialize TTS if it seems to have stopped working"""
        if TTS_ENGINE == "pyttsx3" and self.tts_initialized:
            try:
                # Test if TTS is still working by checking properties
                current_rate = self.tts.getProperty('rate')
                if current_rate is None:
                    raise Exception("TTS engine appears to be dead")
            except Exception as e:
                print(f"🔧 TTS needs reinitialization: {e}")
                try:
                    # Reinitialize TTS
                    self.tts.stop()
                    self.tts = pyttsx3.init()
                    self.tts.setProperty('rate', 175)
                    self.tts.setProperty('volume', 1.0)
                    print("✅ TTS reinitialized successfully")
                except Exception as reinit_error:
                    print(f"❌ Failed to reinitialize TTS: {reinit_error}")
                    self.tts_initialized = False
    
    def speak_text_immediate(self, text):
        """Speak text immediately in a separate thread"""
        if not self.tts_available or not text.strip():
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
        """Show available commands"""
        print("\nAvailable commands:")
        print("  exit/quit/bye    - Exit the program")
        print("  models           - List available models")
        print("  model <name>     - Switch to different model")
        print("  repeat           - Repeat last response")
        print("  test_tts         - Test TTS functionality")
        print("  voice            - List available voices")
        print("  voice <number>   - Switch to voice number")
        print("  faster/slower    - Adjust speech speed")
        print("  louder/quieter   - Adjust volume")
        print("  stream           - Toggle streaming mode on/off")
        print("  help             - Show this help")
        print("  <question>       - Ask ollama a question")
    
    def run(self):
        """Main conversation loop"""
        print("=" * 60)
        print("         Ollama TTS Assistant - Python Version")
        print("=" * 60)
        print(f"Server: {self.ollama_url}")
        print(f"Model: {self.model}")
        
        if not self.tts_available:
            print("⚠️  TTS not available - responses will be text-only")
        else:
            print("✅ TTS is available")
        
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
        
        print("\nType 'help' for commands or start asking questions!")
        print("Type 'test_tts' to test text-to-speech")
        print("Type 'exit' to quit")
        print("=" * 60)
        
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
                    
                    # Process as question
                    self.question_count += 1
                    mode_text = "streaming" if self.use_streaming else "non-streaming"
                    print(f"\n🤔 Asking ollama ({mode_text})...")
                    
                    try:
                        response = self.ask_ollama(user_input)
                        
                        if response and response.strip():
                            # Save conversation
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


def main():
    parser = argparse.ArgumentParser(description="Ollama TTS Assistant")
    parser.add_argument("--model", "-m", default="llama3.2", 
                       help="Ollama model to use (default: llama3.2)")
    parser.add_argument("--url", "-u", default="http://localhost:11434",
                       help="Ollama server URL (default: http://localhost:11434)")
    parser.add_argument("--rate", "-r", type=int, default=175,
                       help="Speech rate (default: 175)")
    parser.add_argument("--volume", "-v", type=float, default=1.0,
                       help="Speech volume 0.0-1.0 (default: 1.0)")
    parser.add_argument("--save", "-s", action="store_true",
                       help="Save conversation to file")
    
    args = parser.parse_args()
    
    # Create and run the assistant
    assistant = OllamaTTS(
        model=args.model,
        ollama_url=args.url,
        speech_rate=args.rate,
        volume=args.volume,
        save_responses=args.save
    )
    
    assistant.run()


if __name__ == "__main__":
    main()