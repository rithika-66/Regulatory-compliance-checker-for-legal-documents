import os
import requests
from flask import Flask, request, jsonify, render_template
import PyPDF2
from docx import Document

app = Flask(__name__)

# Folder to store uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowable file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Groq API configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "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"  # Replace with your actual Groq API key

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to read PDF file
def read_pdf(file_path):
    pdf_text = ""
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(pdf_reader.pages)
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                pdf_text += page.extract_text()
    except Exception as e:
        pdf_text = f"Error reading PDF: {e}"
    return pdf_text

# Function to read DOCX file
def read_docx(file_path):
    doc_text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            doc_text += paragraph.text + "\n"
    except Exception as e:
        doc_text = f"Error reading DOCX: {e}"
    return doc_text

# Function to extract key clauses using Groq API
def extract_key_clauses(text):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",  # Adjust as needed
        "messages": [{"role": "user", "content": f"Extract key clauses from the following text: {text}"}],
        "max_tokens": 1500  # Adjust according to your needs
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad HTTP status codes
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except requests.exceptions.RequestException as e:
        return f"Error calling Groq API: {e}"

# Route for file upload
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file upload and extraction
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extract text based on file type
        if filename.endswith('.pdf'):
            extracted_text = read_pdf(filepath)
        elif filename.endswith('.docx'):
            extracted_text = read_docx(filepath)
        
        # Extract key clauses using Groq API
        key_clauses = extract_key_clauses(extracted_text)
        
        # Return extracted clauses to frontend
        return jsonify({'key_clauses': key_clauses})

    return jsonify({'error': 'Invalid file type. Please upload a .pdf or .docx file.'})

if __name__ == '__main__':
    app.run(debug=True)
