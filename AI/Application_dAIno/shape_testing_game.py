import cv2
from ultralytics import YOLO
import pygame
import time
import os
import random
import protocol

class ShapeTestingMode:
    def __init__(self, audio_path="audio/shape test", camera_index=1, model_path='shape_model.pt'):
        self.audio_path = audio_path
        self.shapes = ['circle', 'square', 'triangle', 'star', 'pentagon']
        self.cam = cv2.VideoCapture(camera_index)
        self.model = YOLO(model_path)
        self._init_pygame()
        self.last_reaction_time = 0
        self.base_cooldown = 1.0
        self.cooldown = self.base_cooldown
        self.audio_playing = False
        self.servo_busy = False
        self.invalid_state = False
        self.invalid_start_time = 0
        self.invalid_led_reset_duration = 5.0
        self.audio_files = self._index_audio_files(audio_path)
        self.pi_socket = None  # Set externally
        self.shape_counts = {shape: 5 for shape in self.shapes}

    def _init_pygame(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)

    def _index_audio_files(self, path):
        audio_files = {"find": {}, "reject": {}, "try_again": {}}
        for shape in self.shapes:
            audio_files["find"][shape] = [
                os.path.join(path, f) for f in os.listdir(path)
                if f.startswith(f"Find {shape}")
            ]
            audio_files["try_again"][shape] = [
                os.path.join(path, f) for f in os.listdir(path)
                if f.startswith(f"Try again {shape}")
            ]
            reject_file = os.path.join(path, f"Reject {shape}.mp3")
            if os.path.exists(reject_file):
                audio_files["reject"][shape] = reject_file
        reject_invalid = os.path.join(path, "Reject invalid.mp3")
        if os.path.exists(reject_invalid):
            audio_files["reject"]["invalid"] = reject_invalid
        return audio_files

    def play_random_audio(self, category, shape):
        if category in ("find", "try_again"):
            files = self.audio_files[category].get(shape, [])
            if not files:
                return
            audio_file = random.choice(files)
        elif category == "reject":
            audio_file = self.audio_files["reject"].get(shape)
            if not audio_file:
                return
        else:
            return

        sound = pygame.mixer.Sound(audio_file)
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.wait(100)

    def play_startup_audio(self):
        startup_audio = os.path.join(self.audio_path, "Shape test start.mp3")
        if os.path.exists(startup_audio):
            sound = pygame.mixer.Sound(startup_audio)
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.wait(100)

    def play_end_audio(self):
        end_audio = os.path.join(self.audio_path, "End shape test game.mp3")
        if os.path.exists(end_audio):
            sound = pygame.mixer.Sound(end_audio)
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.wait(100)

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

    def send_to_pi(self, shape, duration, correct=True, color=None):
        if self.pi_socket:
            try:
                if color:
                    cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": color})
                elif correct:
                    cmd = protocol.create_command(protocol.LEARNING_SHAPE, {"shape": shape, "duration": duration})
                else:
                    cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": "red"})
                self.pi_socket.sendall(cmd)
            except Exception as e:
                print("Error sending to Pi:", e)

    def run(self):
        print("Starting Shape Testing mode...")
        self.play_startup_audio()
        try:
            while True:
                available_shapes = [shape for shape, count in self.shape_counts.items() if count > 0]
                if not available_shapes:
                    print("All shapes have been swallowed. Ending test.")
                    self.play_end_audio()
                    break

                target_shape = random.choice(available_shapes)
                print(f"Please insert a {target_shape}!")
                self.play_random_audio("find", target_shape)

                last_detection = None
                last_detection_type = None

                while True:
                    frame, detection, conf = self.process_frame()
                    if frame is None:
                        continue
                    display_frame = frame.copy()
                    cv2.putText(display_frame, f"Find: {target_shape}", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)

                    # Handle invalid
                    if detection is not None and detection.lower() == "invalid":
                        if last_detection_type != "invalid":
                            print("Invalid piece detected!")
                            self.send_to_pi("invalid", 0, correct=False)  # LED red, no servo
                            cv2.putText(display_frame, "Invalid piece!", (10, 120),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2)
                            cv2.imshow("Testing Mode", display_frame)
                            self.play_random_audio("reject", "invalid")
                            time.sleep(1)
                            self.send_to_pi("reset", 0, color="white")
                            last_detection_type = "invalid"
                        continue

                    # Handle correct or incorrect shape
                    if detection and conf >= 0.75:
                        detected_shape = detection
                        if detected_shape == target_shape:
                            if last_detection_type != "correct":
                                print("Correct!")
                                self.send_to_pi(target_shape, 1.0, correct=True)
                                self.shape_counts[target_shape] -= 1
                                time.sleep(0.2)
                                # Wait for slot to be empty
                                while True:
                                    frame2, detection2, conf2 = self.process_frame()
                                    if detection2 is None or conf2 < 0.75:
                                        break
                                    time.sleep(0.1)
                                self.send_to_pi("reset", 0, color="white")  # Reset LED to white after correct
                                last_detection_type = "correct"
                                break
                        else:
                            if last_detection_type != "incorrect" or last_detection != detected_shape:
                                print("Incorrect!")
                                self.send_to_pi("wrong", 0, correct=False)  # LED red, no servo
                                self.play_random_audio("reject", detected_shape)
                                time.sleep(1)
                                self.send_to_pi("reset", 0, color="white")
                                self.play_random_audio("try_again", target_shape)
                                last_detection_type = "incorrect"
                                last_detection = detected_shape
                            continue

                    cv2.imshow("Testing Mode", display_frame)
                    if cv2.waitKey(1) == ord('q'):
                        return

                self.last_reaction_time = time.time()
                time.sleep(2)
        finally:
            self.cam.release()
            pygame.quit()
            cv2.destroyAllWindows()
