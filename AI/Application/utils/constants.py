# Supported modes
MODE_COLOR = "color"
MODE_SHAPE = "shape"
MODE_COMBINED = "combined"  # optional future expansion

# Supported shapes and colors (must match your YOLO training class names)
SHAPES = ["circle", "square", "triangle", "pentagon"]
COLORS = ["red", "blue", "green", "yellow", "purple"]

# Audio folders
AUDIO_DIRS = {
    "start": "audio/start",
    "names": {
        "shapes": "audio/names/shapes",
        "colors": "audio/names/colors"
    },
    "requests": "audio/requests",
    "rejections": "audio/rejections",
    "success": "audio/success",
    "encouragement": "audio/encouragement"
}