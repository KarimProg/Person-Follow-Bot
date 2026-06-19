# Person-Follow-Bot

A real-time person-following robot project that uses computer vision and control logic to detect a person from an RTSP camera stream and send movement commands to a robot/controller.

## Overview

The project:

- Opens a low-latency RTSP video stream using OpenCV + GStreamer
- Runs YOLOv8 person detection and tracking
- Uses a centralization/PID control loop to compute movement commands
- Sends speed commands to the robot via the `Control` class
- Supports a simple text-file command mode with `command.txt`

## Features

- **RTSP input** with a GStreamer pipeline tuned for low latency
- **Person detection** using Ultralytics YOLOv8
- **Tracking** with `botsort.yaml`
- **Centering logic** to keep the target person aligned in frame
- **PID control** for smoother movement
- **Manual state switching** between `follow` and `stop` using `command.txt`

## How it works

The main loop:

1. Reads frames from the RTSP stream
2. Detects and tracks class `0` objects (people)
3. Computes movement offsets using `Centralization`
4. Reads `command.txt` every 0.5 seconds
5. If the command is `stop`, it zeroes movement output
6. Sends the resulting speeds through `Control.post_speeds()`

## Requirements

This project depends on:

- Python 3.9+
- OpenCV
- Ultralytics
- A working GStreamer installation
- The `movement` package/modules used by the project:
  - `movement.Centralization_class`
  - `movement.Control_class`
  - `movement.PID`

You will also need a YOLOv8 model file at:

- `models/yolov8m.pt`

## Installation

Example setup:

```bash
pip install opencv-python ultralytics
```

If your system does not already have GStreamer, install it through your OS package manager.

## Configuration

Before running the project, check these values in `main.py`:

- `rtsp_url` — your camera stream address
- `width` / `height` — the desired frame size
- `models/yolov8m.pt` — the detection model path

## Run

```bash
python main.py
```

## Command control

The file `command.txt` is used to control the state of the bot.

Supported values:

- `follow` — enable person following
- `stop` — stop all motion

Example:

```txt
follow
```

## Notes

- The script currently targets only class `0` from YOLO, which is the person class.
- Press `q` in the OpenCV window to quit.
- If the RTSP stream cannot be opened, the script prints an error message.

## Project structure

```text
.
├── main.py
├── README.md
├── command.txt
├── models/
│   └── yolov8m.pt
└── movement/
    ├── Centralization_class.py
    ├── Control_class.py
    └── PID.py
```

## License

Add a license here if you want to publish or share the project.
