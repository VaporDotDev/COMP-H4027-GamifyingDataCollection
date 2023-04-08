import json
import os
import zipfile
from functools import wraps

import cachecontrol as cachecontrol
import cv2
import google
import numpy as np
import requests
import tensorflow as tf
from dotenv import load_dotenv
from flask import Flask, render_template, session, abort, redirect, request, jsonify, send_file
from google.oauth2 import id_token

from classes.User import User, db
from google_auth import get_flow

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

app = Flask(__name__)
app.secret_key = json.load(open("client_secret.json", "r"))["web"]["client_secret"]

app.config["SQLALCHEMY_DATABASE_URI"] = f"mariadb+mariadbconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
db.init_app(app)

flow, GOOGLE_CLIENT_ID = get_flow()

plate_model = tf.keras.models.load_model('models/plate.h5')
vehicle_model = tf.keras.models.load_model('models/vehicle.h5')


def login_is_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return redirect("/login")
        else:
            return f()

    return wrapper


@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html')


@app.route('/scan')
@login_is_required
def scan():
    return render_template('scan.html')


@app.route('/guide')
def guide():
    return render_template('guide.html')


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["POST"])
def register():
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = google.oauth2.id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    # Check if user already exists
    user = User.query.filter_by(google_id=id_info["sub"]).first()
    if user is not None:
        return redirect("/")
    else:
        # Add the user to the database
        user = User(
            google_id=id_info["sub"],
            email=id_info["email"],
            password="",
            name=id_info["name"],
            picture=id_info["picture"],
            interest="",
            trusted=False
        )
        db.session.add(user)
        db.session.commit()

    return redirect("/")


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = google.oauth2.id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    session["google_id"] = id_info["sub"]

    # Verify if the user exists in the database
    user = User.query.filter_by(google_id=session["google_id"]).first()

    if user is None:
        # Present a privacy policy and ask for consent
        return render_template("privacy.html")
    else:
        # Log the user in
        return redirect("/")


@app.route('/download')
@login_is_required
def download():
    # Create a zip file
    with zipfile.ZipFile("images.zip", "w") as zip_file:
        # Write each file in the images directory to the zip file
        for filename in os.listdir("images"):
            zip_file.write(os.path.join("images", filename))

    # Send the zip file to the user
    response = send_file("images.zip", as_attachment=True)

    # Delete the zip file
    os.remove("images.zip")

    return response


@app.route('/predict', methods=['POST', 'GET'])
@login_is_required
def predict():
    # Get the image from the request
    image = request.files['image'].read()

    # Convert the image to a numpy array
    image = np.frombuffer(image, np.uint8)

    # Decode the image using the TIFF flag
    image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)

    # Get the number of files in the images folder excluding the CSV file
    num_files = len([file for file in os.listdir('images') if file.endswith('.tiff')])

    # Save the image to disk with incremented file name
    cv2.imwrite(f"images/image_{num_files + 1}.tiff", image)

    # Resize the image to (224, 224)
    image = cv2.resize(image, (224, 224))

    # Normalize the image
    image = image / 255.0

    # Remove the alpha channel if the image has it
    if image.shape[-1] == 4:
        image = image[..., :3]

    # Make a prediction with the model
    plate_prediction = plate_model.predict(image[np.newaxis, ...])
    vehicle_prediction = vehicle_model.predict(image[np.newaxis, ...])

    # Create a CSV file with image name and prediction
    with open('images/data.csv', 'a') as f:
        # Get the prediction values
        xmin_plate, ymin_plate, xmax_plate, ymax_plate = plate_prediction[0]
        xmin_vehicle, ymin_vehicle, xmax_vehicle, ymax_vehicle = vehicle_prediction[0]

        # Multiply the values by the image width and height
        xmin_plate, ymin_plate, xmax_plate, ymax_plate = xmin_plate * image.shape[1], ymin_plate * image.shape[
            0], xmax_plate * image.shape[1], ymax_plate * image.shape[0]
        xmin_vehicle, ymin_vehicle, xmax_vehicle, ymax_vehicle = xmin_vehicle * image.shape[1], ymin_vehicle * \
                                                                 image.shape[0], xmax_vehicle * image.shape[
                                                                     1], ymax_vehicle * image.shape[0]

        # Convert the values to integers
        xmin_plate, ymin_plate, xmax_plate, ymax_plate = int(xmin_plate), int(xmin_plate), int(xmax_plate), int(
            ymax_plate)
        xmin_vehicle, ymin_vehicle, xmax_vehicle, ymax_vehicle = int(xmin_vehicle), int(ymin_vehicle), int(
            xmax_vehicle), int(ymax_vehicle)

        # Write the values to the CSV file
        f.write(f"image_{num_files + 1}.tiff,{xmin_plate},{ymin_plate},{xmax_plate},{ymax_plate},Plate\n")
        f.write(f"image_{num_files + 1}.tiff,{xmin_vehicle},{ymin_vehicle},{xmax_vehicle},{ymax_vehicle},Vehicle\n")
    response = {
        "plate": plate_prediction.tolist(),
        "vehicle": vehicle_prediction.tolist()
    }

    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
