"""Runnable entry for `flask run` / containers.

Named wsgi.py on purpose: a root app.py would clash with the app/ package.
Flask discovers wsgi.py the same way as app.py.
"""

from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()
