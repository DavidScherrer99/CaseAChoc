import json
from flask import Flask, request, jsonify
import time
import hmac
import hashlib
from binascii import hexlify
from datetime import datetime, timedelta

app = Flask(__name__)

SECRET_KEY = b"secret"
PETZI_DEFAULT_VERSION = "2"


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
    secret_key = hashlib.pbkdf2_hmac("sha256", key, b"salt", 100000)
    return hmac.new(secret_key, data.encode("utf-8"), hashlib.sha256).digest()


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
            save_json(json_data)
            return jsonify({"message": "JSON enregistré avec succès"}), 200
        except Exception as e:
            return jsonify({"error": f"Erreur lors de l'enregistrement du JSON : {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'enregistrement du JSON : {str(e)}"}), 500


@app.route("/retrieve/<int:id>", methods=["GET"])
def get_json(id):
    try:
        json_data = get_json(id)
        return jsonify({"data": json_data}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération du JSON : {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
