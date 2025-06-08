import cv2

class CameraHandler:
    def __init__(self, camera_index=0, width=640, height=480):
        # Use DirectShow backend for Windows to speed up webcam init
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            raise Exception("Could not open webcam.")

        # Set resolution (640x480 recommended for speed and compatibility with my camera)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Set buffer size to 1 to reduce lag
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def get_frame(self):
        # Flush stale frame (improves real-time freshness)
        self.cap.grab()

        # Capture the most recent frame
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Failed to read frame from webcam.")

        return frame  # This will be 640x480

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()

