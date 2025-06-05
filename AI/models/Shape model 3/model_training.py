import os
from ultralytics import YOLO

SAVE_DIR = "my_custom_runs/shape_model"

def main():
    model = YOLO("yolo11n.pt")  

    # Train the model
    model.train(
        data="C:\Users\natal\Documents\2024-2025\Semester 2\Project One\Anotated Datasets\DAINO SHAPES.v6i.yolov11", 
          # Path to your dataset configuration
        epochs=400,
        verbose=True,
        device = 0,
        patience=150,
        batch=32,
        project="my_custom_runs",
        name="shape_model"
    )
    print("done training")

    weight_path = f"{SAVE_DIR}/weights/best.pt"
    
    if not os.path.exists(weight_path):
        print(f"Warning: {weight_path} not found. Searching for latest weights...")

        paths = sorted(
            [p for p in os.listdir("my_custom_runs") if p.startswith("shape_model_2")],
            reverse=True
        )

        if paths:
            weight_path = f"my_custom_runs/{paths[0]}/weights/best.pt"
            print(f"Using weights from: {weight_path}")
        else:
            print("Error: No weights found!")
            return

    # Load the best trained model
    best_model = YOLO(weight_path)

    # Validate on the validation set
    print("\nRunning Validation on Validation Set...")
    best_model.val(task="detect", data="C:\Users\natal\Documents\2024-2025\Semester 2\Project One\Anotated Datasets\DAINO SHAPES.v6i.yolov11")

    # Test on a separate test set
    print("\nRunning Testing on Test Set...")
    best_model.val(task="detect", data="C:\Users\natal\Documents\2024-2025\Semester 2\Project One\Anotated Datasets\DAINO SHAPES.v6i.yolov11", split="test")

    # Export model to TensorFlow Lite format
    print("\nExporting Model to TFLite...")
    best_model.export(format="tflite")

if __name__ == '__main__':
    main()