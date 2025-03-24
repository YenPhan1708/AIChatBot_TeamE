import logging
from openai import OpenAI
from fuzzywuzzy import fuzz
from app.config import OPENAI_API_KEY
from app.database import fetch_relevant_info, get_session_messages, store_message
from app.agentConnector import AgentConnector

client = OpenAI(api_key=OPENAI_API_KEY)
agent_connector = AgentConnector()

# Common prompts to recall past questions
memory_prompts = [
    "what was my last question",
    "what was my previous question",
    "can you remind me my last question",
    "what did I ask before",
    "what was my earlier question",
    "show me my previous question",
    "tell me my last question",
    "repeat my last question",
    "what did I say last"
]

# Check if the user is asking about the last question
def is_last_question_request(user_input):
    for prompt in memory_prompts:
        if fuzz.partial_ratio(user_input.lower(), prompt) > 80:
            return True
    return False

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


def get_recent_conversation(session_id, limit=3):
    """Retrieve the last 'limit' messages to maintain recent context."""
    if not session_id:
        return []

    messages = get_session_messages(session_id)

    # Format messages as user and assistant roles
    formatted_messages = []
    for _, content, _ in messages:
        if content.startswith("USER: "):
            formatted_messages.append({"role": "user", "content": content[6:]})
        elif content.startswith("BOT: "):
            formatted_messages.append({"role": "assistant", "content": content[5:]})

    # Return only the last 'limit' messages to avoid repetition
    return formatted_messages[-(limit * 2):]  # Each turn has 2 messages (user + assistant)


def handle_meta_questions(user_input, session_id):
    """Handle meta-questions like 'What was my last question?' or 'Summarize our conversation'."""
    if not session_id:
        return "I don't have any previous conversation to refer to."

    # Fetch all messages to process meta-questions
    messages = get_session_messages(session_id)

    if not messages:
        return "I don't remember anything yet."

    # Reverse messages to get the latest ones first
    messages.reverse()

    # Handle last question request
    if is_last_question_request(user_input):
        # Skip the current input and find the previous real user question
        last_real_question = None
        skip_current = True

        for _, content, _ in messages:
            if content.startswith("USER: "):
                if skip_current:
                    skip_current = False
                    continue  # Skip the current meta-question

                # Found the last real question
                last_real_question = content[6:]
                break

        if last_real_question:
            return f"Your last question was: \"{last_real_question}\""
        else:
            return "I couldn't find your last question."

    # Handle last answer request
    elif "last answer" in user_input.lower():
        for _, content, _ in messages:
            if content.startswith("BOT: "):
                return f"My last answer was: \"{content[5:]}\""
        return "I couldn't find my last answer."

    # Handle conversation summary
    elif "summarize" in user_input.lower():
        # Collect ALL messages for the session
        all_messages = get_session_messages(session_id)

        # Prepare messages for GPT summarization
        formatted_messages = []
        for _, content, _ in all_messages:
            if content.startswith("USER: "):
                formatted_messages.append({"role": "user", "content": content[6:]})
            elif content.startswith("BOT: "):
                formatted_messages.append({"role": "assistant", "content": content[5:]})

        # Build the summarization prompt
        summary_prompt = [
                             {"role": "system",
                              "content": "Summarize the following conversation in a concise manner, covering the key points discussed."}
                         ] + formatted_messages

        # Call GPT to generate the summary
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=summary_prompt
        )

        # Return the generated summary
        return response.choices[0].message.content.strip()

    return "I'm not sure what you're referring to. Could you clarify?"


def company_info_handler(user_input, session_id=None):
    """Handles queries related to company information, IT trends, and human support."""

    # Prioritize meta-questions
    if is_last_question_request(user_input) or "last answer" in user_input.lower() or "summarize" in user_input.lower():
        return handle_meta_questions(user_input, session_id)

    # Fetch the last 3 messages (user and assistant) to maintain flow and prevent repetition
    recent_conversation = get_recent_conversation(session_id, limit=3)

    # Classify intent based only on the latest user message
    detected_intent = classify_intent(user_input)

    if detected_intent == "Unknown":
        return "I'm here to answer questions about Bravur and IT services. How can I help?"

    if detected_intent == "Human Support Service Request":
        return "For human support, contact us on WhatsApp at +31 6 12345678 or email support@bravur.com."

    if detected_intent == "IT Services & Trends":
        # Specialized prompt for IT Services & Trends
        it_prompt = [
            {"role": "system",
             "content": "You are a knowledgeable assistant providing insights on IT services and industry trends. "
                        "Prioritize the latest user question, but consider recent context for better accuracy. "
                        "Avoid repeating recent answers unless explicitly asked."}
        ]

        # Add recent conversation history to keep track of context
        it_prompt.extend(recent_conversation)

        # Add current user input
        it_prompt.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=it_prompt
        )

        final_response = response.choices[0].message.content.strip()

        # Store the messages to maintain conversation flow
        if session_id:
            store_message(session_id, f"USER: {user_input}", is_user=True)
            store_message(session_id, f"BOT: {final_response}", is_user=False)

        return final_response

    # Handle Bravur-related Information
    bravur_info = fetch_relevant_info()

    # Prepare the base system prompt
    system_prompt = f"You are a helpful assistant providing information about Bravur and IT services. " \
                    f"Format responses for display in a simple HTML website. " \
                    f"Be concise. Use short paragraphs, barely use bullet points, make it look like a human chatbot and avoid long blocks of text. " \
                    f"ALWAYS include the source (row or multiple rows if applicable) regarding where you found the answer to the question. " \
                    f"If 2 or more questions are asked, you answer the first question, cite the source, answer the next one, cite the source etc. " \
                    f"\nHere is relevant company information:\n{bravur_info}"

    # Build the prompt with conversation history
    gpt_prompt = [{"role": "system", "content": system_prompt}]

    # Include the last 3 user and assistant messages for context
    gpt_prompt.extend(recent_conversation)

    # Add current user input
    gpt_prompt.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=gpt_prompt
    )

    final_response = response.choices[0].message.content.strip()

    # Store the messages to maintain conversation flow
    if session_id:
        store_message(session_id, f"USER: {user_input}", is_user=True)
        store_message(session_id, f"BOT: {final_response}", is_user=False)

    return final_response


# Register the Company Information Agent
agent_connector.register_agent("Bravur_Information_Agent", company_info_handler)