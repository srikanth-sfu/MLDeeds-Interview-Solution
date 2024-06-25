# MLDeeds

## Summary

Redactions were applied using three distinct methods, each with varying levels of sophistication:

1.The first method employed a re-based framework to redact account numbers and emails. The assumption for account numbers was the presence of repetitive patterns of 3 sets of 4 digits separated by hyphens, with arbitrary spaces preceding or following the hyphens. It's important to note that some of these issues may also be attributed to PyPDF2 I/O.

2. The second method involved leveraging BERT for the detection of usernames and passwords. The approach reframed the task as a question-answering (QA) problem, with the text containing the terms "username" or "password" acting as the passage. This method adds a layer of sophistication to the redaction process.

3. The third method employed Spacy NER for redacting names and addresses. A transformer model, specifically a small English model, was utilized. The labels FAC and GPE were used for the redaction process. Additionally, a small multilingual model was employed to handle corner cases where addresses were in languages other than English. The decision to use small models was driven by computational constraints.

## Running demo instructions

### Step 1: Setup virtualenv

```
virtualenv MLDeeds
source +x MLDeeds/bin/activate
```

### Step 2: Run installation script

```
./install.sh
```

### Step 3: Launch App

```
MLDeeds/bin/flask run
```

### Step 4: Test App

Open ```http://127.0.0.1:5000```
On the WebGUI, upload the pdf file you want to redact. After sometime, you would be able to download
the redacted output to the folder of your choice. Note: The processing time depends on the size of your pdf file.

## Running a clickable version

I attempted to use PyInstall and ran into issues due to complicated dependencies for the repo. I attempted to build a double click
version using shell script (``redact_app.sh``).
