from flask import Flask, render_template, request
from fuzzywuzzy import process
import google.generativeai as genai 
from dotenv import load_dotenv
import os
import json
import random

load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# Load predefined responses from JSON file
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
    # Check if the question is predefined
    for question in predefined_answers["questions"]:
        if any(tag.lower() == text.lower() for tag in question.get("patterns", [])):
            return random.choice(question["responses"])
    
    # If not, find the closest matching question using fuzzywuzzy
    matching_patterns = [pattern.lower() for question in predefined_answers["questions"] for pattern in question.get("patterns", [])]
    closest_match, score = process.extractOne(text.lower(), matching_patterns)
    
    # If the similarity score is above a certain threshold (e.g., 90), use the closest match
    if score >= 90 and closest_match == text.lower():
        for question in predefined_answers["questions"]:
            if closest_match in [tag.lower() for tag in question.get("patterns", [])]:
                return random.choice(question["responses"])
    
    # If the similarity score is below the threshold, continue with the chatbot model
    try:
        response = model.generate_content(text)
        responses = []
        
        # Check if the response has multiple parts
        if response.candidates and response.candidates[0].content.parts:
            # Access the parts of the response
            for part in response.candidates[0].content.parts:
                # Check if part is code, if so, wrap it with <code> tags
                if "```" in part.text:
                    part_text = part.text.replace("```", "")
                    responses.append(f"<code>{part_text}</code>")
                else:
                    responses.append(part.text)
            formatted_response = "\n\n".join(responses)
        else:
            # Handle the case when there are no candidates or no parts in the response
            formatted_response = "No suitable response found."
        
        return formatted_response
    except Exception as e:
        if "timeout" in str(e).lower():
            return "Sorry, I couldn't find an answer. The GenerativeAI API timed out. Please try again later."
        else:
            raise

if __name__ == "__main__":
    app.run(debug=True)
