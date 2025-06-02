# import torch
# print(f"CUDA Available: {torch.cuda.is_available()}")  # Should output True
# print(f"CUDA Devices: {torch.cuda.device_count()}")    # Should show ≥1


from roboflow import Roboflow
from ultralytics import YOLO

# Initialize Roboflow and download dataset in YOLOv11 format
rf = Roboflow(api_key="pXbF9ik69UC691xELEwF")
project = rf.workspace("ai-concepts-ougid").project("daino_v2")
version = project.version(4)
dataset = version.download("yolov11")

# Load pretrained YOLOv11n model
model = YOLO("yolo11n.pt")

# Train the model (stats will be printed automatically)
model.train(
    data=f"{dataset.location}/data.yaml",
    epochs=50,      # Adjust as needed
    imgsz=640,      # Adjust as needed
    batch=16,       # Adjust based on your hardware
    device=0        # Use 0 for GPU, 'cpu' if no GPU
)
