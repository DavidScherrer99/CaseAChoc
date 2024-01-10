from flask import Flask, render_template
import stomp
import threading
import json

app = Flask(__name__)

# Global variable to store received tickets
tickets = []

class TicketSubscriber(stomp.ConnectionListener, threading.Thread):
    def __init__(self, connection, topic):
        super().__init__()
        self.connection = connection
        self.topic = topic

    def on_message(self, message):
        # Process the received message and append to tickets list
        json_string = message.body
        ticket_data = json.loads(json_string)
        tickets.append(ticket_data)

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

# Flask route to render the tickets
@app.route('/')
def index():
    global tickets  # Make sure to use the global variable
    return render_template('index.html', tickets=tickets)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
