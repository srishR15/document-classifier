from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
import PyPDF2
import docx
import re

app = Flask(__name__)

# Configure upload folder for uploading files to check the type of document!
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions as given in problem statement
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Here we extract text if file is pdf format
def extract_text_from_pdf(filepath):
    text = ""
    with open(filepath, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + " "
    return text
# Here we extract text if file is a doc
def extract_text_from_docx(filepath):
    doc = docx.Document(filepath)
    return " ".join([para.text for para in doc.paragraphs])
# Main function which checks which type of document it is
def classify_document(text):
    # Converting to uppercase for case-insensitive matching
    text_upper = text.upper()
    
    # Patterns to identify each document type (more strict matching)
    patterns = {
        'Stock Purchase Agreement': [
            r'SERIES\s[A-Z]\sPREFERRED\sSTOCK\sPURCHASE\sAGREEMENT',  # Strict matching for "SERIES A PREFERRED STOCK PURCHASE AGREEMENT"
            r'STOCK\sPURCHASE\sAGREEMENT\s(THIS|THIS\sAGREEMENT)',  # Avoid matching inside Investors' Rights Agreement
        ],
        'Investors\' Rights Agreement': [
            r'INVESTORS[\’\']\sRIGHTS\sAGREEMENT',  # Catches both "Investors' Rights Agreement" and "Investors’ Rights Agreement" For amended versions
            r'AMENDED\sAND\sRESTATED\sINVESTORS[\’\']\sRIGHTS\sAGREEMENT',
            r'THIS\sINVESTORS[\’\']\sRIGHTS\sAGREEMENT\sIS\sMADE',  # Checks for a common opening phrase
        ],
        'Certificate of Incorporation': [
            r'CERTIFICATE\sOF\sINCORPORATION',
            r'AMENDED\sAND\sRESTATED\sCERTIFICATE\sOF\sINCORPORATION',
            r'[A-Z\s]+CORPORATION\sCERTIFICATE\sOF\sINCORPORATION',  # Some docs include state information hence this line
        ]
    }
    
    # Check for each document type
    for doc_type, doc_patterns in patterns.items():
        for pattern in doc_patterns:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return doc_type
    
    return "Unknown Document Type"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text based on file type
            if filename.lower().endswith('.pdf'):
                text = extract_text_from_pdf(filepath)
            elif filename.lower().endswith(('.doc', '.docx')):
                text = extract_text_from_docx(filepath)
            else:
                return "Unsupported file type"
            
            # Classify the document
            doc_type = classify_document(text)
            
            # Clean up - here we remove the uploaded file
            os.remove(filepath)
            
            return render_template('result.html', doc_type=doc_type)
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)