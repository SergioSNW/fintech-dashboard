from flask import Flask, jsonify
from dotenv import load_dotenv
import os
from flask_cors import CORS

app = Flask(__name__)
load_dotenv()
CORS(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'
