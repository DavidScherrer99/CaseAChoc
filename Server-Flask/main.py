from flask import Flask, render_template, Response, request
import stomp
import threading
import json
from queue import Queue
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

tickets_queue = Queue()
conn = None
subscription_created = False

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
        self.connection.connect('consumer', 'consumer', wait=True)
        self.connection.subscribe(destination=self.topic, id=1, ack='auto', headers={'activemq.subscriptionName': 'consumer'})

# ActiveMQ configuration
active_mq_host = 'activemq_container'
active_mq_port = 61613
active_mq_topic = '/topic/tickets'

def setup_active_mq():
    global conn, subscription_created
    # Create ActiveMQ connection only if not already created
    if not conn:
        conn = stomp.Connection([(active_mq_host, active_mq_port)])
        # Create and start the subscriber only if the subscription hasn't been created
        if not subscription_created:
            subscriber = TicketSubscriber(conn, active_mq_topic)
            subscriber.start()
            subscription_created = True

@app.before_request
def before_request():
    setup_active_mq()

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
    app.run(debug=True, host="0.0.0.0", threaded=True, port=5001)
