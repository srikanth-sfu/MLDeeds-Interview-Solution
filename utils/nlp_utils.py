import warnings
warnings.filterwarnings("ignore")
import re
import string
from enum import Enum
from config import ENTITY_PLACEHOLDER_MAP, SPACY_TRANSFORMER_EN, SPACY_MULTILINGUAL, BERT_MODEL, BERT_TOKENIZER
from nltk.tokenize import word_tokenize
import torch

# text cleanup
def cleanup(text):
  text = text.split("\n")
  clean_text = ""
  for line in text:
    clean_text+=" "+ line.strip()

  clean_text = clean_text.strip()
  return clean_text

# use regex to replace account numbers and emails
# account assumptions based on given text : [4d-4d-4d]
def redact_account_and_email(text: str) -> str:
  account_pattern = re.compile(r'\b\d{4}[- ]*?\d{4}[- ]*?\d{4}\b')
  email_pattern = re.compile(r'\b[\w.-]+?@\w+?\.\w+?\b')

  text_acc = account_pattern.sub('[account number]', text)
  text_email = email_pattern.sub('[personal information]', text_acc)
  return text_email

def proc_wordsonly(redacted_text, entity):
    if (redacted_text.startswith(entity) or not redacted_text[redacted_text.find(entity) - 1].isalnum()) and \
           (redacted_text.endswith(entity) or not redacted_text[redacted_text.find(entity) + len(entity)].isalnum()):
        return True

    return False 

# use NER from spacy (en; transformer) to find Names, Addresses (+GPE, FAC) 
def redact_personal_info(text: str) -> str:
    entities = SPACY_TRANSFORMER_EN(text).ents
    # entities = nlp(text).ents
    redacted_text = text
    for entity in entities:
        placeholder = ENTITY_PLACEHOLDER_MAP.get(entity.label_)
        if placeholder is not None and proc_wordsonly(redacted_text, entity.text):
            redacted_text = redacted_text.replace(entity.text, placeholder)
    return redacted_text

# use NER from spacy (multilingual; transformer) to find Names, Addresses (+GPE, FAC) 
def redact_personal_info_multi(text: str) -> str:
    entities = SPACY_MULTILINGUAL(text).ents
    redacted_text = text
    for entity in entities:
        placeholder = None
        if entity.label_ in ["LOC"]:
          placeholder = ENTITY_PLACEHOLDER_MAP.get(entity.label_)
        if placeholder is not None and proc_wordsonly(redacted_text, entity.text):
            redacted_text = redacted_text.replace(entity.text, placeholder)
    return redacted_text

#################### redact username and password ##############################
# for username and password detection, I leverage BERT and reframe the task
# as QA - question answering - with some text containing the term "username" or
# "password" acting as the passage. 
################################################################################

# find all indices that the word username/password exists in the list
def get_lines_with_un_pwd_keywords(text_list):
  # TODO: Needs to be robust
  un_keyword_list = ["usernames", "username", "usernam", "userna", "usern"]
  pwd_keyword_list = ["password", "passwords", "passwrd", "pwd"]

  un_key_lines = []
  pwd_key_lines = []
  for i,line in enumerate(text_list):
    tokenizer_out = set([x.lower() for x in word_tokenize(line.text)])
    un_common = list(tokenizer_out & set(un_keyword_list))
    pwd_common = list(tokenizer_out & set(pwd_keyword_list))
    if len(un_common) > 0:
      un_key_lines.append(i)
    if len(pwd_common) > 0:
      pwd_key_lines.append(i)

  return un_key_lines, pwd_key_lines

def get_usernames(un_id_list, text_list):
  usernames = []
  for id in un_id_list:
    start = id-1 if id>0 else id
    end = id+2
    chunk = " ".join(line.text for line in text_list[start:end]).strip()

    un = ask_bert("username", chunk)
    un = un.replace(" ", "")

    usernames.append(un.strip())

  return list(set(usernames))

def get_passwords(pwd_id_list, text_list):
  passwords = []
  for id in pwd_id_list:
    start = id-1 if id>0 else id
    end = id+2
    chunk = " ".join(line.text for line in text_list[start:end]).strip()

    pwd = ask_bert("password", chunk)
    pwd = pwd.replace(" ", "")

    passwords.append(pwd.strip())

  return list(set(passwords))


