import os
from PyPDF2 import PdfReader 
from flask import request
from typing import Tuple
from config import ALLOWED_EXTENSIONS, ConversionErrorMessage
from io import BytesIO
from .nlp_utils import Pipeline 

def allowed_file(filename: str) -> bool:
    """
    Checks if file is a PDF.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_request_veracity(req: request) -> Tuple[bool, str]:
    """
    Checks if upload file post request is valid.
    """
    is_auth = False
    if 'file' not in request.files:
        message = ConversionErrorMessage.NO_FILE_ATTACHED_ERROR
    else:
        file = request.files['file']
        if file.filename == '':
            message = ConversionErrorMessage.NO_FILE_ATTACHED_ERROR
        elif not allowed_file(file.filename):
            message = ConversionErrorMessage.ONLY_PDF_FILES_ERROR
        else:
            is_auth = True
            message = ConversionErrorMessage.SUCCESS_MESSAGE
    return is_auth, message.value


def save_as_text(stream: BytesIO, filename: str, download_folder: str) -> None:
    """
    Converts pdf to redacted text and saves redacted text to a text file.
    """
    try:
        input_file = PdfReader(stream, filename)
    except Exception as e:
        message = ConversionErrorMessage.ERROR_OPEN_PDF.value + e.message
        return
    out = []
    for page_number in range(len(input_file.pages)):
        page = input_file.pages[page_number]
        try:
            out.append(Pipeline(page.extract_text()))
        except Exception as e:
            message = ConversionErrorMessage.ERROR_PAGE_CONVERT.value%(page_number+1) + e.message
            return

    output_stream = open(download_folder + filename.replace('.pdf', '.txt'), 'w')
    output_stream.write(''.join(out))

def process_file(stream: BytesIO, filename: str, download_folder: str) -> None:
    """
    Main converter function: calls conversion method save as text. 
    """
    save_as_text(stream, filename, download_folder)

