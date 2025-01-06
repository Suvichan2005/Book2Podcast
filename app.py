import os
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import podcast_generator

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'pdf', 'epub', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    audio_url = None

    if request.method == 'POST':
        if 'document' not in request.files:
            flash('No file part in the request')
            return render_template('index.html', audio_url=audio_url)
        file = request.files['document']
        if file.filename == '':
            flash('No selected file')
            return render_template('index.html', audio_url=audio_url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            format_option = request.form.get('format_option', 'monologue')
            try:
                output_filename = podcast_generator.main(upload_path, format_option, filename)
                output_file_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
                audio_url = url_for('outputs', filename=output_filename)
                os.remove(upload_path)
            except Exception as e:
                flash(f'Error during processing: {e}')
                return render_template('index.html', audio_url=audio_url)

            return render_template('index.html', audio_url=audio_url)
        else:
            flash('Allowed file types are pdf, epub, docx, txt')
            return render_template('index.html', audio_url=audio_url)

    return render_template('index.html', audio_url=audio_url)

@app.route('/outputs/<filename>')
def outputs(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=False)

if __name__ == '__main__':
    app.run() 