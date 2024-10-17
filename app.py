from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS to handle Cross-Origin Resource Sharing
import mysql.connector
import openai
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Connect to MySQL database
try:
    db = mysql.connector.connect(
        host="localhost",
        user=os.getenv("DB_USER", "root"),  # Use environment variable for username
        password=os.getenv("DB_PASSWORD", "Student@123"),  # Use environment variable for password
        database=os.getenv("DB_NAME", "sensor_data")  # Use environment variable for database name
    )
except mysql.connector.Error as err:
    print(f"Error connecting to MySQL: {err}")
    exit(1)

# OpenAI API key for LLM responses from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY", "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")  # Use environment variable

# Fetch all sensor names from the database
@app.route('/get_sensors', methods=['GET'])
def get_sensors():
    cursor = db.cursor(dictionary=True)
    query = "SELECT DISTINCT sensor_name FROM sensors"
    cursor.execute(query)
    result = cursor.fetchall()

    # Return the list of sensor names
    sensor_names = [row['sensor_name'] for row in result]
    return jsonify(sensor_names)

# Fetch sensor data based on selected sensor
@app.route('/get_sensor_data', methods=['POST'])
def get_sensor_data():
    sensor_name = request.json['sensor_name']  # Get the selected sensor name from user input

    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM sensors WHERE sensor_name = %s ORDER BY timestamp DESC LIMIT 1"
    cursor.execute(query, (sensor_name,))
    result = cursor.fetchone()

    if result:
        sensor_value = result['sensor_value']
        ideal_value = result['ideal_value']

        # Generate AI-based feedback on how to stabilize the sensor
        feedback = generate_stabilization_feedback(sensor_name, sensor_value, ideal_value)

        return jsonify({
            "sensor_name": sensor_name,
            "actual_value": sensor_value,
            "ideal_value": ideal_value,
            "feedback": feedback
        })
    else:
        return jsonify({"error": "Sensor not found"}), 404

# Function to generate AI-based feedback with error handling
def generate_stabilization_feedback(sensor_name, sensor_value, ideal_value):
    try:
        # Use OpenAI API to generate feedback
        prompt = (
            f"The sensor '{sensor_name}' has an actual value of {sensor_value}, but the ideal value is {ideal_value}. "
            f"Explain how AI and machine learning could help stabilize the sensor performance."
        )

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=100
        )

        return response.choices[0].text.strip()

    except Exception as e:
        print(f"Error in OpenAI API call: {e}")
        return "Error generating feedback. Please try again."

if __name__ == '__main__':
    app.run(debug=True)
