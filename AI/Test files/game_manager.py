import cv2
from ultralytics import YOLO
import pygame
import socket
import time
import protocol
import os
from threading import Thread

class LearningShapesTrainer:
    def __init__(self, pi_ip='192.168.168.167'):
        # Pygame initialization
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        
        # Camera setup
        self.cam = cv2.VideoCapture(1)
        if not self.cam.isOpened():
            raise RuntimeError("Camera not accessible")
        
        # AI model
        self.model = YOLO('shape_model.pt')
        
        # Network setup
        self.pi_ip = pi_ip
        self.pi_socket = None
        self.connect_to_pi()
        
        # State tracking
        self.last_shape = None
        self.waiting_for_background = False
        self.audio_playing = False
        self.current_audio = None
        
        # Timing controls
        self.last_reaction_time = 0
        self.cooldown = 3.0  # 3 seconds between reactions
        
        # Audio setup
        self.audio_files = {}
        shapes = ['circle', 'square', 'triangle', 'star', 'pentagon']
        for shape in shapes:
            path = f"audio/shapes/{shape}.mp3"
            if os.path.exists(path):
                self.audio_files[shape] = pygame.mixer.Sound(path)
            else:
                print(f"Missing audio: {path}")

    def connect_to_pi(self):
        """Establish connection with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.pi_socket = socket.socket()
                self.pi_socket.connect((self.pi_ip, 8888))
                print(f"Connected to Pi at {self.pi_ip}")
                return
            except ConnectionRefusedError:
                print(f"Connection attempt {attempt+1} failed")
                time.sleep(2)
        raise ConnectionError("Could not connect to Pi")

    def get_shape_name(self, detection):
        """Extract shape from detection, filtering invalid classes"""
        parts = detection.split('_')
        shape = parts[-1] if len(parts) > 1 else detection
        return None if shape.lower() == "invalid" else shape

    def process_frame(self):
        """Capture frame and return top detection"""
        ret, frame = self.cam.read()
        if not ret:
            print("Frame capture failed")
            return None, None, 0.0
        
        results = self.model(frame)[0]
        boxes = results.boxes
        if len(boxes) == 0:
            return frame, None, 0.0
        
        # Get highest confidence detection
        max_idx = boxes.conf.argmax()
        class_id = int(boxes.cls[max_idx])
        confidence = float(boxes.conf[max_idx])
        detection = results.names[class_id]
        
        return frame, self.get_shape_name(detection), confidence

    def should_react(self, current_shape, confidence):
        # Skip invalid detections entirely
        if current_shape is None or current_shape.lower() == "invalid":
            self.waiting_for_background = True
            return False
        
        # Minimum confidence threshold 
        if confidence < 0.75:
            return False
        
        # Debounce period (2 seconds) for same shape
        time_since_last = time.time() - self.last_reaction_time
        if current_shape == self.last_shape and time_since_last < 2.0:
            return False
        
        # Background check logic
        if self.waiting_for_background:
            # Valid reaction after background
            self.waiting_for_background = False
            self.last_shape = current_shape
            return True
        else:
            # New shape detection
            if current_shape != self.last_shape:
                self.last_shape = current_shape
                return True
        
        return False


    def play_audio(self, shape):
        """Play audio in a non-blocking thread"""
        if not self.audio_playing and shape in self.audio_files:
            self.audio_playing = True
            Thread(target=self._audio_thread, args=(shape,)).start()

    def _audio_thread(self, shape):
        """Internal audio playback thread"""
        sound = self.audio_files[shape]
        sound.play()
        while pygame.mixer.get_busy():
            time.sleep(0.1)
        self.audio_playing = False

    def send_to_pi(self, shape, duration):
        """Send command to Pi with error recovery"""
        try:
            cmd = protocol.create_command(
                protocol.LEARNING_SHAPE,
                {"shape": shape, "duration": duration}
            )
            self.pi_socket.sendall(cmd)
        except (ConnectionResetError, BrokenPipeError):
            print("Reconnecting to Pi...")
            self.connect_to_pi()
            self.pi_socket.sendall(cmd)

    def run_learning_mode(self):
        print("Starting learning mode...")
        try:
            while True:
                # Process Pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                
                # Process frame
                frame, current_shape, confidence = self.process_frame()
                if frame is None:
                    continue
                
                # Display logic
                display_frame = frame.copy()
                time_since_last = time.time() - self.last_reaction_time
                reaction = False
                
                # Cooldown indicator
                cv2.rectangle(display_frame, (10, 100), (110, 120), (50, 50, 50), -1)
                if time_since_last < self.cooldown:
                    progress = int(100 * (time_since_last / self.cooldown))
                    cv2.rectangle(display_frame, (10, 100), (10+progress, 120), (0,255,0), -1)
                
                # Detection handling
                if time_since_last >= self.cooldown:
                    reaction = self.should_react(current_shape, confidence)
                
                # Visual feedback
                if current_shape:
                    cv2.putText(display_frame, f"{current_shape} ({confidence:.2f})", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
                
                status = "Ready" if time_since_last >= self.cooldown else "Cooling down"
                cv2.putText(display_frame, status, (10, 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)
                
                cv2.imshow("Learning Mode", display_frame)
                
                # Handle reactions
                if reaction and current_shape:
                    try:
                        duration = self.audio_files[current_shape].get_length()
                        self.send_to_pi(current_shape, duration)
                        self.play_audio(current_shape)
                        self.last_reaction_time = time.time()
                        print(f"Processed: {current_shape} ({confidence:.2f})")
                    except Exception as e:
                        print(f"Error: {str(e)}")
                
                # Exit key
                if cv2.waitKey(1) == ord('q'):
                    break
        finally:
            pygame.quit()
            self.cam.release()
            cv2.destroyAllWindows()
            if self.pi_socket:
                self.pi_socket.close()
            print("System shutdown complete")

if __name__ == "__main__":
    trainer = LearningShapesTrainer()
    trainer.run_learning_mode()
