from flask import Flask, render_template, request
import pandas as pd
import pickle
import mysql.connector

app = Flask(__name__)

# Load ML Model
model = pickle.load(open('LinearRegressionModel.pkl', 'rb'))

# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="osamah@786",
    database="car_price_predictor"
)

cursor = db.cursor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():

    name = request.form['name']
    company = request.form['company']
    year = int(request.form['year'])
    kms_driven = int(request.form['kms_driven'])
    fuel_type = request.form['fuel_type']

    # Prediction
    prediction = model.predict(pd.DataFrame(
        [[name, company, year, kms_driven, fuel_type]],
        columns=['name', 'company', 'year', 'kms_driven', 'fuel_type']
    ))

    output = round(prediction[0], 2)

    # Insert into MySQL
    sql = """
    INSERT INTO car_predictions
    (car_name, company, year, kms_driven, fuel_type, predicted_price)

    VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (
        name,
        company,
        year,
        kms_driven,
        fuel_type,
        output
    )

    cursor.execute(sql, values)
    db.commit()

    return render_template(
        'index.html',
        prediction_text=f'Estimated Price: ₹ {output}'
    )

if __name__ == '__main__':
    app.run(debug=True)