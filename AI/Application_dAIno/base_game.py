import cv2
from ultralytics import YOLO
import pygame

class BaseGameMode:
    def __init__(self, camera_index=1):
        self.cam = cv2.VideoCapture(camera_index)
        self.model = None  
        self._init_pygame()

    def _init_pygame(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)

    def load_model(self, model_path):
        """Load specific model for child class"""
        self.model = YOLO(model_path)

    def process_frame(self):
        if not self.model:
            raise ValueError("Model not loaded! Call load_model() first")
            
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

    def cleanup(self):
        self.cam.release()
        pygame.quit()
        cv2.destroyAllWindows()
