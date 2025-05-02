# Orka: Orchestrator Kernel for Agents

Orka is a Python framework for building and controlling modular AI agents across multiple platforms including Linux, Android (via Termux), Raspberry Pi, and microcontrollers.

## What is Orka?

Orka (Orchestrator Kernel for Agents) provides a flexible infrastructure for:

- Creating AI agents with configurable personas and behaviors
- Running on various hardware platforms from smartphones to embedded systems
- Supporting multiple LLM providers (currently focusing on Gemini)
- Enabling hardware interaction (audio, camera, sensors) across platforms
- Providing a unified interface regardless of underlying hardware

## A bit of History
- If you will browse the commits, this started as Roastyy, a fun lil bot that I wanna make that can go someowhere look at something and talk and roast it, it was a good idea, but now I realized I can turn this into a good library that I can develop later with more features, and have agents rather than a hardcoded persona that is Roastyy, rip Roastyy, bro got deleted before it even made it through github, but yes, the first commits will be roastyy, so if you wanna explore go ahead!.


## TODO

- [ ] Finish V feature. ( Voice to Voice/Text as of now just TTS/STT is working )
- [ ] Implement P,T together ( photo and TTS/STT both simul)
- [ ] Agentic Framework rather than it being Roastty.
- [ ] Add detailed faliures for what can happen in android/rpi.
- [ ] add vnc and streaming for phones soon

## Getting Started

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/mostlyKIGuess/Orka.git
   cd Orka
   ```

2. **API Key Setup:**

   - Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/)
   - Create a `.env` file in the project root:
     ```dotenv
     GEMINI_API_KEY=YOUR_API_KEY_HERE
     ```

3. **Installation:**

   - **Core Dependencies (All Platforms):**
     ```bash
     pip install -r requirements.txt
     ```

   - **Platform-Specific Setup:**
     - [Android/Termux Setup](#android-with-termux)
     - [Raspberry Pi Setup](#raspberry-pi-setup)
     - [Linux Desktop Setup](#linux-desktop-setup)

## Cross-Platform Support

### Android with Termux

1. Install [Termux](https://f-droid.org/packages/com.termux/) and [Termux:API](https://f-droid.org/packages/com.termux.api/)
2. Install required packages:
   ```bash
   pkg update && pkg upgrade
   pkg install python git termux-api
   pip install -r requirements.txt
   ```
3. Grant necessary permissions (camera, microphone, storage)

PS: You might run into things, I will add those here soon!, but just a google search would be fine

### Raspberry Pi Setup

1. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install espeak python3-pip git portaudio19-dev
   ```
2. For camera support:
   - RPi Camera Module: `pip install picamera2`
   - USB Webcam: `pip install opencv-python`
3. For audio support:
   ```bash
   pip install pyttsx3 SpeechRecognition PyAudio
   ```

### Linux Desktop Setup

1. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install espeak python3-pip git portaudio19-dev
   ```
2. Install audio and camera libraries:
   ```bash
   pip install pyttsx3 SpeechRecognition PyAudio opencv-python
   ```

## Usage

```bash
python main.py
```

Follow the interactive prompts to interact with your agent.

## Configuration

You can customize your agent by modifying `config.py`:

- Change the agent's name and personality
- Configure different LLM models
- Adjust platform-specific settings

## Development

- HEAVY WORK IN DEVELOPMENT RIGHT NOW!!! .Anything can break anytime.

Orka is designed to be extended with additional:
- LLM providers beyond Gemini
- Hardware interactions beyond audio and camera
- Platform support beyond current targets

