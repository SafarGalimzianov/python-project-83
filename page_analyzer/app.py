import os
import psycopg2
from flask import (
    abort,
    get_flashed_messages,
    flash,
    Flask,
    redirect,
    render_template,
    request,
    url_for,
)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DB_URL'] = os.getenv('DB_URL')

conn = psycopg2.connect(app.config['DB_URL'])