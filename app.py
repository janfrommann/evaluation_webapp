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
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Session(app)
db = SQLAlchemy(app)

class VotingResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, unique=True, nullable=False)  # Updated from title
    custom_model_votes = db.Column(db.Integer, default=0)
    benchmark_votes = db.Column(db.Integer, default=0)
    voted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<VotingResult %r>' % self.document_id  # Updated from title

# def generate_markdown(sentences, highlights):
#     highlight_dict = {highlight['text']: f'<mark style="background-color: {highlight["color"]};">{highlight["text"]}</mark>' for highlight in highlights}
#     paragraphs = []
#     paragraph = []
#     for sentence in sentences:
#         marked_sentence = highlight_dict.get(sentence, sentence)
#         paragraph.append(marked_sentence)
#         if len(paragraph) >= 5:
#             paragraphs.append(' '.join(paragraph))
#             paragraph = []
#     if paragraph:
#         paragraphs.append(' '.join(paragraph))
#     text = '</p><p>'.join(paragraphs)
#     return f'<p>{text}</p>'


def load_documents():
    with open('data_file_records.json', 'r') as f:
        documents = json.load(f)
    return documents

documents = load_documents()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/random_document')  # Added route decorator
def random_document():
    voted_ids = {result.document_id for result in VotingResult.query.filter_by(voted=True).all()}
    available_documents = [doc for doc in documents if doc['Document_ID'] not in voted_ids]
    
    if not available_documents:
        return "All documents have been voted on", 404

    document = choice(available_documents)
    colors = ['lightgreen', 'lightblue']
    random.shuffle(colors)
    session['color_model_mapping'] = {'Custom Model': colors[0], 'Benchmark Model': colors[1]}
    session['model_color_mapping'] = {colors[0]: 'Custom Model', colors[1]: 'Benchmark Model'}

    # Prepare highlights
    custom_highlights = [{'text': sentence, 'color': colors[0]} for sentence in document['Custom Highlights']]
    benchmark_highlights = [{'text': sentence, 'color': colors[1]} for sentence in document['Benchmark Highlights']]
    highlights = custom_highlights + benchmark_highlights

    return render_template('document.html', document=document, highlights=highlights, color_mapping=session['color_model_mapping'], model_mapping=session['model_color_mapping'])





@app.route('/document/<int:document_id>')  # Updated from title
def document(document_id):
    document = next((doc for doc in documents if doc['Document_ID'] == document_id), None)
    if document is None:
        return "Document not found", 404

    # Define the colors for the highlights
    colors = ['lightgreen', 'lightblue']

    # Prepare highlights
    custom_highlights = [{'text': sentence, 'color': colors[0]} for sentence in document['Custom Highlights']]
    benchmark_highlights = [{'text': sentence, 'color': colors[1]} for sentence in document['Benchmark Highlights']]
    highlights = custom_highlights + benchmark_highlights

    return render_template('document.html', document=document, highlights=highlights)


@app.route('/vote', methods=['POST'])
def vote():
    document_id = request.form.get('title')  # Assuming this form field now contains the Document_ID
    voted_color = request.form.get('color')
    model = session['model_color_mapping'][voted_color]
    result = VotingResult.query.filter_by(document_id=document_id).first()  # Updated from title
    if result is None:
        result = VotingResult(document_id=document_id, custom_model_votes=0, benchmark_votes=0)  # Updated from title
        db.session.add(result)
    if model == 'Custom Model':
        result.custom_model_votes += 1
    else:  # model is 'Benchmark Model'
        result.benchmark_votes += 1

    
    result.voted = True

    db.session.commit()
    flash(f'You voted for the model associated with the color {voted_color}. Thank you for your vote!')
    return redirect(url_for('index'))

@app.route('/results')
def results():
    voting_results = VotingResult.query.all()
    return render_template('results.html', voting_results=voting_results)


engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
inspector = sa.inspect(engine)

# Create database tables if they do not exist

# def table_exists(tablename):
#     engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
#     metadata = MetaData(bind=engine)
#     try:
#         t = Table(tablename, metadata, autoload=True)
#         return engine.dialect.has_table(engine, tablename)
#     except exc.NoSuchTableError:
#         return False

def table_exists(tablename):
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
    inspector = sa.inspect(engine)
    return inspector.has_table(tablename)


with app.app_context():
        if not table_exists("voting_result"):
            db.create_all()
            app.logger.info('Initialized the database!')
        else:
            app.logger.info('Database already contains the voting_result table.')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
