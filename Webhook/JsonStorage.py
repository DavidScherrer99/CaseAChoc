from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
db = SQLAlchemy(app)

class JsonStorage(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    value = db.Column(db.String)

@app.route("/store", methods=["POST"])
def save_json():
    try:
        json_data = request.get_json()
        new_json_storage = JsonStorage(value=json_data)
        db.session.add(new_json_storage)
        db.session.commit()
        return jsonify({"message": "JSON enregistré avec succès"}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'enregistrement du JSON : {str(e)}"}), 500

@app.route("/retrieve/<int:id>", methods=["GET"])
def get_json(id):
    try:
        json_storage = JsonStorage.query.get(id)
        if json_storage:
            return jsonify({"data": json_storage.value}), 200
        else:
            return jsonify({"error": f"Aucune donnée trouvée avec l'id: {id}"}), 404
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération du JSON : {str(e)}"}), 500

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
