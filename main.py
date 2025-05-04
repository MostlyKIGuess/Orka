import logging
import sys
import time
import os # Added import

# --- Setup Logging FIRST ---
try:
    from src import utils
    utils.setup_logging()
except ImportError:
    import logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.warning("Could not import src.utils. Using basic logging.")

# --- Import other components AFTER logging is set up ---
try:
    import config
    # Import persona module and handlers
    from src import audio_handler, gemini_handler, image_handler, persona as persona_module
except ImportError as e:
    logging.exception(f"Failed to import necessary modules: {e}") # Log traceback
    logging.error(
        "Please ensure all files exist (config.py, src/*) and required packages are installed (requirements.txt)."
    )
    sys.exit(1)
except ValueError as e: # Catch config errors like missing API key
    logging.error(f"Configuration error: {e}")
    sys.exit(1)

# --- Load Active Persona ---
# The logic is now primarily within persona.py, just grab the result
try:
    active_persona = persona_module.ACTIVE_PERSONA
    agent_name = active_persona['name'] # Get agent name for convenience
    logging.info(f"Using active persona: {agent_name}")
except AttributeError:
    logging.critical("CRITICAL: Could not load ACTIVE_PERSONA from src.persona. Exiting.")
    print("Fatal error: Could not load agent persona configuration.")
    sys.exit(1)
except Exception as e:
     logging.exception(f"An unexpected error occurred loading persona: {e}")
     print("Fatal error: Could not load agent persona. Exiting.")
     sys.exit(1)


def display_intro():
    """Displays the welcome message and instructions using the agent's name."""
    # Use agent_name loaded globally
    print("\n" + "=" * 40)
    print(f" Welcome! I am {agent_name}. ")
    # Removed hardcoded roast message
    print("=" * 40)
    print("Options:")
    # Updated option descriptions slightly
    print(f"  P - Interact with a Photo using {agent_name}")
    print(f"  T - Start Conversation with {agent_name}")
    print("  Q - Quit")
    print("=" * 40)


# --- Renamed Function ---
def handle_image_interaction():
    """Handles getting an image and interacting with it based on the persona."""
    # Use agent_name loaded globally
    print(f"\n--- Image Interaction ({agent_name}) ---")
    # Pass agent_name to speak/listen functions
    audio_handler.speak("Okay, let's get an image to look at.", agent_name)
    image_path = image_handler.get_image() # Assumes get_image handles platform specifics

    if image_path:
        logging.info(f"Image obtained: {image_path}")
        audio_handler.speak("Got the image. Let me analyze it...", agent_name)
        print(f"Processing image with {agent_name}...")
        # Pass active_persona to the handler function
        response_text = gemini_handler.get_response_from_image(image_path, active_persona)

        print(f"\n{agent_name}: {response_text}")
        audio_handler.speak(response_text, agent_name)

        # Optional temp image removal (check if it's the configured temp path)
        if image_path == config.TEMP_IMAGE_PATH and os.path.exists(image_path):
            try:
                os.remove(image_path)
                logging.info(f"Removed temporary image: {image_path}")
            except OSError as e:
                logging.error(f"Error removing temporary image {image_path}: {e}")
        return True # Indicate success
    else:
        logging.warning("Failed to get an image.")
        error_msg = "Couldn't get an image. Can't interact with thin air!"
        print(f"\n{agent_name}: {error_msg}")
        audio_handler.speak(error_msg, agent_name)
        return False # Indicate failure


