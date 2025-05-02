import logging
import sys
import time

# --- Setup Logging FIRST ---
# Import utils early to set up logging before other modules might log.
try:
    from src import utils

    utils.setup_logging()
except ImportError:
    # Basic fallback logging if utils fails for some reason
    import logging

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.warning("Could not import src.utils. Using basic logging.")

# --- Import other components AFTER logging is set up ---
try:
    import config
    from src import audio_handler, gemini_handler, image_handler
except ImportError as e:
    logging.error(f"Failed to import necessary modules: {e}")
    logging.error(
        "Please ensure all files exist in the 'src' directory and required packages are installed."
    )
    sys.exit(1)
except ValueError as e:  # Catch config errors like missing API key
    logging.error(f"Configuration error: {e}")
    sys.exit(1)


def display_intro():
    """Displays the welcome message and instructions."""
    print("\n" + "=" * 40)
    print(f" Welcome to {config.BOT_NAME}! ")
    print(" I'm here to roast... with style (and AI).")
    print("=" * 40)
    print("Options:")
    print("  P - Roast a Photo (takes picture or asks for path)")
    print("  T - Start Roasting (Text/Voice conversation)")
    # print("  V - Start Roasting (Voice input first - if supported)") # Combine T/V for simplicity now
    print("  Q - Quit")
    print("=" * 40)


def handle_photo_roast():
    """Handles the process of getting an image and roasting it."""
    print("\n--- Photo Roast ---")
    audio_handler.speak("Alright, show me what you got! Let's capture an image.")
    image_path = image_handler.get_image()

    if image_path:
        logging.info(f"Image obtained: {image_path}")
        audio_handler.speak("Got the image. Warming up my roasting circuits...")
        print("Processing image with Gemini...")
        roast = gemini_handler.get_roast_from_image(image_path)
        print(f"\n{config.BOT_NAME}: {roast}")
        audio_handler.speak(roast)
        # Optionally remove the temp image after use
        # if image_path == config.TEMP_IMAGE_PATH:
        #     try:
        #         os.remove(image_path)
        #         logging.info(f"Removed temporary image: {image_path}")
        #     except OSError as e:
        #         logging.error(f"Error removing temporary image {image_path}: {e}")
        return True  # Indicate success to potentially start chat
    else:
        logging.warning("Failed to get an image for roasting.")
        error_msg = "Couldn't get an image. Can't roast thin air!"
        print(f"\n{config.BOT_NAME}: {error_msg}")
        audio_handler.speak(error_msg)
        return False  # Indicate failure


def conversation_loop(chat_session):
    """Handles the ongoing text/voice conversation."""
    print("\n--- Conversation Mode ---")
    print(
        "Type your message or speak when 'Listening...'. Type 'quit' or 'exit' to stop."
    )
    print(
        "Additional commands: 'history' to view chat history, 'clear' to clear history"
    )
    audio_handler.speak("Okay, let's chat. What's on your mind?")

    while True:
        # Get input (handles STT or text fallback)
        user_input = audio_handler.listen()

        if (
            not user_input
        ):  # Handle cases where listen() returns None (e.g., timeout, error)
            print("(No input received or error during listening)")
            audio_handler.speak("Did you say something? I didn't catch that.")
            continue  # Ask again

        logging.info(f"User Input: '{user_input}'")
        # Check for exit command
        if user_input.lower() in ["quit", "exit", "stop", "bye"]:
            logging.info("User requested to quit the conversation.")
            farewell_msg = "Alright, I'm outta here. Keep it frosty!"
            print(f"\n{config.BOT_NAME}: {farewell_msg}")
            audio_handler.speak(farewell_msg)
            break

        # Check for history command
        elif user_input.lower() == "history":
            print("\n--- Chat History ---")
            history = chat_session.get_history()
            for i, message in enumerate(history):
                role = "🤖 Roastyy" if message.role == "model" else "👤 You"
                print(f"{role}: {message.parts[0].text}")
            print("--- End of History ---\n")
            continue

        # Check for clear history command
        elif user_input.lower() == "clear":
            # Create a new chat session with the same settings
            chat_session = gemini_handler.start_chat_session()
            print("Chat history has been cleared.")
            continue

        # If we get here, process the user input with Gemini
        try:
            # Get response from Gemini
            reply = gemini_handler.get_reply_from_text(chat_session, user_input)

            # Display the response
            print(f"\n{config.BOT_NAME}: {reply}")
            audio_handler.speak(reply)
        except Exception as e:
            logging.error(f"Error getting response from Gemini: {e}")
            error_msg = "Sorry, my brain just short-circuited. Can we try again?"
            print(f"\n{config.BOT_NAME}: {error_msg}")
            audio_handler.speak(error_msg)


def main():
    """Main application function."""
    logging.info(f"{config.BOT_NAME} starting up on platform: {config.PLATFORM}")

    # Initialize Gemini chat session once
    chat_session = None
    try:
        chat_session = gemini_handler.start_chat_session()
    except Exception as e:
        logging.error(f"CRITICAL: Failed to initialize Gemini chat session: {e}")
        print("Fatal error: Could not start chat with the AI. Exiting.")
        sys.exit(1)

    while True:
        display_intro()
        choice = input("Choose an option (P/T/Q): ").upper()
        logging.debug(f"User selected option: {choice}")

        if choice == "P":
            if handle_photo_roast():
                # Optionally transition directly into conversation after a photo roast
                start_chat = input(
                    "Roast delivered! Continue chatting? (Y/N): "
                ).upper()
                if start_chat == "Y":
                    conversation_loop(chat_session)
                else:
                    print("Okay, returning to main menu.")
            time.sleep(1)  # Pause before showing menu again

        elif choice == "T":
            conversation_loop(chat_session)
            # Reset chat session history after a full conversation ends if desired
            # print("Resetting chat session for next time.")
            # chat_session = gemini_handler.start_chat_session()
            time.sleep(1)  # Pause

        # elif choice == 'V': # Example if you wanted separate voice start
        #     print("Starting with voice input...")
        #     # Potentially call a specific voice-only initial prompt here
        #     conversation_loop(chat_session)

        elif choice == "Q":
            logging.info("User chose to quit the application.")
            print("Shutting down Roastyy. Stay cool!")
            audio_handler.speak("Goodbye! It's been... something.")
            break

        else:
            logging.warning(f"Invalid user choice: {choice}")
            error_msg = "Invalid choice, pal. Try P, T, or Q."
            print(error_msg)
            audio_handler.speak(error_msg)
            time.sleep(1)

    logging.info(f"{config.BOT_NAME} finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting...")
        logging.info("Application interrupted by user (Ctrl+C).")
    except Exception as e:
        logging.exception(
            "An uncaught exception occurred in main execution loop:"
        )  # Logs traceback
        print(f"\nAn unexpected critical error occurred: {e}")
    finally:
        print("Roastyy signing off.")
