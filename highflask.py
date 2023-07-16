from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session  # added this line
import json
import random
from flask import Markup
from random import choice

app = Flask(__name__)
app.secret_key = '123456'
app.config['SESSION_TYPE'] = 'filesystem'  # Session data will be stored in the filesystem
Session(app)

def generate_markdown(text, highlights):
    # Find and replace highlights with colored marks
    for highlight in highlights:
        text = text.replace(highlight['text'], f'<mark style="background-color: {highlight["color"]};">{highlight["text"]}</mark>')
    sentences = text.split('. ')
    paragraphs = [' '.join(sentences[i:i+5]) for i in range(0, len(sentences), 5)]
    text = '</p><p>'.join(paragraphs)
    return f'<p>{text}</p>'

def load_documents():
    with open('clv_data.json', 'r') as f:
        documents = json.load(f)
    return documents

documents = load_documents()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/random_document', methods=['GET'])
def random_document():
    document = choice(documents)  # Select a random document from the list
    # Replace highlights in the text with colored marks
    colors = ['lightgreen', 'lightblue']
    random.shuffle(colors)
    highlights = [{'text': document['highlight_custom_model'], 'color': colors[0]}, {'text': document['highlight_gpt3.5'], 'color': colors[1]}]
    session['color_model_mapping'] = {colors[0]: 'Custom Model', colors[1]: 'GPT_Model'}
    document['content'] = generate_markdown(document['content'], highlights)
    return render_template('document.html', document=document)

@app.route('/document/<title>')
def document(title):
    document = next((doc for doc in documents if doc['title'] == title), None)
    if document is None:
        return "Document not found", 404
    highlights = [{'text': document['highlight_custom_model'], 'color': 'lightgreen'}, {'text': document['highlight_gpt3.5'], 'color': 'lightblue'}]
    document['content'] = generate_markdown(document['content'], highlights)
    return render_template('document.html', document=document)

@app.route('/vote', methods=['POST'])
def vote():
    with open('results.json') as f:
        results = json.load(f)
    title = request.form.get('title')
    voted_color = request.form.get('color')
    model = session['color_model_mapping'][voted_color]
    for result in results:
        if result['Title'] == title:
            result[model] += 1
            break
    else:
        results.append({'Title': title, 'Custom Model': 0, 'GPT_Model': 0, model: 1})
    with open('results.json', 'w') as f:
        json.dump(results, f)
    flash(f'You voted for the model associated with the color {voted_color}. Thank you for your vote!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)














# from flask import Flask, render_template, request, redirect, url_for
# import json
# import random
# from flask import Markup
# from random import choice

# app = Flask(__name__)

# def generate_markdown(text, highlights):
#     # Find and replace highlights with colored marks
#     for highlight in highlights:
#         original_text = text
#         text = text.replace(highlight['text'], f'<mark style="background-color: {highlight["color"]};">{highlight["text"]}</mark>')
#         if original_text == text:
#             print(f"Could not highlight: {highlight['text']}")

#     # Split text into sentences
#     sentences = text.split('. ')
    
#     # Group sentences into paragraphs of 5
#     paragraphs = [' '.join(sentences[i:i+5]) for i in range(0, len(sentences), 5)]
    
#     # Join paragraphs with paragraph tags
#     text = '</p><p>'.join(paragraphs)
    
#     return f'<p>{text}</p>'

# def load_documents():
#     with open('clv_data.json', 'r') as f:
#         documents = json.load(f)
#     return documents

# documents = load_documents()

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/random_document', methods=['GET'])
# def random_document():
#     document = choice(documents) # Select a random document from the list
#     highlights = [{'text': document['highlight_custom_model'], 'color': 'lightgreen'}, {'text': document['highlight_gpt3.5'], 'color': 'lightblue'}]
#     document['content'] = generate_markdown(document['content'], highlights)
#     return render_template('document.html', document=document)

# @app.route('/document/<title>')
# def document(title):
#     # Find the document with the matching title
#     document = next((doc for doc in documents if doc['title'] == title), None)

#     # If no document with the title was found, show an error
#     if document is None:
#         return "Document not found", 404

#     # Replace highlights in the text with colored marks
#     highlights = [{'text': document['highlight_custom_model'], 'color': 'lightgreen'}, {'text': document['highlight_gpt3.5'], 'color': 'lightblue'}]
#     document['content'] = generate_markdown(document['content'], highlights)

#     return render_template('document.html', document=document)


# @app.route('/vote', methods=['POST'])
# def vote():
#     # load results from file
#     with open('results.json') as f:
#         results = json.load(f)

#     # increment the count for the chosen model
#     title = request.form.get('title')
#     model = request.form.get('model')
#     for result in results:
#         if result['Title'] == title:
#             result[model] += 1
#             break
#     else:
#         results.append({'Title': title, 'Custom Model': 0, 'GPT_Model': 0, model: 1})

#     # save results back to file
#     with open('results.json', 'w') as f:
#         json.dump(results, f)

#     return redirect(url_for('index'))

# if __name__ == '__main__':
#     app.run(debug=True)

