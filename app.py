from flask import Flask, render_template, request
import os  # Import the 'os' module

app = Flask(__name__)

# Import necessary libraries and modules
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain

# Directory path
directory = 'C:\\Users\\Samirit Saha\\OneDrive\\Desktop\\datatset'

# Function to load the text documents
def load_docs(directory):
    loader = DirectoryLoader(directory)
    documents = loader.load()
    return documents

documents = load_docs(directory)

# Split the documents into chunks using recursive character splitter
def split_docs(documents, chunk_size=800, chunk_overlap=0):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents(documents)
    return docs

# Store the split documents in the 'docs' variable
docs = split_docs(documents)

# Initialize Sentence Transformer embeddings
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Use Chroma as a vector store and store the documents in it
db = Chroma.from_documents(docs, embeddings)

# Access the OpenAI API key from the environment variable
openai_api_key = os.environ.get("OPENAI_API_KEY")  # Retrieve the API key

# Load the Language Model (LLM)
model_name = "gpt-3.5-turbo"
llm = ChatOpenAI(model_name=model_name, api_key=openai_api_key)  # Pass the API key to the model

# Load the Q&A chain to get answers to queries
chain = load_qa_chain(llm, chain_type="stuff", verbose=True)

# Define the route for the index page
@app.route('/')
def index():
    return render_template('index.html')

# Define the route for handling user queries
@app.route('/query', methods=['POST'])
def query():
    user_query = request.form.get('query')
    
    # Add the ranking prompt by default
    ranking_prompt = " go thoroughly through the document you're trained on and rank by rating and dont show their phone number. Make sure you dont mention that you have omitted their phone number. "
    user_query_with_ranking = user_query + ranking_prompt 
    
    # Perform the similarity search
    matching_docs = db.similarity_search(user_query_with_ranking)
    
    # Run the query with the updated ranking
    answer = chain.run(input_documents=matching_docs, question=user_query_with_ranking)
    
    # Process the answer to remove phone numbers
    processed_answer = process_answer(answer)
    
    return render_template('result.html', answer=processed_answer)

# Function to process the answer and remove phone numbers
def process_answer(answer):
    # Split the answer into lines
    lines = answer.split('\n')
    
    # Initialize an empty list to store processed lines
    processed_lines = []
    
    for line in lines:
        # Check if the line contains a phone number, indicated by "Phone Number:"
        if "Phone Number:" not in line:
            # If the line does not contain a phone number, add it to the processed lines
            processed_lines.append(line)
    
    # Join the processed lines with line breaks
    processed_answer = '<br>'.join(processed_lines)
    
    return processed_answer

if __name__ == '__main__':
    app.run(debug=True)
