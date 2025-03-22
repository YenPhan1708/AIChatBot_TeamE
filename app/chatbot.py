import logging
from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.database import fetch_relevant_info, get_session_messages
from app.agentConnector import AgentConnector

client = OpenAI(api_key=OPENAI_API_KEY)

agent_connector = AgentConnector()


def classify_intent(user_input):
    """Classifies user intent using GPT."""
    intent_prompt = [
                 {"role": "system", "content": "You are a classifier. Identify the intent of the user's question. "
                                               "Valid intents: ['Company Info', 'IT Services & Trends', 'Human Support Service Request']."
                                               "If the question is unrelated to Bravur or IT, classify it as 'Unknown'."},
                 {"role": "user", "content": user_input}
             ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=intent_prompt
    )

    return response.choices[0].message.content.strip()


def get_conversation_history(session_id):
    """Get the conversation history for a session."""
    if not session_id:
        return []

    messages = get_session_messages(session_id)
    formatted_messages = []

    for _, content, _ in messages:
        if content.startswith("USER: "):
            formatted_messages.append({"role": "user", "content": content[6:]})
        elif content.startswith("BOT: "):
            formatted_messages.append({"role": "assistant", "content": content[5:]})

    return formatted_messages


def company_info_handler(user_input, session_id=None):
    """Handles queries related to company information."""
    detected_intent = classify_intent(user_input)

    if detected_intent == "Unknown":
        return "I'm here to answer questions about Bravur and IT services. How can I help?"

    if detected_intent == "Human Support Service Request":
        return "For human support, contact us on WhatsApp at +31 6 12345678 or email support@bravur.com."

    if detected_intent == "IT Services & Trends":
        # Get conversation history if session_id is provided
        conversation_history = get_conversation_history(session_id) if session_id else []

        # Prepare the prompt with conversation history
        gpt_prompt = [
            {"role": "system",
             "content": "You are a knowledgeable assistant providing insights on IT services and industry trends."}
        ]

        # Add relevant conversation history
        gpt_prompt.extend(conversation_history)

        # Add current user input
        gpt_prompt.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=gpt_prompt
        )

        return response.choices[0].message.content.strip()

    # Fetch Bravur-related information
    bravur_info = fetch_relevant_info()

    # Get conversation history if session_id is provided
    conversation_history = get_conversation_history(session_id) if session_id else []

    # Prepare the base system prompt
    system_prompt = f"You are a helpful assistant providing information about Bravur and IT services. " \
                    f"Format responses for display in a simple HTML website. " \
                    f"Be concise. Use short paragraphs, barely use bullet points, make it look like a human chatbot and avoid long blocks of text. " \
                    f"ALWAYS include the source (row or multiple rows if applicable) regarding where you found the answer to the question. " \
                    f"If 2 or more questions are asked, you answer the first question, cite the source, answer the next one, cite the source etc. " \
                    f"\nHere is relevant company information:\n{bravur_info}"

    # Build the prompt with conversation history
    gpt_prompt = [{"role": "system", "content": system_prompt}]

    # Add relevant conversation history
    gpt_prompt.extend(conversation_history)

    # Add current user input
    gpt_prompt.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=gpt_prompt
    )

    return response.choices[0].message.content.strip()


# Register the Company Information Agent
agent_connector.register_agent("Bravur_Information_Agent", company_info_handler)