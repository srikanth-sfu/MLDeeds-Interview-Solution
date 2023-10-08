from enum import Enum
import spacy
import os
import transformers
transformers.logging.set_verbosity_error()
from transformers import BertForQuestionAnswering
from transformers import BertTokenizer

ALLOWED_EXTENSIONS = {'pdf'}
class EntityPlaceholder(Enum):
    PERSONAL_INFO = "[personal information]"
    PASSWORD = "[password]"
    USERNAME = "[username]"
    ADDRESS = "[address]"

ENTITY_PLACEHOLDER_MAP = {
    "PERSON": EntityPlaceholder.PERSONAL_INFO.value,
    "USERNAME": EntityPlaceholder.USERNAME.value,
    "ADDRESS": EntityPlaceholder.ADDRESS.value,
    "GPE": EntityPlaceholder.ADDRESS.value,
    "FAC": EntityPlaceholder.ADDRESS.value,
    "LOC": EntityPlaceholder.ADDRESS.value,
}

SPACY_TRANSFORMER_EN = spacy.load('en_core_web_trf')
SPACY_MULTILINGUAL = spacy.load("xx_ent_wiki_sm") #smaller model -- gets better with better models

BERT_MODEL = BertForQuestionAnswering.from_pretrained('bert-large-uncased-whole-word-masking-finetuned-squad')
BERT_TOKENIZER = BertTokenizer.from_pretrained('bert-large-uncased-whole-word-masking-finetuned-squad')

INDEX_FILE = 'index.html'
DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/downloads/'
if not os.path.isdir(DOWNLOAD_FOLDER): os.makedirs(DOWNLOAD_FOLDER)

class ConversionErrorMessage(Enum):
     NO_FILE_ATTACHED_ERROR = "Error: No file attached in request"
     ONLY_PDF_FILES_ERROR = "Error: Only PDF files accepted"
     ERROR_OPEN_PDF = 'Error: Unable to open PDF. Error message: '
     ERROR_PAGE_CONVERT = "Error: Attempting to process page %d. Error Message: "
     SUCCESS_MESSAGE = "File conversion Successful!"

class MSG_COLOR(Enum):
     SUCCESS = "green"
     FAIL = "red"
