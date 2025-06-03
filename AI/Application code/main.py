import cv2
from ultralytics import YOLO

# Load the trained YOLO model (.pt file)
model = YOLO("best.pt")

# Set detection threshold
conf_threshold = 0.5

# Open webcam
cap = cv2.VideoCapture(1)  # Use 0 for default webcam

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Perform detection on the frame
    results = model.predict(source=frame, conf=conf_threshold, verbose=False)

    # Draw bounding boxes, class labels, and confidence
    annotated_frame = results[0].plot()

    # Display the annotated frame
    cv2.imshow("YOLOv8 Detection", annotated_frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release webcam and close windows
cap.release()
cv2.destroyAllWindows()
