from flask import Flask, request, jsonify
from store import Store

store = Store(sqlite_path="kv_store.sqlite")
app = Flask(__name__)

@app.route("/set", methods=["POST"])
def set_key():
    data = request.get_json()
    key = data["key"]
    value = data["value"]
    store.set(key, value)
    store.flush_to_sqlite()
    return jsonify({"key": key, "value": value})

@app.route("/get/<key>", methods=["GET"])
def get_key(key):
    val = store.get(key)
    return jsonify({"key": key, "value": val})

@app.route("/delete/<key>", methods=["DELETE"])
def delete_key(key):
    store.delete(key)
    store.flush_to_sqlite()
    return jsonify({"deleted": key})

@app.route("/snapshot", methods=["GET"])
def snapshot():
    return jsonify(store.snapshot())

@app.route("/begin", methods=["POST"])
def begin_tx():
    store.begin()
    return jsonify({"status": "transaction started"})

@app.route("/commit", methods=["POST"])
def commit_tx():
    try:
        store.commit()
        store.flush_to_sqlite()
        return jsonify({"status": "committed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 409

@app.route("/rollback", methods=["POST"])
def rollback_tx():
    store.rollback()
    return jsonify({"status": "rolled back"})

@app.route("/close", methods=["POST"])
def close_store():
    store.flush_to_sqlite()
    store.close()
    return jsonify({"status": "store closed"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
