from flask import Flask, jsonify
import asyncio
from app.backend.tasks import fetch_data

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def get_data():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(fetch_data())
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)