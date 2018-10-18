from flask import Flask
from kubecortex_backend.main import main

app = Flask(__name__)

app.register_blueprint(main)
