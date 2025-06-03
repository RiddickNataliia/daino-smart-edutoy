import cv2
import os


# Create output folder if it doesn't exist
output_folder = "captured_images"
os.makedirs(output_folder, exist_ok=True)

# Open webcam (0 = default camera)
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Error: Cannot open webcam")
    exit()

img_counter = 0

print("Press SPACE to capture, ESC to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    cv2.imshow("Webcam", frame)

    key = cv2.waitKey(1)
    if key % 256 == 27:  # ESC key
        print("Exiting...") 
        break
    elif key % 256 == 32:  # Spacebar
        img_name = f"{output_folder}/image_{img_counter:02d}.jpg"
        cv2.imwrite(img_name, frame)
        print(f"Saved: {img_name}")
        img_counter += 1

cap.release()
cv2.destroyAllWindows()

