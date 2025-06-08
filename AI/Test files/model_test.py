import cv2
from ultralytics import YOLO
import time

# Initialize YOLO model
model = YOLO('shape_model.pt')  # Path to your YOLO11 model

# Initialize camera
cap = cv2.VideoCapture(1)  

while True:
    ret, frame = cap.read()
    if not ret:
        print('Failed to capture image')
        continue

    # Run YOLO detection
    results = model(frame)  # This returns a list of Results objects

    for result in results:  # Iterate over the list
        boxes = result.boxes  # Boxes object for bounding box outputs
        names = result.names  # Dictionary of class names

        detected_classes = []
        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls_id = int(box.cls)
                label = names[cls_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                detected_classes.append(label)
        print('Detected:', detected_classes)

    # Show the camera view
    cv2.imshow('Camera View', frame)

    # Wait for 1 second or until 'q' is pressed
    if cv2.waitKey(1000) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
