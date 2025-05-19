"""
Flask web server for Sisimpur Brain.

This module provides a web interface for the Sisimpur Brain system.
"""

import os
import json
from flask import Flask, request, render_template, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

# Import Sisimpur Brain modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sisimpur.generators.generate_qa_raw_text import generate_qa_from_raw_text
from sisimpur.config import GEMINI_API_KEY

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html', api_key_set=bool(GEMINI_API_KEY))

@app.route('/generate', methods=['POST'])
def generate():
    """Generate Q&A pairs from text or uploaded file."""
    try:
        # Get parameters
        language = request.form.get('language', 'auto')
        num_questions = request.form.get('num_questions')
        if num_questions and num_questions.isdigit():
            num_questions = int(num_questions)
        else:
            num_questions = None
        
        # Check if text is provided directly
        text_input = request.form.get('text', '').strip()
        source_name = None
        
        # Check if file is uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Read text from file
                with open(filepath, 'r', encoding='utf-8') as f:
                    text_input = f.read()
                source_name = filename
        
        # Validate input
        if not text_input:
            return jsonify({
                'success': False,
                'error': 'No text provided. Please enter text or upload a file.'
            }), 400
        
        # Generate Q&A pairs
        output_file = generate_qa_from_raw_text(
            text=text_input,
            language=language,
            num_questions=num_questions,
            source_name=source_name
        )
        
        # Read the generated JSON file
        with open(output_file, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
        
        return jsonify({
            'success': True,
            'output_file': output_file,
            'data': qa_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API endpoint for generating Q&A pairs."""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        text = data.get('text', '').strip()
        language = data.get('language', 'auto')
        num_questions = data.get('num_questions')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400
        
        # Generate Q&A pairs
        output_file = generate_qa_from_raw_text(
            text=text,
            language=language,
            num_questions=num_questions
        )
        
        # Read the generated JSON file
        with open(output_file, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
        
        return jsonify({
            'success': True,
            'output_file': output_file,
            'data': qa_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
