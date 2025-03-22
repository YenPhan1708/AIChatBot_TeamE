from flask import Blueprint, request, render_template, jsonify, session as flask_session
import uuid
import logging
from app.chatbot import classify_intent, company_info_handler
from app.database import create_chat_session, store_message, get_session_messages

routes = Blueprint("routes", __name__)


@routes.route("/")
def home():
    # Generate a new session ID for each new visitor
    session_id = create_chat_session()
    logging.info(f"Home route - created session_id: {session_id}")
    return render_template("index.html", session_id=session_id)


@routes.route("/chat", methods=["POST"])
def chat():
    """Handles chat messages from the UI."""
    user_input = request.form["user_input"]
    session_id = request.form.get("session_id")
    logging.info(f"Chat route - received session_id: {session_id}, type: {type(session_id)}")

    # Check if session_id is "None" or empty and create a new one if needed
    if session_id == "None" or not session_id:
        logging.info("Creating new session as session_id is None or empty")
        session_id = create_chat_session()
        logging.info(f"New session created: {session_id}")
        if not session_id:
            logging.error("Failed to create a new session")
            return jsonify({
                "response": "Sorry, I'm having trouble with your session. Please try again.",
                "session_id": None
            })

    # Try to convert session_id to integer (assuming it's stored as an integer in DB)
    try:
        session_id = int(session_id)
        logging.info(f"Converted session_id to integer: {session_id}")
    except (ValueError, TypeError) as e:
        logging.error(f"Error converting session_id to integer: {e}")
        # If conversion fails, create a new session
        session_id = create_chat_session()
        logging.info(f"Created new session after conversion error: {session_id}")
        if not session_id:
            logging.error("Failed to create a new session after conversion error")
            return jsonify({
                "response": "Sorry, I'm having trouble with your session. Please try again.",
                "session_id": None
            })

    # Store user message in the database
    logging.info(f"Storing user message for session: {session_id}")
    message_stored = store_message(session_id, user_input, is_user=True)
    if not message_stored:
        logging.error(f"Failed to store user message for session {session_id}")
    else:
        logging.info(f"User message stored with ID: {message_stored}")

    # Get response from chatbot
    logging.info("Getting response from chatbot")
    response_text = company_info_handler(user_input, session_id)

    # Store bot response in the database
    logging.info("Storing bot response")
    bot_message_id = store_message(session_id, response_text, is_user=False)
    if not bot_message_id:
        logging.error("Failed to store bot response")
    else:
        logging.info(f"Bot message stored with ID: {bot_message_id}")

    return jsonify({
        "response": response_text,
        "session_id": session_id
    })