from flask import Flask, render_template, Response, request
import stomp
import threading
import json
from queue import Queue
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

tickets_queue = Queue()

class TicketSubscriber(stomp.ConnectionListener, threading.Thread):
    def __init__(self, connection, topic):
        super().__init__()
        self.connection = connection
        self.topic = topic

    def on_message(self, message):
        # Process the received message and append to tickets list
        json_string = message.body
        tickets_data = json.loads(json_string)
        tickets_queue.put(tickets_data)

    def run(self):
        self.connection.set_listener('', self)
        self.connection.connect('admin', 'admin', wait=True)
        self.connection.subscribe(destination=self.topic, id=1, ack='auto')

# ActiveMQ configuration
active_mq_host = 'localhost'
active_mq_port = 61613
active_mq_topic = '/topic/tickets'

# Create ActiveMQ connection
conn = stomp.Connection([(active_mq_host, active_mq_port)])
subscriber = TicketSubscriber(conn, active_mq_topic)

# Start the subscriber thread
subscriber.start()

def event_stream():
    while True:
        if tickets_queue.empty() == False:   
            # Retrieve ticket data from the queue with a timeout
            tickets_data = tickets_queue.get(timeout=1)
            # Convert ticket data to JSON-formatted string
            json_string = json.dumps(tickets_data)
            # Send the JSON data to clients
            yield f"data: {json_string}\n\n"
        

@app.route('/')
def index():
    return ""

@app.route('/tickets')
def sse():
    return Response(event_stream(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5001)