def conversation_loop(chat_session):
    """Handles the ongoing text/voice conversation using the agent's persona."""
    # Use agent_name loaded globally
    print(f"\n--- Conversation Mode ({agent_name}) ---")
    print(
        "Type your message or speak when 'Listening...'. Type 'quit' or 'exit' to stop."
    )
    print(
        "Additional commands: 'history' to view chat history, 'clear' to clear history"
    )
    # Pass agent_name to speak/listen
    audio_handler.speak("Okay, let's chat. What's on your mind?", agent_name)

    while True:
        # Pass agent_name to listen
        user_input = audio_handler.listen(agent_name)

        if not user_input:
            print("(No input received or error during listening)")
            audio_handler.speak("Did you say something? I didn't catch that.", agent_name)
            continue

        logging.info(f"User Input: '{user_input}'")

        # Check for exit command
        if user_input.lower() in ["quit", "exit", "stop", "bye"]:
            logging.info("User requested to quit the conversation.")
            farewell_msg = "Alright, signing off for now." # Generic farewell
            print(f"\n{agent_name}: {farewell_msg}")
            audio_handler.speak(farewell_msg, agent_name)
            break

        # Check for history command
        elif user_input.lower() == "history":
            print("\n--- Chat History ---")
            # Use the refactored history retrieval
            history = gemini_handler.get_chat_history(chat_session)
            if not history:
                print("(History is empty)")
            else:
                # Use persona name from chat session if available, else global
                display_name = getattr(chat_session, 'persona_name', agent_name)
                for message in history:
                    role = f"🤖 {display_name}" if message.role == "model" else "👤 You"
                    text_content = "".join(part.text for part in message.parts if hasattr(part, 'text'))
                    print(f"{role}: {text_content}")
            print("--- End of History ---\n")
            continue

        # Check for clear history command
        elif user_input.lower() == "clear":
            # Create a new chat session with the same persona
            try:
                # Pass active_persona when restarting
                chat_session = gemini_handler.start_chat_session(active_persona)
                clear_msg = "Chat history has been cleared. Fresh start!"
                print(clear_msg)
                audio_handler.speak(clear_msg, agent_name)
            except Exception as e:
                 logging.error(f"Failed to restart chat session after clear: {e}")
                 error_msg = "Sorry, couldn't clear the history properly."
                 print(error_msg)
                 audio_handler.speak(error_msg, agent_name)
            continue

        # Process the user input with Gemini
        try:
            # Pass chat_session (no persona needed here)
            reply = gemini_handler.get_chat_reply(chat_session, user_input)

            print(f"\n{agent_name}: {reply}")
            audio_handler.speak(reply, agent_name)
        except Exception as e:
            logging.exception(f"Error getting response from Gemini during conversation: {e}")
            error_msg = "Sorry, my brain circuits seem to be tangled. Can we try that again?"
            print(f"\n{agent_name}: {error_msg}")
            audio_handler.speak(error_msg, agent_name)


def main():
    """Main application function."""
    # Use agent_name loaded globally
    logging.info(f"{agent_name} starting up on platform: {config.PLATFORM}")

    # Initialize Gemini chat session once with the active persona
    chat_session = None
    try:
        # Pass the loaded persona to the start function
        chat_session = gemini_handler.start_chat_session(active_persona)
    except Exception as e:
        # Error logged within start_chat_session, provide user feedback
        logging.critical(f"CRITICAL: Failed to initialize Gemini chat session: {e}")
        print(f"Fatal error: Could not start chat session with {agent_name}. Check API key and configuration. Exiting.")
        sys.exit(1)

    while True:
        display_intro()
        choice = input("Choose an option (P/T/Q): ").upper().strip()
        logging.debug(f"User selected option: {choice}")

        if choice == "P":
            handle_image_interaction() # Uses active_persona internally
            # Optional: Transition to chat
            # start_chat = input(f"Interaction complete! Continue chatting with {agent_name}? (Y/N): ").upper()
            # if start_chat == "Y":
            #     conversation_loop(chat_session)
            time.sleep(1) # Pause

        elif choice == "T":
            conversation_loop(chat_session)
            # Optionally reset chat session after conversation
            # print("Resetting chat session.")
            # try:
            #     chat_session = gemini_handler.start_chat_session(active_persona)
            # except Exception as e:
            #     logging.error(f"Failed to reset chat session: {e}")
            time.sleep(1) # Pause

        elif choice == "Q":
            logging.info("User chose to quit the application.")
            shutdown_msg = f"Shutting down {agent_name}. Goodbye!"
            print(shutdown_msg)
            audio_handler.speak("Goodbye!", agent_name)
            break

        else:
            logging.warning(f"Invalid user choice: {choice}")
            error_msg = "Invalid choice. Please try P, T, or Q."
            print(error_msg)
            audio_handler.speak(error_msg, agent_name)
            time.sleep(1)

    logging.info(f"{agent_name} finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting...")
        logging.info("Application interrupted by user (Ctrl+C).")
    except Exception as e:
        logging.exception("An uncaught exception occurred in the main execution loop:")
        print(f"\nAn unexpected critical error occurred: {e}")
    finally:
        # Use agent_name loaded globally
        print(f"{agent_name} signing off.")
