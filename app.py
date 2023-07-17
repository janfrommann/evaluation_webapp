from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import json
import random
from random import choice
import sqlalchemy as sa  # new import
from sqlalchemy import MetaData, Table, create_engine, exc
from flask import current_app


app = Flask(__name__)
app.secret_key = '123456'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dbhigh_user:R9kIBmxZ8vbglRrJH2iPwheeR1X7DfSV@dpg-ciq8d7unqql4qa4k57pg-a/dbhigh'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Session(app)
db = SQLAlchemy(app)

class VotingResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    custom_model_votes = db.Column(db.Integer, default=0)
    gpt_model_votes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<VotingResult %r>' % self.title

def generate_markdown(text, highlights):
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
    document = choice(documents)
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
@app.route('/vote', methods=['POST'])
def vote():
    title = request.form.get('title')
    voted_color = request.form.get('color')
    model = session['color_model_mapping'][voted_color]
    result = VotingResult.query.filter_by(title=title).first()
    if result is None:
        result = VotingResult(title=title, custom_model_votes=0, gpt_model_votes=0)  # explicitly set vote counts to 0
        db.session.add(result)
    if model == 'Custom Model':
        result.custom_model_votes += 1
    else:  # model is 'GPT_Model'
        result.gpt_model_votes += 1
    db.session.commit()
    flash(f'You voted for the model associated with the color {voted_color}. Thank you for your vote!')
    return redirect(url_for('index'))

engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
inspector = sa.inspect(engine)

# Create database tables if they do not exist

def table_exists(tablename):
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
    metadata = MetaData(bind=engine)
    try:
        t = Table(tablename, metadata, autoload=True)
        return engine.dialect.has_table(engine, tablename)
    except exc.NoSuchTableError:
        return False


with app.app_context():
        if not table_exists("voting_result"):
            db.create_all()
            app.logger.info('Initialized the database!')
        else:
            app.logger.info('Database already contains the voting_result table.')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
