from flask import Flask, render_template, request
from fuzzywuzzy import process
import google.generativeai as genai 
from dotenv import load_dotenv
import os
import json
import random

# Load environment variables
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# Load predefined responses from a JSON file
with open('predefined_answers.json', 'r') as file:
    predefined_answers = json.load(file)

# Initialize the GenerativeAI model
API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Route for the home page
@app.route("/")
def index():
    return render_template('chat.html')

# Route to handle chat requests
@app.route("/get", methods=["POST"])
def chat():
    msg = request.form["msg"]
    response = get_chat_response(msg)
    return response

# Function to get the response for a given input text
def get_chat_response(text):
    # Make the input lowercase for case-insensitive comparison
    text_lower = text.lower()

    # Find the closest matching question using fuzzywuzzy
    matching_patterns = [pattern.lower() for question in predefined_answers["questions"] for pattern in question.get("patterns", [])]
    closest_match, score = process.extractOne(text_lower, matching_patterns)
    
    # Check if the similarity score is above a certain threshold (e.g., 80)
    # Setting a lower threshold to allow for some spelling errors or typos
    threshold = 90  # Adjusted threshold for fuzzy matching
    if score >= threshold:
        for question in predefined_answers["questions"]:
            if closest_match in [tag.lower() for tag in question.get("patterns", [])]:
                return random.choice(question["responses"])
    
    # If no close match, generate a response using the AI model
    try:
        response = model.generate_content(text)  # Generative AI call
        if response.candidates and response.candidates[0].content:
            formatted_response = response.candidates[0].content.parts[0].text
        else:
            formatted_response = "I don't know the answer to that."

        return formatted_response
    except Exception as e:
        if "timeout" in str(e).lower():
            return "Sorry, the GenerativeAI API timed out. Please try again later."
        else:
            return "An error occurred. Please try again later."

if __name__ == "__main__":
    app.run(debug=True)
