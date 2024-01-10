import json
from flask import Flask, request, jsonify
import time
import hmac
import hashlib
from binascii import hexlify
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from stomp import Connection11

app = Flask(__name__)

SECRET_KEY = b"secret"
PETZI_DEFAULT_VERSION = "2"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
db = SQLAlchemy(app)

ACTIVEMQ_HOST = 'localhost'
ACTIVEMQ_PORT = 61613
ACTIVEMQ_TOPIC = '/topic/tickets'

conn = Connection11([(ACTIVEMQ_HOST, ACTIVEMQ_PORT)])
conn.connect(wait=True, headers={'admin': 'admin'})

class JsonStorage(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    value = db.Column(db.String)

def send_ticket_created_message(ticket_data):

    ticket_json = json.dumps(ticket_data)

    conn.send(body=ticket_json, destination=ACTIVEMQ_TOPIC)

def save_json_to_DB(json_data):
    try:
        new_json_storage = JsonStorage(value=json.dumps(json_data))
        db.session.add(new_json_storage)
        db.session.commit()
        send_ticket_created_message(json_data)
        return jsonify({"message": "JSON enregistré avec succès"}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'enregistrement du JSON : {str(e)}"}), 500

def get_json_from_DB(id):
    try:
        json_storage = db.session.get(JsonStorage, id)
        if json_storage:
            return json_storage.value
        else:
            return {"error": f"Aucune donnée trouvée avec l'id: {id}"}, 404
    except Exception as e:
        return {"error": f"Erreur lors de la récupération du JSON : {str(e)}"}, 500


def is_signature_valid(payload, received_signature_header):
    print("Validating signature")
    try:
        parts = received_signature_header.split(",")
        timestamp = int(parts[0].split("=")[1])
        received_signature = parts[1].split("=")[1]

        current_time = int(time.time())
        if abs(current_time - timestamp) > 30:
            return False

        signed_payload = f"{timestamp}.{payload}"
    
        expected_signature = calculate_hmac(signed_payload, SECRET_KEY)

        received_signature_bytes = bytes.fromhex(received_signature)

        return hmac.compare_digest(expected_signature, received_signature_bytes)
    except Exception as e:
        print(f"Error while validating signature: {e}")
        return False


def calculate_hmac(data, key):

    key_bytes = key.encode('utf-8') if isinstance(key, str) else key

    data_bytes = data.encode('utf-8') if isinstance(data, str) else data

    hmac_sha256 = hmac.new(key_bytes, data_bytes, hashlib.sha256)

    return hmac_sha256.digest()


@app.route("/store", methods=["POST"])
def save_json():
    print("Request received")
    petzi_signature = request.headers.get("Petzi-Signature")
    petzi_version = request.headers.get("Petzi-Version")

    if petzi_version != PETZI_DEFAULT_VERSION:
        print("Version not supported")
        return jsonify({"error": "Version non prise en charge"}), 400

    try:
        if not is_signature_valid(request.get_data().decode("utf-8"), petzi_signature):
            return jsonify({"error": "Signature invalide"}), 400
        print("Signature valid")

        try:
            json_data = json.loads(request.get_data().decode("utf-8"))
            save_json_to_DB(json_data)
            return jsonify({"message": "JSON enregistré avec succès"}), 200
        except Exception as e:
            return jsonify({"error": f"Erreur lors de l'enregistrement du JSON : {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'enregistrement du JSON : {str(e)}"}), 500

@app.route("/", methods=["GET"])
def hello_world():
    return jsonify({"message": "Hello World"}), 200

@app.route("/retrieve/<int:id>", methods=["GET"])
def get_json(id):
    try:
        json_data = get_json_from_DB(id)
        return jsonify({"data": json_data}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la recuperation du JSON : {str(e)}"}), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
