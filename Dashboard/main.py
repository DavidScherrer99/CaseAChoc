from flask import Flask, render_template, Response, request
import json
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def event_stream():
    while True:
        # Fetch data from the sender server
        response = requests.get('http://127.0.0.1:5001/tickets', stream=True)

        # Forward the received data to connected clients
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk.decode('utf-8')

#@app.route('/tickets')
#def index():
#   return Response(event_stream(), content_type='text/event-stream')

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')
    

if __name__ == '__main__':
    app.run(debug=True, port=5002)
