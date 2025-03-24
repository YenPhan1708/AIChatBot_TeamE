import psycopg2
import logging
from datetime import datetime
from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None


def fetch_relevant_info():
    conn = get_db_connection()
    if conn is None:
        return ""

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, title, content FROM bravur_information;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        formatted_data = "\n".join(
            [f"Row ID: {row_id}\nCategory: {category}\nTitle: {title}\nContent: {content}\n"
             for row_id, category, title, content in rows]
        )

        logging.info(f"Retrieved DB Data:\n{formatted_data}")
        return formatted_data

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return ""


def create_chat_session():
    """Create a new chat session and return its ID"""
    conn = get_db_connection()
    if conn is None:
        logging.error("Failed to get database connection in create_chat_session")
        return None

    try:
        cursor = conn.cursor()
        now = datetime.now()
        # Add detailed error information
        logging.info("Attempting to insert new chat session")
        cursor.execute(
            "INSERT INTO chat_session (timestamp, voice_enabled, duration_minutes) VALUES (%s, %s, %s) RETURNING session_id",
            (now, False, 0)  # Default values
        )
        session_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"Created new chat session with ID: {session_id}")
        return session_id
    except Exception as e:
        logging.error(f"Error creating chat session: {e}")
        # Add stack trace for more information
        import traceback
        logging.error(traceback.format_exc())
        if conn:
            conn.close()
        return None


def store_message(session_id, content, is_user=True):
    """Store a message in the database"""
    if not session_id:
        logging.error("Cannot store message: No session ID provided")
        return False

    try:
        # Ensure session_id is an integer
        session_id = int(session_id)
    except (ValueError, TypeError):
        logging.error(f"Invalid session ID format: {session_id}")
        return False

    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        now = datetime.now()
        # Add a prefix to distinguish between user and bot messages
        message_content = f"{'USER: ' if is_user else 'BOT: '}{content}"

        cursor.execute(
            "INSERT INTO message (session_id, content, timestamp) VALUES (%s, %s, %s) RETURNING message_id",
            (session_id, message_content, now)
        )
        message_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"Stored message (ID: {message_id}) for session {session_id}")
        return message_id
    except Exception as e:
        logging.error(f"Error storing message: {e}")
        if conn:
            conn.close()
        return False

def get_session_messages(session_id):
    """Retrieve all messages for a specific session"""
    if not session_id:
        return []

    conn = get_db_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message_id, content, timestamp FROM message WHERE session_id = %s ORDER BY timestamp",
            (session_id,)
        )
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        logging.info(f"Retrieved {len(messages)} messages for session {session_id}")
        return messages
    except Exception as e:
        logging.error(f"Error retrieving session messages: {e}")
        if conn:
            conn.close()
        return []