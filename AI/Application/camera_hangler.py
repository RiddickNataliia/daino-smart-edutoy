import cv2

class CameraHandler:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise Exception("Could not open webcam.")

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Failed to read frame from webcam.")
        return frame

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
