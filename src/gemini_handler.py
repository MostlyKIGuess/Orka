import logging

from google import genai
from PIL import Image
import config  

try:
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    logging.info("Gemini AI configured successfully.")
except Exception as e:
    logging.error(f"Error configuring Gemini AI: {e}")
    raise

# Define model names to use them later
try:
    # We don't need to initialize models explicitly with the new API
    # Just keep track of model names
    vision_model_name = config.VISION_MODEL_NAME
    text_model_name = config.TEXT_MODEL_NAME
    logging.info(f"Initialized Vision Model: {vision_model_name}")
    logging.info(f"Initialized Text Model: {text_model_name}")
except Exception as e:
    logging.error(f"Error initializing Gemini models: {e}")
    raise


def get_roast_from_image(image_path):
    """
    Analyzes an image using Gemini Vision and generates a roast.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The generated roast text, or an error message.
    """
    logging.info(f"Generating roast for image: {image_path}")
    try:
        img = Image.open(image_path)
        prompt = (
            "You are Roastyy, a witty and sarcastic AI assistant. "
            "Your task is to analyze the provided image and deliver a short, funny, "
            "and SFW (safe-for-work) roast based on its content. "
            "Keep it light-hearted and clever. Do not be overly mean or offensive. "
            "Focus on observable details in the image for your roast."
            "\n\nRoast this image:"
        )

        # Use the new API format for generation
        response = client.models.generate_content(
            model=vision_model_name, contents=[prompt, img]
        )

        # Handle potential blocks or empty responses
        if hasattr(response, "candidates") and not response.candidates:
            logging.warning("Gemini response has no candidates (possibly blocked).")
            return "I looked, but I'm speechless... and not in a good way. Couldn't come up with a roast for that."

        # Check if response has text
        if not hasattr(response, "text") or not response.text:
            logging.warning("Gemini response was blocked or empty.")
            return "My circuits fizzled trying to process that. Try a different image maybe?"

        roast = response.text.strip()
        logging.info(f"Generated roast: {roast}")
        return roast

    except FileNotFoundError:
        logging.error(f"Image file not found at path: {image_path}")
        return "I can't roast what I can't see! Image file not found."
    except Exception as e:
        logging.error(f"An error occurred during image roasting: {e}")
        return f"Ouch! Something went wrong on my end trying to roast that image ({type(e).__name__})."


def start_chat_session():
    """Starts a new chat session with the text model."""
    logging.info("Starting new chat session.")
    try:
        # System instruction helps set the persona consistently
        system_instruction = (
            "You are Roastyy, a witty and sarcastic AI assistant specializing in light-hearted roasts. "
            "Engage in conversation, be funny, slightly sarcastic, but always SFW (safe-for-work). "
            "Respond to user input with witty remarks or follow-up roasts. Keep responses relatively concise."
        )

        # Use the new API format for chat creation
        chat = client.chats.create(
            model=text_model_name,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
        )
        return chat

    except Exception as e:
        logging.error(f"Error creating chat session: {e}")
        raise


def get_reply_from_text(chat_session, user_input):
    """
    Gets a conversational reply from the Gemini text model within a chat session.

    Args:
        chat_session: An active chat session object from `start_chat_session()`.
        user_input (str): The text input from the user.

    Returns:
        str: The generated reply text, or an error message.
    """
    logging.info(f"Sending user input to chat: '{user_input}'")
    try:
        response = chat_session.send_message(user_input)

        # Check if response has text
        if not hasattr(response, "text") or not response.text:
            logging.warning("Gemini chat response was blocked or empty.")
            return "My wit seems to have short-circuited. I got nothing."

        reply = response.text.strip()
        logging.info(f"Generated reply: {reply}")
        return reply
    except Exception as e:
        logging.error(f"An error occurred during text reply generation: {e}")
        return (
            f"Yikes! My circuits sparked on that reply ({type(e).__name__}). Try again?"
        )
