from ultralytics import YOLO
import cv2
from utils.helpers import get_random_encouragement

# resized = cv2.resize(frame, (640, 640))
# results = self.model(resized)
class AIHandler:
    def __init__(self):
        self.color_model = YOLO("models/color_model.pt")
        self.shape_model = YOLO("models/shape_model.pt")

    def detect(self, image, mode):
        if mode == "color":
            return self.detect_color(image)
        else:
            return self.detect_shape(image)

    def detect_color(self, image):
        results = self.color_model(image)
        return self.extract_top_label(results)

    def detect_shape(self, image):
        results = self.shape_model(image)
        return self.extract_top_label(results)

    def extract_top_label(self, results):
        """
        Get the class name of the highest-confidence detection
        """
        names = results[0].names  # dict of {class_id: class_name}
        if results[0].boxes and len(results[0].boxes.cls) > 0:
            class_id = int(results[0].boxes.cls[0])
            return names[class_id]
        else:
            return "none"
    
    def random_encouragement(self):
        filename = get_random_encouragement()
        audio_player.play(filename)



