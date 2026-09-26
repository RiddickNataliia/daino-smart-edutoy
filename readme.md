# dAIno — AI-Powered Educational Companion Toy

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Raspberry%20Pi-5-A22846?logo=raspberrypi&logoColor=white" alt="Raspberry Pi" />
  <img src="https://img.shields.io/badge/Ultralytics-YOLO-00FFFF?logo=yolo&logoColor=black" alt="YOLO" />
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white" alt="PyTorch" />
  <img src="https://img.shields.io/badge/OpenCV-5C3EE8?logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/Bluetooth%20LE-GATT-0082FC?logo=bluetooth&logoColor=white" alt="Bluetooth LE" />
  <img src="https://img.shields.io/badge/Pygame-audio-000000?logo=pygame&logoColor=white" alt="Pygame" />
  <img src="https://img.shields.io/badge/GPIO-WS2812%20%2B%20Servo-8A2BE2" alt="GPIO" />
</p>

An interactive dinosaur toy that teaches young children colors and shapes: a child places a
physical block in dAIno's mouth, a camera and a fine-tuned YOLO model identify its color or shape,
and dAIno reacts in real time with LED colors, a chomping servo-driven mouth, and spoken audio
feedback. Conceived, designed, and built end-to-end (toy body, hardware assembly, computer vision,
control software, and voice prompts) as part of an Applied Computer Science project at Howest, and
recognized with a prize on Instructables.

## How it works

dAIno is split across two cooperating applications:

- **AI app** (`AI/Application_dAIno/`) — runs on a laptop connected to a USB camera pointed at the
  toy's mouth. It captures frames, runs a fine-tuned YOLO model to detect the color or shape of the
  inserted block, drives the game logic (learning mode, testing mode with streak scoring, bedtime
  mode with lullabies), and plays matching audio feedback.
- **Pi app** (`RPi/Application_dAIno/`) — runs on a Raspberry Pi 5 inside the toy. It receives JSON
  commands over a TCP socket from the AI app and drives the physical hardware: a servo that opens
  and closes the mouth, and a WS2812 LED strip that lights up in the detected color.

```
 USB camera            AI app (laptop)                    Pi app (Raspberry Pi 5, inside toy)
 ┌─────────┐    frame   ┌───────────────────────┐  TCP/JSON  ┌─────────────────────────┐
 │  camera │ ─────────▶ │ YOLO detection         │ ─────────▶ │ DinoController           │
 └─────────┘            │ game logic + scoring   │  socket    │  • servo → mouth action  │
                         │ audio (pygame)         │  :8888     │  • WS2812 LED strip      │
                         └───────────────────────┘            └─────────────────────────┘
```

Two learn/test games are implemented:

| Mode | Description |
|---|---|
| **Color learning** | Child inserts a colored block; dAIno announces the color, lights up to match, and "chomps" |
| **Color testing** | dAIno asks for a specific color; correct/incorrect answers are tracked as a streak with a saved best score |
| **Shape learning** | Same as color learning, for shapes (circle, square, triangle, star, pentagon) |
| **Shape testing** | Same as color testing, for shapes |
| **Bedtime mode** | Plays a rotating set of lullabies for a configurable duration |

## Repository structure

```
AI/
├── Application_dAIno/       # Main AI app — game manager, game modes, protocol, trained models, audio
│   ├── models/               # Fine-tuned YOLO weights (color_model.pt, shape_model.pt)
│   └── audio/                # Spoken prompts for each game mode
├── Dataset collection code/  # Script used to capture training images from the toy's camera
└── Intro_test/               # Early BLE connectivity proof-of-concept (course kickoff exercise)

RPi/
├── Application_dAIno/        # Production Pi controller — servo + LED strip, TCP command server
├── Application_Pi/           # Earlier, simpler GPIO socket-server prototype
├── ble_utils/                 # BLE GATT server utilities (from the course kickoff exercise)
└── app.py                    # BLE + LCD demo app from the course kickoff exercise

Docs/                          # Course setup guides (RPi imaging, config, deployment) and feedback log
```

## Tech stack

- **Computer vision:** [Ultralytics YOLO](https://github.com/ultralytics/ultralytics), OpenCV, PyTorch — two models fine-tuned on a self-collected, self-annotated dataset of the toy's color and shape blocks
- **Hardware control:** Raspberry Pi GPIO (servo motor for the mouth), WS2812 addressable LED strip (`rpi5-ws2812`)
- **Communication:** TCP sockets with a small JSON command protocol between the AI app and the Pi; Bluetooth LE GATT (`bleak`, BlueZ) explored during the course kickoff phase
- **Audio:** `pygame.mixer` for pre-recorded voice prompts and lullabies
- **Dataset collection:** custom OpenCV capture script for gathering training images directly from the toy's camera

## Hardware

- Raspberry Pi 5
- USB camera (mounted to view the toy's mouth)
- Servo motor (mouth open/close mechanism)
- WS2812 addressable LED strip
- 3D-printed / hand-built dinosaur body

## Running it

**Pi side** (inside the toy, on the Raspberry Pi):

```bash
cd RPi
pip install -r requirements.txt
python Application_dAIno/controller.py
```

**AI side** (on a laptop with a USB camera, on the same network as the Pi):

```bash
cd AI/Application_dAIno
pip install -r ../Intro_test/requirements.txt   # ultralytics, opencv-python, torch, etc.
python game_manager.py
```

Update the Pi's IP address in `game_manager.py` (`pi_ip`) to match your Raspberry Pi.

## Background

Built solo — idea, dinosaur body design and physical build, hardware assembly, dataset collection
and annotation, YOLO model training, Python control logic, and voice prompts — as an Applied
Computer Science project at Howest. Despite being a rough first prototype (papier-mâché body, an
exposed Raspberry Pi), it was durable and engaging enough that children played with it for extended
periods, and it drew interest from a special needs school. The project won a prize on Instructables.
