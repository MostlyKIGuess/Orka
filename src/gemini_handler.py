import logging

from google import genai
from google.genai import types
from PIL import Image

import config

try:
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    logging.info("Gemini AI configured successfully.")
except Exception as e:
    logging.error(f"Error configuring Gemini AI: {e}")
    raise

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


def get_response_from_image(image_path, persona):
    """
    Analyzes an image using Gemini Vision based on the provided persona.

    Args:
        image_path (str): The path to the image file.
        persona (dict): The persona dictionary defining behavior.

    Returns:
        str: The generated text response, or an error message.
    """
    logging.info(
        f"Generating image response for: {image_path} using persona: {persona['name']}"
    )
    try:
        img = Image.open(image_path)
        # Use the persona's vision prompt template
        prompt = persona.get("vision_prompt_template", "Describe this image.")

        # Use the API format for generation
        response = client.models.generate_content(
            model=vision_model_name, contents=[prompt, img]
        )

        # Handle potential blocks or empty responses
        if hasattr(response, "candidates") and not response.candidates:
            logging.warning("Gemini response has no candidates (possibly blocked).")
            return f"I looked, but {persona['name']} is speechless. Couldn't generate a response."

        # Check if response has text
        if not hasattr(response, "text") or not response.text:
            logging.warning("Gemini response was blocked or empty.")
            return f"My analysis using {persona['name']} was blocked or couldn't generate content."

        response_text = response.text.strip()
        logging.info(f"Generated image response: {response_text}")
        return response_text

    except FileNotFoundError:
        logging.error(f"Image file not found at path: {image_path}")
        return "I can't process what I can't see! Image file not found."
    except Exception as e:
        logging.error(f"An error occurred during image processing: {e}")
        return f"Ouch! Something went wrong on my end processing that image ({type(e).__name__})."


def start_chat_session(persona):
    """
    Starts a new chat session with the text model using the specified persona.

    Args:
        persona (dict): The persona dictionary containing system_instruction.

    Returns:
        object: Chat session object.
    """
    logging.info(f"Starting new chat session with persona: {persona['name']}")
    try:
        # Get the system instruction from the persona
        system_instruction = persona.get(
            "system_instruction", "You are a helpful assistant."
        )

        # Use the API format for chat creation
        chat = client.chats.create(
            model=text_model_name,
            config=types.GenerateContentConfig(system_instruction=system_instruction),
        )

        return chat

    except Exception as e:
        logging.error(f"Error creating chat session: {e}")
        raise


def get_chat_reply(chat_session, user_input):
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
            return "I'm not sure how to respond to that. Let's try something else."

        reply = response.text.strip()
        logging.info(f"Generated reply: {reply}")
        return reply
    except Exception as e:
        logging.error(f"An error occurred during text reply generation: {e}")
        return f"Sorry, I encountered an error ({type(e).__name__}). Can we try again?"


def get_chat_history(chat_session):
    """
    Retrieves the chat history from a chat session.

    Args:
        chat_session: An active chat session object.

    Returns:
        list: The chat history or empty list if not available.
    """
    try:
        if hasattr(chat_session, "history"):
            return chat_session.history
        logging.warning("Chat session doesn't have a history attribute.")
        return []
    except Exception as e:
        logging.error(f"Error retrieving chat history: {e}")
        return []


# Keep these for backward compatibility, though they're deprecated
def get_roast_from_image(image_path):
    """
    Legacy function - use get_response_from_image with persona instead.
    """
    from src.persona import ROASTYY

    logging.warning(
        "Using deprecated get_roast_from_image function. Use get_response_from_image instead."
    )
    return get_response_from_image(image_path, ROASTYY)


def get_reply_from_text(chat_session, user_input):
    """
    Legacy function - use get_chat_reply instead.
    """
    logging.warning(
        "Using deprecated get_reply_from_text function. Use get_chat_reply instead."
    )
    return get_chat_reply(chat_session, user_input)
