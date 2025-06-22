import cv2
import pygame
import time
import os
import random
import threading
import protocol
import traceback
from collections import deque

from base_game import BaseGameMode

class ColorTestingMode(BaseGameMode):
    BEST_SCORE_FILE = "data/color_test_best_score.txt"
    
    def __init__(self, audio_path="audio/color test", camera_index=1):
        super().__init__(camera_index)
        self.load_model('models/color_model.pt')
        self.colors = ['red', 'green', 'blue', 'yellow', 'purple']
        self.audio_path = audio_path
        self._init_pygame()
        self.last_reaction_time = 0
        self.base_cooldown = 1.0
        self.cooldown = self.base_cooldown
        self.audio_playing = False
        self.servo_busy = False
        self.audio_files = self._index_audio_files(audio_path)
        self.pi_socket = None
        self.color_counts = {color: 5 for color in self.colors}
        
        # Score tracking
        self.current_streak = 0
        self.best_streak = self._load_best_score()
        self.session_correct = 0
        
        # Crunch sound effect
        self.crunch_sound = None
        crunch_path = os.path.join(self.audio_path, "crunch.mp3")
        if os.path.exists(crunch_path):
            self.crunch_sound = pygame.mixer.Sound(crunch_path)
            print("Loaded crunch sound effect")
        else:
            print(f"Crunch sound not found at: {crunch_path}")

        # Independent timers for invalid handling
        self.invalid_led_timer_active = False
        self.invalid_led_timer_start = 0
        self.last_invalid_detection_time = 0
        self.invalid_detection_cooldown = 10.0  
        self.invalid_led_duration = 5.0         

    def _init_pygame(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
    
    def _load_best_score(self):
        try:
            if os.path.exists(self.BEST_SCORE_FILE):
                with open(self.BEST_SCORE_FILE, 'r') as f:
                    return int(f.read().strip())
        except Exception as e:
            print(f"Error loading best score: {e}")
        return 0

    def _save_best_score(self):
        try:
            with open(self.BEST_SCORE_FILE, 'w') as f:
                f.write(str(self.best_streak))
        except Exception as e:
            print(f"Error saving best score: {e}")

    def _index_audio_files(self, path):
        audio_files = {"find": {}, "reject": {}, "try_again": {}}
        for color in self.colors:
            audio_files["find"][color] = [
                os.path.join(path, f) for f in os.listdir(path)
                if f.startswith(f"Find {color}")
            ]
            audio_files["try_again"][color] = [
                os.path.join(path, f) for f in os.listdir(path)
                if f.startswith(f"Try again {color}")
            ]
            reject_file = os.path.join(path, f"Reject {color}.mp3")
            if os.path.exists(reject_file):
                audio_files["reject"][color] = reject_file
        reject_invalid = os.path.join(path, "Reject invalid.mp3")
        if os.path.exists(reject_invalid):
            audio_files["reject"]["invalid"] = reject_invalid
        return audio_files

    def play_random_audio(self, category, color):
        if category in ("find", "try_again"):
            files = self.audio_files[category].get(color, [])
            if not files:
                return
            audio_file = random.choice(files)
        elif category == "reject":
            audio_file = self.audio_files["reject"].get(color)
            if not audio_file:
                return
        else:
            return

        sound = pygame.mixer.Sound(audio_file)
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.wait(100)

    def play_startup_audio(self):
        startup_audio = os.path.join(self.audio_path, "Color test start.mp3")
        if os.path.exists(startup_audio):
            sound = pygame.mixer.Sound(startup_audio)
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.wait(100)

    def play_end_audio(self):
        end_audio = os.path.join(self.audio_path, "End color test game.mp3")
        if os.path.exists(end_audio):
            sound = pygame.mixer.Sound(end_audio)
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.wait(100)
    
    def play_crunch_with_delay(self, delay=0.6):
        if self.crunch_sound:
            time.sleep(delay)
            self.crunch_sound.play()

    def process_frame(self):
        ret, frame = self.cam.read()
        if not ret:
            return None, None, 0.0
        results = self.model(frame)[0]
        boxes = results.boxes
        if len(boxes) == 0:
            return frame, None, 0.0
        max_idx = boxes.conf.argmax()
        class_id = int(boxes.cls[max_idx])
        confidence = float(boxes.conf[max_idx])
        detection = results.names[class_id]
        return frame, detection, confidence

    def send_to_pi(self, new_color, duration, correct=True, color=None):
        if self.pi_socket:
            try:
                if color:
                    cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": color})
                elif correct:
                    cmd = protocol.create_command(protocol.LEARNING_COLOR, {"color": new_color, "duration": duration})
                else:
                    cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": "red"})
                self.pi_socket.sendall(cmd)
            except Exception as e:
                print("Error sending to Pi:", e)

    def run(self):
        print("Starting Color Testing mode...")
        print(f"Current best streak: {self.best_streak}")
        self.current_streak = 0
        self.session_correct = 0
        self.play_startup_audio()
        try:
            while True:
                available_colors = [color for color, count in self.color_counts.items() if count > 0]
                if not available_colors:
                    print("All colors used. Ending test.")
                    self.play_end_audio()
                    break

                # Prevent same color twice in a row
                if hasattr(self, "last_color") and self.last_color in available_colors and len(available_colors) > 1:
                    colors_to_choose = [color for color in available_colors if color != self.last_color]
                else:
                    colors_to_choose = available_colors
                
                target_color = random.choice(colors_to_choose)
                self.last_color = target_color  # Store last selected color
                
                print(f"Please insert a {target_color} piece!")
                self.play_random_audio("find", target_color)
                
                # Initialize deques for 10 consecutive detections
                correct_history = deque(maxlen=10)
                incorrect_history = deque(maxlen=10)
                invalid_history = deque(maxlen=10)
                
                while True:
                    current_time = time.time()
                    
                    # Handle LED timer independently
                    if self.invalid_led_timer_active:
                        if current_time - self.invalid_led_timer_start > self.invalid_led_duration:
                            print("Red LED timeout reached. Resetting to white.")
                            self.send_to_pi("reset", 0, color="white")
                            self.invalid_led_timer_active = False
                    
                    frame, detection, conf = self.process_frame()
                    if frame is None:
                        continue
                    
                    display_frame = frame.copy()
                    cv2.putText(display_frame, f"Find: {target_color}", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)

                    # Process detections and update histories
                    if detection and conf >= 0.75:
                        if detection.lower() == "invalid":
                            invalid_history.append("invalid")
                            correct_history.clear()
                            incorrect_history.clear()
                        elif detection == target_color:
                            correct_history.append("correct")
                            incorrect_history.clear()
                            invalid_history.clear()
                        else:
                            incorrect_history.append(detection)
                            correct_history.clear()
                            invalid_history.clear()
                    else:
                        # Clear histories on low confidence or no detection
                        correct_history.clear()
                        incorrect_history.clear()
                        invalid_history.clear()
                    
                    # Check for 10 consecutive correct detections
                    if len(correct_history) == 10 and all(x == "correct" for x in correct_history):
                        print("10 consecutive correct detections!")
                        self.current_streak += 10
                        self.session_correct += 10
                        if self.current_streak > self.best_streak:
                            self.best_streak = self.current_streak
                        
                        self.send_to_pi(target_color, 1.0, correct=True)
                        
                        if self.crunch_sound:
                            threading.Thread(
                                target=self.play_crunch_with_delay,
                                args=(0.6,),
                                daemon=True
                            ).start()
                        
                        self.color_counts[target_color] -= 1
                        time.sleep(0.2)
                        
                        # Wait for piece to be removed
                        while True:
                            frame2, detection2, conf2 = self.process_frame()
                            if detection2 is None or conf2 < 0.75:
                                break
                            time.sleep(0.1)
                        
                        self.send_to_pi("reset", 0, color="white")
                        break

                    # Check for 10 consecutive invalid detections
                    if len(invalid_history) == 10:
                        # Check cooldown for invalid detections
                        if current_time - self.last_invalid_detection_time > self.invalid_detection_cooldown:
                            print("10 consecutive invalid detections!")
                            self.send_to_pi("invalid", 0, correct=False)
                            cv2.putText(display_frame, "Invalid piece!", (10, 120),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2)
                            cv2.imshow("Testing Mode", display_frame)
                            self.play_random_audio("reject", "invalid")
                            
                            # Activate LED timer and update detection time
                            self.invalid_led_timer_active = True
                            self.invalid_led_timer_start = current_time
                            self.last_invalid_detection_time = current_time
                            
                            invalid_history.clear()
                        else:
                            print(f"Invalid cooldown active: {self.invalid_detection_cooldown - (current_time - self.last_invalid_detection_time):.1f}s remaining")

                    # Check for 10 consecutive incorrect detections (same color)
                    if len(incorrect_history) == 10:
                        # Ensure all 10 detections are the same incorrect color
                        if all(x == incorrect_history[0] for x in incorrect_history):
                            detected_color = incorrect_history[0]
                            print(f"10 consecutive incorrect detections! Expected {target_color}, got {detected_color}")
                            self.current_streak = 0
                            self.send_to_pi("wrong", 0, correct=False)
                            self.play_random_audio("reject", detected_color)
                            self.send_to_pi("reset", 0, color="white")
                            self.play_random_audio("try_again", target_color)
                            incorrect_history.clear()
                    
                    cv2.imshow("Testing Mode", display_frame)
                    if cv2.waitKey(1) == ord('q'):
                        return
                
                time.sleep(2)
                
        except Exception as e:
            print(f"Error during game execution: {e}")
            traceback.print_exc()
        finally:
            self._save_best_score()
            
            print("\n--- Game Results ---")
            print(f"Current streak: {self.current_streak} consecutive correct")
            print(f"Best streak: {self.best_streak} consecutive correct")
            print(f"Total correct answers: {self.session_correct}")
            
            self.cam.release()
            pygame.quit()
            cv2.destroyAllWindows()
