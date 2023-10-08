pip install -r requirements.txt
pip install torch==2.1.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
pip install spacy spacy-transformers transformers tqdm
python -m spacy download en_core_web_sm
python -m spacy download xx_ent_wiki_sm
python -m spacy download en_core_web_trf
python -c "import nltk; nltk.download('punkt')"
