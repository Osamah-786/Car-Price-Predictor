from flask import Flask, render_template, request, jsonify
import pandas as pd
import pickle
import mysql.connector
from datetime import datetime
import logging

app = Flask(__name__)

# ---------------------------
# Logging Configuration
# ---------------------------
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------------------
# Load Model
# ---------------------------
model = pickle.load(open("LinearRegressionModel.pkl", "rb"))

# ---------------------------
# Database Connection
# ---------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="osamah@786",
        database="car_price_predictor"
    )

# ---------------------------
# Home Route
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------
# Prediction Route
# ---------------------------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        name = request.form["name"]
        company = request.form["company"]
        year = int(request.form["year"])
        kms_driven = int(request.form["kms_driven"])
        fuel_type = request.form["fuel_type"]

        # Validation
        current_year = datetime.now().year

        if year < 1990 or year > current_year:
            return render_template(
                "index.html",
                prediction_text="Invalid Manufacturing Year"
            )

        if kms_driven < 0:
            return render_template(
                "index.html",
                prediction_text="Kilometers Driven cannot be negative"
            )

        # Prediction
        prediction = model.predict(
            pd.DataFrame(
                [[name, company, year, kms_driven, fuel_type]],
                columns=[
                    "name",
                    "company",
                    "year",
                    "kms_driven",
                    "fuel_type"
                ]
            )
        )

        output = round(float(prediction[0]), 2)

        # Save to Database
        db = get_db_connection()
        cursor = db.cursor()

        sql = """
        INSERT INTO car_predictions
        (
            car_name,
            company,
            year,
            kms_driven,
            fuel_type,
            predicted_price,
            prediction_time
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            name,
            company,
            year,
            kms_driven,
            fuel_type,
            output,
            datetime.now()
        )

        cursor.execute(sql, values)
        db.commit()

        cursor.close()
        db.close()

        logging.info(
            f"Prediction Generated | {name} | ₹{output}"
        )

        return render_template(
            "index.html",
            prediction_text=f"Estimated Price: ₹ {output:,.2f}"
        )

    except Exception as e:
        logging.error(str(e))

        return render_template(
            "index.html",
            prediction_text=f"Error: {str(e)}"
        )


# ---------------------------
# API Endpoint
# ---------------------------
@app.route("/api/predict", methods=["POST"])
def api_predict():

    data = request.json

    prediction = model.predict(
        pd.DataFrame(
            [[
                data["name"],
                data["company"],
                data["year"],
                data["kms_driven"],
                data["fuel_type"]
            ]],
            columns=[
                "name",
                "company",
                "year",
                "kms_driven",
                "fuel_type"
            ]
        )
    )

    return jsonify({
        "predicted_price": round(float(prediction[0]), 2),
        "status": "success"
    })


# ---------------------------
# Prediction History
# ---------------------------
@app.route("/history")
def history():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM car_predictions
        ORDER BY id DESC
        LIMIT 20
    """)

    records = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "history.html",
        records=records
    )


# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
