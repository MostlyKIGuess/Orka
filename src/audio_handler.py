import logging
import subprocess
import config 

try:
    import pyttsx3
except ImportError:
    logging.info(
        "pyttsx3 library not found. RPi/Desktop TTS will not work unless installed."
    )
    pyttsx3 = None  # type: ignore

try:
    import speech_recognition as sr
except ImportError:
    logging.info(
        "SpeechRecognition library not found. RPi/Desktop STT will not work unless installed."
    )
    sr = None  # type: ignore
try:
    import pyaudio  # noqa: F401
    logging.debug("PyAudio library found.")
    pyaudio_available = True
except ImportError:
    # Don't log error here, only if STT is attempted on relevant platform
    pyaudio_available = False
    logging.debug("PyAudio library not found. Microphone input might require it on Linux/RPi.")



# TTS 

def _speak_termux(text):
    """Uses Termux:API for TTS."""
    logging.info("Attempting TTS via Termux:API...")
    try:
        # Use -e com.google.android.tts for Google TTS engine if default is bad
        command = ["termux-tts-speak", text]
        logging.info(
            f"Running Termux TTS command: {' '.join(command)}"
        )  # Log the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,  # Add timeout
        )
        if result.returncode != 0:
            # Log stdout and stderr for debugging
            logging.warning(
                f"Termux TTS command finished with code {result.returncode}. "
                f"Stdout: '{result.stdout.strip()}'. Stderr: '{result.stderr.strip()}'"
            )
            # Check common errors
            if (
                "termux-api" in result.stderr.lower()
                and "not found" in result.stderr.lower()
            ):
                logging.error(
                    "Is the Termux:API package installed (`pkg install termux-api`)?"
                )
            elif "timed out" in result.stderr.lower():
                logging.error(
                    "Termux:API command timed out. Is the Termux:API app running and permissions granted?"
                )
            return False  # Explicitly return False on error
        else:
            logging.info(
                f"Termux TTS command executed successfully. Stdout: '{result.stdout.strip()}'"
            )
            return True
    except FileNotFoundError:
        logging.error(
            "`termux-tts-speak` command not found. Is Termux:API installed (`pkg install termux-api`)?"
        )
        return False
    except subprocess.TimeoutExpired:
        logging.error(
            "Termux TTS command timed out. Is the Termux:API app running and responsive?"
        )
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during Termux TTS: {e}")
        return False


