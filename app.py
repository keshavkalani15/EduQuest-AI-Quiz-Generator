from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import os
from dotenv import load_dotenv
import traceback
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get API key from environment variable
API_KEY = os.getenv('GOOGLE_API_KEY')
if not API_KEY:
    raise ValueError("No Google API key found. Please set GOOGLE_API_KEY in .env file.")

genai.configure(api_key=API_KEY)

def generate_mcqs(keyword, difficulty_level, num_mcqs):
    """Generate multiple-choice questions using Google Generative AI."""
    try:
        # Validate inputs
        difficulty_level = str(difficulty_level).lower()
        num_mcqs = int(num_mcqs)

        # Create prompt based on difficulty level
        difficulty_descriptions = {
            'easy': 'simple and straightforward, suitable for beginners',
            'moderate': 'of medium complexity, requiring some critical thinking',
            'challenging': 'more complex, requiring deeper understanding and analysis',
            'hard': 'highly complex, demanding advanced knowledge and critical reasoning'
        }

        prompt = f"""
Generate EXACTLY {num_mcqs} multiple-choice questions about {keyword} that are {difficulty_descriptions.get(difficulty_level, 'of varying complexity')}.

IMPORTANT RULES:
1. ALL questions MUST be text-based
2. NO image-based or graphical options allowed
3. Options must be purely textual descriptions or statements
4. Generate EXACTLY {num_mcqs} questions
5. Each question MUST have 4 options and a correct answer
6. Each time generate unique MCQs

Format EXACTLY like this for EACH question:

Q: [Question text - NO REFERENCES TO IMAGES]
A) [First text-only option]
B) [Second text-only option]
C) [Third text-only option]
D) [Fourth text-only option]
Correct: [A/B/C/D]
{'' if difficulty_level == 'easy' else 'Explanation: [Brief text explanation of why this is the correct answer]'}

"""

        model = genai.GenerativeModel("models/gemini-2.5-flash")
        
        try:
            # Added timeout and error handling
            response = model.generate_content(prompt, generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.7,
                "top_p": 1
            })
            
            # Print the raw response for debugging
            print("Raw API Response:")
            print(response.text)
            
        except Exception as api_error:
            print(f"API Generation Error: {api_error}")
            traceback.print_exc()
            return f"API Error: {str(api_error)}"

        # Check if response is valid
        if not response.text:
            return "Error: No response received from API."

        # Improved parsing logic
        def parse_mcq(mcq_text):
            # Split the MCQ block into lines
            lines = mcq_text.strip().split('\n')
            
            # Extract question
            if not lines or not lines[0].startswith('Q:'):
                return None
            
            question = lines[0].replace('Q: ', '').strip()
            
            # Extract options
            if len(lines) < 5:
                return None
            
            options = [
                lines[1].replace('A) ', '').strip(),
                lines[2].replace('B) ', '').strip(),
                lines[3].replace('C) ', '').strip(),
                lines[4].replace('D) ', '').strip()
            ]
            
            # Extract correct answer
            if len(lines) < 6 or not lines[5].startswith('Correct:'):
                return None
            
            correct_answer = lines[5].replace('Correct: ', '').strip()
            
            # Prepare MCQ entry
            mcq_entry = {
                "question": question,
                "options": [
                    f"A) {options[0]}",
                    f"B) {options[1]}",
                    f"C) {options[2]}",
                    f"D) {options[3]}"
                ],
                "answer": correct_answer
            }
            
            # Add explanation for non-easy difficulty levels
            if difficulty_level != 'easy' and len(lines) > 6:
                explanation = lines[6].replace('Explanation: ', '').strip()
                mcq_entry["explanation"] = explanation
            
            return mcq_entry

        # Parse MCQs from the response
        mcqs_list = []
        
        # Split response into individual MCQ blocks
        mcq_blocks = re.split(r'\n\n+', response.text)
        
        for block in mcq_blocks:
            mcq = parse_mcq(block)
            if mcq:
                mcqs_list.append(mcq)
                
                # Stop if we've reached the desired number of MCQs
                if len(mcqs_list) == num_mcqs:
                    break
        
        # Ensure we generate the exact number of MCQs requested
        if len(mcqs_list) < num_mcqs:
            return f"Error: Could only generate {len(mcqs_list)} MCQs out of {num_mcqs} requested."

        return mcqs_list

    except ValueError:
        return "Error: Please enter valid inputs."
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        return f"An error occurred: {str(e)}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    keyword = data.get("keyword", "").strip()
    difficulty_level = data.get("difficulty_level", "").strip()
    num_mcqs = data.get("num_mcqs", "").strip()

    if not keyword or not difficulty_level or not num_mcqs:
        return jsonify({"error": "Please provide all inputs."}), 400

    mcqs = generate_mcqs(keyword, difficulty_level, num_mcqs)
    return jsonify({"mcqs": mcqs})

if __name__ == "__main__":
    app.run(debug=True)