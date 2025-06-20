import os
import time
import pygame
import cv2
from threading import Thread, Event
import protocol
from base_game import BaseGameMode

class LearningColorsMode(BaseGameMode):
    def __init__(self, audio_path="audio/color learn"):
        super().__init__()
        self.audio_files = self._load_audio(audio_path)
        self.last_reaction_time = 0
        self.base_cooldown = 1.0
        self.cooldown = self.base_cooldown
        self.detection_buffer = []
        self.min_consistent_frames = 4
        self.currently_processing = False
        self.last_invalid_time = 0
        self.invalid_cooldown = 10.0
        self.audio_playing = False
        self.reaction_in_progress = False
        self.servo_busy = False
        self.servo_last_end_time = 0
        self.invalid_state = False
        self.invalid_start_time = 0
        self.invalid_led_reset_duration = 5.0
        self.reaction_done_event = Event()

    def _load_audio(self, path):
        audio_files = {}
        colors = ['red', 'blue', 'green', 'yellow', 'purple', 'invalid']
        for color in colors:
            sound_file = f"{path}/{color}.mp3"
            if os.path.exists(sound_file):
                audio_files[color] = pygame.mixer.Sound(sound_file)
        return audio_files

    def should_react(self, current_color, confidence):
        if not current_color or current_color.lower() == "invalid" or confidence < 0.75:
            return False
        time_since_last = time.time() - self.last_reaction_time
        return time_since_last >= self.cooldown

    def play_audio(self, color):
        if color in self.audio_files and not self.audio_playing:
            self.audio_playing = True
            Thread(target=self._audio_thread, args=(color,)).start()

    def _audio_thread(self, color):
        sound = self.audio_files[color]
        sound.play()
        while pygame.mixer.get_busy():
            time.sleep(0.1)
        self.audio_playing = False

    def update_cooldown(self, audio_duration):
        servo_time = 1.5
        self.cooldown = audio_duration + servo_time + self.base_cooldown

    def send_to_pi(self, color, duration, correct=True, override_color=None):
        if hasattr(self, 'pi_socket') and self.pi_socket:
            try:
                if override_color:
                    cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": override_color})
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

                # Reset invalid state
                if self.invalid_state and (now - self.invalid_start_time > self.invalid_led_reset_duration):
                    print("Red LED timeout reached. Resetting to white.")
                    self.send_to_pi("reset", 0, override_color="white")
                    self.invalid_state = False
                    self.audio_playing = False

                if detection == "invalid" and (now - self.servo_last_end_time < 1.5):
                    continue

                if detection is not None and detection.lower() == "invalid":
                    if (not self.invalid_state
                        and not self.reaction_in_progress
                        and not self.audio_playing
                        and now - self.last_invalid_time > self.invalid_cooldown):
                        print("Invalid piece detected!")
                        if "invalid" in self.audio_files:
                            self.play_audio("invalid")
                        self.send_to_pi("invalid", 0, correct=False, override_color="red")
                        self.invalid_state = True
                        self.invalid_start_time = now
                        self.last_invalid_time = now
                    continue

                current_color = detection if detection is not None else None

                # Reset after invalid if valid color detected
                if self.invalid_state and current_color and confidence >= 0.75:
                    print("Valid color detected after invalid. Resetting state.")
                    self.send_to_pi("reset", 0, override_color="white")
                    self.invalid_state = False
                    self.audio_playing = False

                if not self.currently_processing:
                    if current_color and confidence >= 0.75:
                        self.detection_buffer.append((current_color, confidence))
                        print(f"Buffering: {len(self.detection_buffer)}/{self.min_consistent_frames} frames")
                        if len(self.detection_buffer) >= self.min_consistent_frames:
                            print("Detection buffer filled, starting processing thread.")
                            self.currently_processing = True
                            Thread(target=self._handle_confirmed_detection, args=(current_color,)).start()
                            self.detection_buffer.clear()
                    else:
                        self.detection_buffer.clear()

                time_since_last = time.time() - self.last_reaction_time
                display_frame = frame.copy()
                cv2.rectangle(display_frame, (10, 100), (110, 120), (50, 50, 50), -1)
                if time_since_last < self.cooldown:
                    progress = int(100 * (time_since_last / self.cooldown))
                    cv2.rectangle(display_frame, (10 + progress, 100), (110, 120), (0, 255, 0), -1)
                status = "Ready" if time_since_last >= self.cooldown else "Cooling down"
                cv2.putText(display_frame, status, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                if current_color:
                    text = f"{current_color} ({confidence:.2f})"
                    cv2.putText(display_frame, text, (10, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Learning Mode", display_frame)

                if cv2.waitKey(1) == ord('q'):
                    break
        finally:
            self.cleanup()

    def _handle_confirmed_detection(self, color):
        print(f"Starting processing for color: {color}")
        self.reaction_in_progress = True
        self.servo_busy = True

        def reaction_thread():
            try:
                self.send_to_pi(color, 0, override_color="white")
                time.sleep(0.3)
                verify_frame, verify_color, verify_conf = self.process_frame()
                print(f"Verification: {verify_color} ({verify_conf:.2f})")
                if verify_color == color and verify_conf >= 0.7:
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
                    self.send_to_pi("reset", 0, override_color="white")
                except Exception as e:
                    print("Failed to reset LED:", e)
                self.servo_last_end_time = time.time()
                print("Finished processing.")
                self.currently_processing = False
                self.reaction_in_progress = False
                self.servo_busy = False
                self.invalid_state = False

        Thread(target=reaction_thread).start()
