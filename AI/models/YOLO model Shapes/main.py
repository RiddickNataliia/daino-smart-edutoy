#get dataset
# from roboflow import Roboflow
# rf = Roboflow(api_key="pXbF9ik69UC691xELEwF")
# project = rf.workspace("ai-concepts-ougid").project("daino_v2")
# version = project.version(4)
# dataset = version.download("yolov11")
          
                
#train and validate          

import os
from ultralytics import YOLO

SAVE_DIR = "new_custom_runs/shapes_model_v11n"

def main():
    model = YOLO("yolo11n.pt")  

    # Train the model
    model.train(
        data="C:/Users/natal/Documents/2024-2025/Semester 2/Project One/Anotated Datasets/DAINO SHAPES.v6-shapes_2.yolov11/data.yaml",  # Path to dataset configuration
        epochs=400,
        patience=150,
        device=0,
        verbose=True,
        batch=32,
        project="new_custom_runs",
        name="shapes_model_v11n"
    )
    print("done training")

    weight_path = f"{SAVE_DIR}/weights/best.pt"
    
    if not os.path.exists(weight_path):
        print(f"Warning: {weight_path} not found. Searching for latest weights...")

        paths = sorted(
            [p for p in os.listdir("new_custom_runs") if p.startswith("shape_model_v11")],
            reverse=True
        )

        if paths:
            weight_path = f"new_custom_runs/{paths[0]}/weights/best.pt"
            print(f"Using weights from: {weight_path}")
        else:
            print("Error: No weights found!")
            return

    # Load the best trained model
    best_model = YOLO(weight_path)

    # Validate on the validation set
    print("\nRunning Validation on Validation Set...")
    best_model.val(task="detect", data="C:/Users/natal/Documents/2024-2025/Semester 2/Project One/Anotated Datasets/DAINO SHAPES.v6-shapes_2.yolov11/data.yaml")

    # Test on a separate test set
    print("\nRunning Testing on Test Set...")
    best_model.val(task="detect", data="C:/Users/natal/Documents/2024-2025/Semester 2/Project One/Anotated Datasets/DAINO SHAPES.v6-shapes_2.yolov11/data.yaml", split="test")

    # Export model to TensorFlow Lite format
    print("\nExporting Model to TFLite...")
    best_model.export(format="tflite")

if __name__ == '__main__':
    main()






# separate testing
# import os
# from ultralytics import YOLO

# # Define path to the YAML file
# data_yaml_path = os.path.abspath("bee-analytics-3/data.yaml")  # Get full path
# print(f"Using data file: {data_yaml_path}")  # Debugging step

# # Load your trained model
# model_path = "my_custom_runs/bee_model_v12/weights/best.pt"  # Update this if needed
# model = YOLO(model_path)  # Load trained YOLO model

# # Run validation on the test set
# results = model.val(data=data_yaml_path, split="test")


# check with videos

# import cv2
# from ultralytics import YOLO

# # Path to your model weights
# model_path = "my_custom_runs/bee_model_v12/weights/best.pt"
# model = YOLO(model_path)  # Load the trained model

# # Path to your input video
# video_path = 'videos/bees.mp4'  # Replace with your video file path

# # Open video using OpenCV
# cap = cv2.VideoCapture(video_path)

# # Check if the video was opened successfully
# if not cap.isOpened():
#     print("Error: Could not open video.")
#     exit()

# # Set up video writer to save the output video
# output_video_path = 'output_video_6.mp4'  # Path to save the output video
# fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' for .mp4
# frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
# out = cv2.VideoWriter(output_video_path, fourcc, 30.0, (frame_width, frame_height))

# while True:
#     ret, frame = cap.read()  # Read each frame
#     if not ret:
#         break  # Exit the loop when the video ends

#     # Perform inference (object detection) on the frame
#     results = model(frame)  # The model will automatically detect objects in the frame

#     # The results are returned as a list, so we access the first (and only) result in this case
#     result = results[0]

#     # Render the results (e.g., bounding boxes, class labels)
#     annotated_frame = result.plot()  # Annotated frame with detections

#     # Save the annotated frame to the output video
#     out.write(annotated_frame)

# # Release the video capture and writer objects, then close all OpenCV windows
# cap.release()
# out.release()

# print(f"Output video saved to {output_video_path}")