def _speak_rpi_desktop(text):
    """Uses pyttsx3 for TTS on RPi/Desktop."""
    if pyttsx3 is None:
        logging.error("pyttsx3 library not available for TTS.")
        return False
    logging.info("Attempting TTS via pyttsx3...")
    try:
        # Check if aplay is available on Linux systems
        if config.PLATFORM == "linux" or config.PLATFORM == "rpi":
            try:
                subprocess.run(["which", "aplay"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                logging.error("aplay command not found. Install with: sudo apt-get install alsa-utils or wtv is there in your distro")
                return False

        engine = pyttsx3.init()
        # Optional: Adjust properties
        # voices = engine.getProperty('voices')/
        # engine.setProperty('voice', voices[0].id) # Change voice if needed
        # engine.setProperty('rate', 150) # Speed percent (can go over 100)
        # engine.setProperty('volume', 0.9) # Volume 0-1
        engine.say(text)
        engine.runAndWait()
        engine.stop()  # Clean up engine resources
        logging.info("pyttsx3 TTS executed successfully.")
        return True
    except Exception as e:
        logging.error(f"An error occurred during pyttsx3 TTS: {e}")
        return False


def _speak_linux_fallback(text):
    """Uses system commands for TTS when pyttsx3 isn't available."""
    logging.info("Attempting TTS via Linux system commands...")

    # Try espeak first (widely available)
    try:
        import subprocess

        subprocess.run(["espeak", text], check=True)
        logging.info("espeak TTS executed successfully.")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logging.warning("espeak not available or failed.")

    # Try festival as fallback
    try:
        with open("/tmp/roastyy_tts.txt", "w") as f:
            f.write(text)
        subprocess.run(["festival", "--tts", "/tmp/roastyy_tts.txt"], check=True)
        logging.info("festival TTS executed successfully.")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logging.warning("festival not available or failed.")

    logging.error("All Linux TTS fallbacks failed.")
    return False


def speak(text, agent_name="Agent"):
    """Speaks the given text using the appropriate platform method."""
    if not text:
        logging.warning("Speak function called with empty text.")
        return

    success = False
    logging.debug(f"Speak request for platform '{config.PLATFORM}': '{text[:50]}...'")

    if config.PLATFORM == "termux":
        success = _speak_termux(text)
    elif config.PLATFORM in ["rpi", "linux", "macos", "windows"]:
        if pyttsx3 is not None:
            success = _speak_rpi_desktop(text)
        if not success and config.PLATFORM == "linux":
            logging.info("pyttsx3 failed or unavailable, trying Linux command fallback...")
            success = _speak_linux_fallback(text)
    else:
        logging.warning(f"TTS not implemented for platform: {config.PLATFORM}")

    # Fallback to printing if all methods failed
    if not success:
        # Use agent_name in fallback print
        print(f"\n[{agent_name} (TTS Fallback)]: {text}\n")
        logging.info("TTS failed, fell back to printing text.")









# SST


def _listen_termux():
    """Uses Termux:API for STT. Often less reliable."""
    logging.info("Attempting STT via Termux:API...")
    print("Listening via Termux... Speak clearly.")
    try:
        # Termux command waits for speech and prints the result
        command = ["termux-speech-to-text"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        recognized_text = result.stdout.strip()
        if recognized_text:
            logging.info(f"Termux STT recognized: '{recognized_text}'")
            return recognized_text
        else:
            logging.warning("Termux STT returned empty result.")
            return None
    except FileNotFoundError:
        logging.error(
            "`termux-speech-to-text` command not found. Is Termux:API installed?"
        )
        return None
    except subprocess.CalledProcessError as e:
        # This might happen if user doesn't speak or there's an error
        logging.error(f"Termux STT command failed: {e.stderr}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during Termux STT: {e}")
        return None


def _listen_rpi_desktop():
    """Uses SpeechRecognition library for STT on RPi/Desktop."""
    if sr is None:
        logging.error("SpeechRecognition library not available for STT.")
        return None

    r = sr.Recognizer()
    # Optional: Adjust energy threshold dynamically
    # r.dynamic_energy_threshold = True
    # r.pause_threshold = 0.8 # seconds of non-speaking audio before phrase is considered complete
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True
    r.pause_threshold = 2  # after these many seconds of pause, phrase completed
    mic_list = sr.Microphone.list_microphone_names()
    logging.debug(f"Available microphones: {mic_list}")
    # You might need to specify device_index if default doesn't work
    # mic = sr.Microphone(device_index=?)

    # Use the specified device index if available
    mic_kwargs = {}
    if hasattr(config, "MIC_DEVICE_INDEX") and config.MIC_DEVICE_INDEX is not None:
        mic_kwargs["device_index"] = config.MIC_DEVICE_INDEX
    with sr.Microphone(**mic_kwargs) as source:
        print("Listening via Microphone... Speak now!")
        try:
            # Add ambient noise adjustment with longer duration
            print("Adjusting for ambient noise... (wait)")
            r.adjust_for_ambient_noise(source)
            logging.info("Adjusted for ambient noise. Listening...")

            audio = r.listen(
                source, timeout=10, phrase_time_limit=15
            )  # Increased timeouts for reliability

            logging.info("Audio captured, attempting recognition...")
        except sr.WaitTimeoutError:
            logging.warning("No speech detected within timeout.")
            print("(No speech detected)")
            return None
        except Exception as e:
            logging.error(f"Error capturing audio: {e}")
            return None

    try:
        # Recognize speech using Google Web Speech API (requires internet)
        recognized_text = r.recognize_google(audio)
        logging.info(f"Google Web Speech recognized: '{recognized_text}'")
        print(f"(Heard: {recognized_text})")  # Give user feedback
        return recognized_text

        # --- Alternative: Offline recognition using Sphinx (requires setup) ---
        # Need: pip install pocketsphinx
        # recognized_text = r.recognize_sphinx(audio)
        # logging.info(f"Sphinx recognized: {recognized_text}")
        # return recognized_text
        # --------------------------------------------------------------------

    except sr.UnknownValueError:
        logging.warning("Google Web Speech could not understand audio.")
        print("(Could not understand audio)")
        return None
    except sr.RequestError as e:
        logging.error(f"Could not request results from Google Web Speech service; {e}")
        print("(Speech service error)")
        return None
    # except Exception as e: # Catch PocketSphinx errors if using offline
    #     logging.error(f"Error during Sphinx recognition: {e}")
    #     return None


def listen(agent_name="Agent"):
    """Listens for audio input using the appropriate platform method."""
    recognized_text = None
    logging.debug(f"Listen request for platform '{config.PLATFORM}'")

    if config.PLATFORM == "termux":
        recognized_text = _listen_termux()
    elif config.PLATFORM in ["rpi", "linux", "macos", "windows"]:
        recognized_text = _listen_rpi_desktop()
    else:
        logging.warning(f"STT not implemented for platform: {config.PLATFORM}")
        print(f"Speech input not supported on this platform ({config.PLATFORM}).")

    # Fallback to Text Input
    if recognized_text is None:
        logging.info("STT failed or not supported, falling back to text input.")
        try:
            # Use agent_name in the prompt
            user_input = input(f"[{agent_name} waiting] You: ")
            return user_input.strip().lower() # Return lowercased and stripped
        except EOFError:
            logging.info("EOF detected during text input.")
            return "quit" # Treat EOF as quit
        except KeyboardInterrupt:
             logging.info("KeyboardInterrupt detected during text input.")
             raise # Re-raise to be caught by main loop
        except Exception as input_e:
             logging.exception(f"Error during text input fallback: {input_e}")
             return None # Indicate input failure

    return recognized_text.lower() # Return successfully recognized text (lowercased)