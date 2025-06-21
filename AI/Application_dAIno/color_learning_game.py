import os
import time
import pygame
import cv2
import random
from threading import Thread
import protocol
from collections import deque
import traceback

from base_game import BaseGameMode

class LearningColorsMode(BaseGameMode):
    def __init__(self, audio_path="audio/color learn", camera_index=1):
        super().__init__(camera_index)
        self.load_model('models/color_model.pt') 
        self.audio_path = audio_path
        self.audio_files = self._load_audio(audio_path)
        self.min_consistent_frames = 10
        self.detection_buffer = deque(maxlen=self.min_consistent_frames)
        self.last_reaction_time = 0
        self.base_cooldown = 1.0
        self.cooldown = self.base_cooldown
        self.currently_processing = False
        self.audio_playing = False
        self.reaction_in_progress = False
        self.servo_busy = False
        self.servo_last_end_time = 0
        
        # Independent timers
        self.invalid_led_timer_active = False
        self.invalid_led_timer_start = 0
        self.last_invalid_detection_time = 0
        self.invalid_detection_cooldown = 10.0
        self.invalid_led_duration = 5.0

    def _load_audio(self, path):
        audio_files = {}
        colors = ['red', 'blue', 'green', 'yellow', 'purple', 'invalid']

        for color in colors:
            sound_file = f"{path}/{color}.mp3"
            if os.path.exists(sound_file):
                try:
                    audio_files[color] = pygame.mixer.Sound(sound_file)
                    print(f"Loaded {color}")
                except Exception as e:
                    print(f"Failed to load {color}: {e}")
            else:
                print(f"Missing: {sound_file}")
        return audio_files

    def play_audio(self, color):
        if color in self.audio_files and not self.audio_playing:
            self.audio_playing = True
            Thread(target=self._audio_thread, args=(color,)).start()

    def _audio_thread(self, color):
        audio = self.audio_files[color]
        if isinstance(audio, list):
            sound = random.choice(audio)
        else:
            sound = audio
        sound.play()
        while pygame.mixer.get_busy():
            time.sleep(0.1)
        self.audio_playing = False

    def update_cooldown(self, audio_duration):
        servo_time = 1.5
        self.cooldown = audio_duration + servo_time + self.base_cooldown

    def send_to_pi(self, shape, duration, correct=True, color=None):
        if hasattr(self, 'pi_socket') and self.pi_socket:
            try:
                if color:
                    cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": color})
                elif correct:
                    cmd = protocol.create_command(protocol.LEARNING_SHAPE, {"shape": color, "duration": duration})
                else:
                    cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": "red"})
                self.pi_socket.sendall(cmd)
            except Exception as e:
                print("Error sending to Pi:", e)

    def run(self):
        print("Starting Color Learning mode...")
        try:
            while True:
                frame, detection, confidence = self.process_frame()
                if frame is None:
                    continue

                now = time.time()

                if self.servo_busy:
                    display_frame = frame.copy()
                    cv2.putText(display_frame, "Please wait...", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                    cv2.imshow("Learning Mode", display_frame)
                    if cv2.waitKey(1) == ord('q'):
                        break
                    continue

                # Handle LED timer independently
                if self.invalid_led_timer_active:
                    if now - self.invalid_led_timer_start > self.invalid_led_duration:
                        print("Red LED timeout reached. Resetting to white.")
                        self.send_to_pi("reset", 0, color="white")
                        self.invalid_led_timer_active = False

                # Process detections
                if detection and confidence >= 0.75:
                    self.detection_buffer.append(detection.lower())
                    
                    if len(self.detection_buffer) == self.min_consistent_frames:
                        if all(x == self.detection_buffer[0] for x in self.detection_buffer):
                            consistent_detection = self.detection_buffer[0]
                            
                            # Handle invalid detection
                            if consistent_detection == "invalid":
                                # Check cooldown for invalid detections
                                if now - self.last_invalid_detection_time > self.invalid_detection_cooldown:
                                    print("10 consecutive invalid detections!")
                                    Thread(target=self._handle_invalid_detection).start()
                            
                            # Handle color detection
                            else:
                                print(f"10 consecutive detections of color: {consistent_detection}")
                                Thread(target=self._handle_confirmed_detection, 
                                      args=(consistent_detection,)).start()
                            
                            self.detection_buffer.clear()
                else:
                    self.detection_buffer.clear()

                # Display status
                time_since_last = time.time() - self.last_reaction_time
                display_frame = frame.copy()
                cv2.rectangle(display_frame, (10, 100), (110, 120), (50, 50, 50), -1)
                if time_since_last < self.cooldown:
                    progress = int(100 * (time_since_last / self.cooldown))
                    cv2.rectangle(display_frame, (10 + progress, 100), (110, 120), (0, 255, 0), -1)
                status = "Ready" if time_since_last >= self.cooldown else "Cooling down"
                cv2.putText(display_frame, status, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                if detection:
                    text = f"{detection} ({confidence:.2f})"
                    cv2.putText(display_frame, text, (10, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Learning Mode", display_frame)

                if cv2.waitKey(1) == ord('q'):
                    break
        except Exception as e:
            print(f"Error during execution: {e}")
            traceback.print_exc()
        finally:
            self.cleanup()

    def _handle_invalid_detection(self):
        """Handle 10 consecutive invalid detections"""
        try:
            print("Invalid piece detected (after 10 frames)!")
            if "invalid" in self.audio_files:
                self.play_audio("invalid")
            
            # Activate LED timer
            self.invalid_led_timer_active = True
            self.invalid_led_timer_start = time.time()
            self.send_to_pi("invalid", 0, correct=False, color="red")
            
            # Update last detection time for cooldown
            self.last_invalid_detection_time = time.time()
            
        except Exception as e:
            print(f"Error in invalid detection: {e}")

    def _handle_confirmed_detection(self, color):
        """Handle 10 consecutive color detections"""
        print(f"Processing confirmed color: {color}")
        self.reaction_in_progress = True
        self.servo_busy = True

        def reaction_thread():
            try:
                self.send_to_pi(color, 0, color="white")
                time.sleep(0.3)
                verify_frame, verify_color, verify_conf = self.process_frame()
                print(f"Verification: {verify_color} ({verify_conf:.2f})")
                if verify_color and verify_color.lower() == color and verify_conf >= 0.7:
                    duration = self.audio_files[color].get_length()
                    self.update_cooldown(duration)
                    self.send_to_pi(color, duration, correct=True)
                    time.sleep(0.2)
                    self.play_audio(color)
                    print(f"Processed: {color}")
                    self.last_reaction_time = time.time()
                    time.sleep(duration + 1.5)
                else:
                    print("Verification failed or color changed.")
                    self.last_reaction_time = time.time()
            except Exception as e:
                print("Exception in reaction_thread:", e)
                self.last_reaction_time = time.time()
            finally:
                try:
                    self.send_to_pi("reset", 0, color="white")
                except Exception as e:
                    print("Failed to reset LED:", e)
                self.servo_last_end_time = time.time()
                self.reaction_in_progress = False
                self.servo_busy = False
        Thread(target=reaction_thread).start()