def ask_bert(question, context):
  def prepare_qa_input(quest, context):
    encoding = BERT_TOKENIZER.encode_plus(text=quest,text_pair=context)

    inputs = encoding['input_ids']  #Token embeddings
    sentence_embedding = encoding['token_type_ids']  #Segment embeddings
    tokens = BERT_TOKENIZER.convert_ids_to_tokens(inputs) #input tokens

    return inputs, sentence_embedding, tokens

  if question == "username":
    quest = "What is the username?"
  elif question == "password":
    quest = "What is the password?"

  # prepare question and context
  inputs, sentence_embedding, tokens = prepare_qa_input(quest, context)

  # model output
  bert_out = BERT_MODEL(input_ids=torch.tensor([inputs]), token_type_ids=torch.tensor([sentence_embedding]))

  # extract logit tensors from output tuple
  start_scores = bert_out[0]
  end_scores = bert_out[1]

  # get start and end pos
  start_index = torch.argmax(start_scores)
  end_index = torch.argmax(end_scores)

  # get raw tokenized answer
  answer = ' '.join(tokens[start_index:end_index+1])

  # change subword tokens back to words
  corrected_answer = ''
  for word in answer.split():
      #if subword
      if word[0:2] == '##':
          corrected_answer += word[2:]
      else:
          corrected_answer += ' ' + word

  return corrected_answer

# packaged function to redact username and passwords
def redact_usernames_passwords(textj):
  # split text into sentences
  doc = SPACY_TRANSFORMER_EN(textj)
  text_list = [sent for sent in doc.sents]

  # get indices wherever usernames and passwords exist
  un_key_lines, pwd_key_lines = get_lines_with_un_pwd_keywords(text_list)

  usernames = get_usernames(un_key_lines, text_list)
  passwords = get_passwords(pwd_key_lines, text_list)

  redacted_text = ""
  punckts = string.punctuation
  for word in textj.split(" "):
    if word not in punckts:
      punckt = None
      clean_word = str(word.lower())
      if clean_word[-1] in punckts:
        punckt = clean_word[-1]
        clean_word = clean_word[:-1]
      if clean_word in usernames:
        redacted_text += "[username] " if punckt is None else "[username]" + punckt + " "
      elif clean_word in passwords:
        redacted_text += "[password] " if punckt is None else "[password]" + punckt + " "
      else:
        redacted_text += word.strip()+ " "
    else:
      redacted_text += word.strip()+ " "

  return redacted_text.strip()

def Pipeline(text: str) -> str:
  # quick cleanup
  textj = cleanup(text)

  # redact in steps
  text_regex = redact_account_and_email(textj)
  text_no_un_pwd = redact_usernames_passwords(text_regex)
  redact_en = redact_personal_info(text_no_un_pwd)
  final_redacted_text = redact_personal_info_multi(redact_en)

  return final_redacted_text

if __name__ == '__main__':
  text="""Memoirs of a Digital Nomad
  It began on a crisp autumn day. I, Thomas Richardson, was sat at my usual spot in "Café Serenity" on
  1456 Pine Boulevard, Manhattan, when an idea sparked. An idea that would have me bid farewell to the
  regular 9 -to-5 life and embrace the winds of digital c hange.
  My initial journey was financed with the generous help of "Urban Bank". As a testimony to the rush of
  the moment, I remember hurriedly scribbling down my account details - Account Number 3256 -7654 -
  2900 - on a napkin, for a quick wire transfer from a freela nce gig. The username, somewhat reflective of
  my surroundings, was CoffeeTom91, and the password was AutumnLeaf$12.
  One of my first stops was in Berlin, where I met up with Clara Müller. We'd connected over an online
  platform, which used my primary email, tommy.richard@wanderer.net , and my password was
  GlobeTrotter#89. Clara was a wealth of knowledge. Living at 89B Friedrichstraße, Berlin, she introduced
  me to the local tech community. She was especially keen on sharing insights from her bank - Deutsche
  Financial - where her usernam e was BerlinClara92 and her account number was an interesting pattern,
  1122 -3344 -5566. Password? She jokingly said it was CurryWurst$56.
  Between coffees, codes, and Wi -Fi passwords, I hopped cities and continents. Often, I'd collaborate with
  fellow nomads. Like the time in Osaka, where Hiroshi Tanaka, from his lofty apartment at 12 -34
  Shinmachi, entrusted me with a project, giving me access  to a shared workspace. His credentials? Email
  was hiroshi.t@japanmail.jp  with the password SushiLover90.
  As these digital memories flood back, it's crucial to remember the essence of the journey. The beauty of
  varied landscapes, the joy of diverse cultures, and the threads of digital connections that tie it all
  together."""

  print(Pipeline(text))
