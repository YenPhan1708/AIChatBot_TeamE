# import os
# import logging
# from dotenv import load_dotenv
# from flask import Flask, render_template, request, jsonify
# import psycopg2
# from openai import OpenAI
#
# # load environment variables from .env
# load_dotenv()
#
# # initialize openai client
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#
#
# app = Flask(__name__)
#
# # set up logging
# logging.basicConfig(level=logging.INFO)
#
# # fetch db credentials from .env
# DB_HOST = os.getenv("DB_HOST")
# DB_PORT = os.getenv("DB_PORT")
# DB_NAME = os.getenv("DB_NAME")
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
#
# def classify_intent(user_input):
#     """classifies user intent using GPT"""
#     intent_prompt = [
#         {"role": "system", "content": "You are a classifier. Identify the intent of the user's question. "
#                                       "Valid intents: ['Company Info', 'IT Services & Trends', 'Human Support Service Request']."
#                                       "If the question is unrelated to Bravur or IT, classify it as 'Unknown'."},
#         {"role": "user", "content": user_input}
#     ]
#
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=intent_prompt
#     )
#
#     return response.choices[0].message.content.strip()
#
# def fetch_relevant_info():
#     """retrieves everything from bravur_information table (non-vector)"""
#     try:
#         # connect to the db
#         conn = psycopg2.connect(
#             host=DB_HOST,
#             port=DB_PORT,
#             dbname=DB_NAME,
#             user=DB_USER,
#             password=DB_PASSWORD
#         )
#         cursor = conn.cursor()
#
#         # execute query to get all data
#         cursor.execute("SELECT id, category, title, content FROM bravur_information;")
#         rows = cursor.fetchall()
#
#         # format data into a readable string
#         formatted_data = "\n".join(
#             [f"Row ID: {row_id}\nCategory: {category}\nTitle: {title}\nContent: {content}\n"
#              for row_id, category, title, content in rows]
#         )
#
#         # log the retrieved database data
#         logging.info(f"Retrieved DB Data:\n{formatted_data}")
#
#         # close connection
#         cursor.close()
#         conn.close()
#
#         return formatted_data
#
#     except Exception as e:
#         print(f"Error fetching data: {e}")
#         return ""
#
# @app.route("/")
# def home():
#     """render the chat UI"""
#     return render_template("index.html")
#
# @app.route("/chat", methods=["POST"])
# def chat():
#     """handles chat messages from the UI"""
#     user_input = request.form["user_input"]
#     detected_intent = classify_intent(user_input)
#
#     if detected_intent == "Unknown":
#         return jsonify({"response": "I'm here to answer questions about Bravur and IT services. How can I help?"})
#
#     if detected_intent == "Human Support Service Request":
#         return jsonify({"response": "For human support, please contact us on WhatsApp at +31 6 12345678 or email us at support@bravur.com."})
#
#     if detected_intent == "IT Services & Trends":
#         # query GPT directly (NO DATABASE CALL)
#         gpt_prompt = [
#             {"role": "system", "content": "You are a knowledgeable assistant providing insights on IT services and current industry trends. "
#                                           f"Format responses for display in a simple HTML website."
#                                           f"Be concise. Use short paragraphs, barely use bullet points, make it look like a human chatbot and avoid long blocks of text."
#                                           f"Keep responses very concise."},
#             {"role": "user", "content": user_input}
#         ]
#
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=gpt_prompt
#         )
#
#         return jsonify({"response": response.choices[0].message.content.strip()})
#
#     # fetch db info if the query is about bravur
#     bravur_info = fetch_relevant_info()
#
#     gpt_prompt = [
#         {"role": "system", "content": f"You are a helpful assistant providing information about Bravur and IT services. "
#                                       f"Format responses for display in a simple HTML website."
#                                       f"Be concise. Use short paragraphs, barely use bullet points, make it look like a human chatbot and avoid long blocks of text."
#                                       f"ALWAYS  include the source (row or multiple rows if applicable) regarding where you found the answer to the question. " #request to include sources
#                                       f"If 2 or more questions are asked, u answer the first question, cite the source, answer the next one, cite the source etc."
#                                       f"\nHere is relevant company information:\n{bravur_info}"},
#         {"role": "user", "content": user_input}
#     ]
#
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=gpt_prompt
#     )
#
#     return jsonify({"response": response.choices[0].message.content.strip()})
#
# if __name__ == "__main__":
#     app.run(debug=True)
