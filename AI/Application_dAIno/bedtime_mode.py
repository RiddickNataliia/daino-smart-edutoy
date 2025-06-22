import pygame
import time
import os
import threading

class BedtimeMode:
    def __init__(self, audio_path="audio/lullabies"):
        self.audio_path = audio_path
        self.lullabies = self._load_lullabies()
        self.duration_minutes = 0
        self.quit_requested = False
        self.pi_socket = None
        self.mixer_initialized = False

    def _load_lullabies(self):
        """Load all lullaby files from the specified directory"""
        if not os.path.exists(self.audio_path):
            os.makedirs(self.audio_path)
            return []
        files = [os.path.join(self.audio_path, f) 
                 for f in os.listdir(self.audio_path) 
                 if f.endswith(('.mp3', '.wav'))]
        return sorted(files)

    def set_duration(self, minutes):
        """Set bedtime duration (10-120 minutes)"""
        self.duration_minutes = max(10, min(120, minutes))

    def _ensure_mixer_initialized(self):
        """Ensure pygame mixer is initialized before playing sounds"""
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            self.mixer_initialized = True

    def _send_with_retry(self, color, max_attempts=5, initial_delay=1.0):
        """Send command with exponential backoff retry logic"""
        delay = initial_delay
        for attempt in range(max_attempts):
            try:
                # Pass required arguments with dummy values
                self.send_to_pi("dummy_shape", 0.0, color=color)
                return True
            except Exception as e:
                print(f"Send attempt {attempt+1} failed: {e}")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
        return False

    def play_lullaby(self):
        """Play lullabies sequentially in order until time expires"""
        self._ensure_mixer_initialized()
        
        if not self.lullabies:
            print("No lullabies found in directory:", self.audio_path)
            return
            
        start_time = time.time()
        end_time = start_time + (self.duration_minutes * 60)
        index = 0
        
        while time.time() < end_time and not self.quit_requested:
            lullaby = self.lullabies[index]
            print(f"Playing: {os.path.basename(lullaby)}")
            try:
                sound = pygame.mixer.Sound(lullaby)
                sound.play()
                while (pygame.mixer.get_busy() and 
                       time.time() < end_time and 
                       not self.quit_requested):
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error playing {lullaby}: {e}")
            index = (index + 1) % len(self.lullabies)
        pygame.mixer.stop()

    def run(self):
        print("Starting Bedtime mode...")
        print(f"Duration: {self.duration_minutes} minutes")
        
        # Initialize pygame mixer
        pygame.mixer.init()
        self.mixer_initialized = True
        
        # 1. FIRST: Set LED to soft yellow with retry
        print("Setting LED to soft yellow...")
        if not self._send_with_retry("soft_yellow"):
            print("Warning: Failed to set LED after multiple attempts. Continuing without LED control.")
        
        # 2. ONLY AFTER LED IS SET: Start audio playback
        print("Starting audio playback...")
        try:
            # Start lullaby playback in background thread
            lullaby_thread = threading.Thread(target=self.play_lullaby)
            lullaby_thread.daemon = True
            lullaby_thread.start()
            
            # Display countdown timer in main thread
            start_time = time.time()
            end_time = start_time + (self.duration_minutes * 60)
            
            while time.time() < end_time and not self.quit_requested:
                remaining = int(end_time - time.time())
                mins, secs = divmod(remaining, 60)
                print(f"Time remaining: {mins:02d}:{secs:02d}", end='\r')
                time.sleep(1)
                
            print("\nBedtime session complete. LED remains on.")
            
        except KeyboardInterrupt:
            self.quit_requested = True
            print("\nBedtime mode interrupted")
        finally:
            if self.mixer_initialized:
                pygame.mixer.quit()
            
    def send_to_pi(self, shape, duration, correct=True, color=None):
        """Send LED color command to Raspberry Pi"""
        if color is None:
            return
        if hasattr(self, 'pi_socket') and self.pi_socket:
            try:
                import protocol
                cmd = protocol.create_command(
                    protocol.SET_LED_COLOR, 
                    {"color": color}
                )
                self.pi_socket.sendall(cmd)
            except Exception as e:
                print("Error sending to Pi:", e)
                raise
                
    def cleanup(self):
        self.quit_requested = True
        if hasattr(self, 'pi_socket') and self.pi_socket:
            try:
                # Reset LED to white when exiting
                self.send_to_pi("dummy_shape", 0.0, color="white")
            except:
                pass
