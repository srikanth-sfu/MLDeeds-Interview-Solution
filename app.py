from flask import Flask, request, render_template, send_file
from flaskwebgui import FlaskUI
from config import INDEX_FILE, DOWNLOAD_FOLDER, MSG_COLOR
from io import BytesIO
from utils import check_request_veracity, process_file
app = Flask(__name__)


# Newly Insert Line
ui = FlaskUI(app, width=500, height=500)


# Create index function for upload and return files
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        is_auth, err_msg = check_request_veracity(request)
        if not is_auth:
            color = MSG_COLOR.FAIL.value 
        else:
            color = MSG_COLOR.SUCCESS.value
            file = request.files['file']
            process_file(BytesIO(file.read()), file.filename, DOWNLOAD_FOLDER)
            download_url = "%s/%s"%(DOWNLOAD_FOLDER, file.filename.replace('.pdf', '.txt'))
        return render_template(INDEX_FILE, message=err_msg, color=color, download_url=download_url)
    else:
        return render_template(INDEX_FILE)

@app.route('/downloads/<filename>')
def download_file(filename):
    file_path = f"{DOWNLOAD_FOLDER}/{filename}"
    return send_file(file_path, as_attachment=True, download_name=filename)



if __name__ == '__main__':
    app.run()
    ui.run()
