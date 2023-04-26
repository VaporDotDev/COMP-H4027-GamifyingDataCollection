import json
import os
import uuid
import zipfile
from functools import wraps

import cachecontrol as cachecontrol
import cv2
import easyocr
import google
import numpy as np
import requests
import tensorflow as tf
from flask import (
    Flask,
    render_template,
    session,
    abort,
    redirect,
    request,
    jsonify,
    Response,
)
from google.oauth2 import id_token

from classes.Gamification import p_year, p_registration
from classes.User import User
from functions.database import init_app
from functions.google_auth import get_flow
from functions.parse_license_plate import plate_correction

cwd = os.getcwd()

app = Flask(__name__)
app.secret_key = json.load(open(os.path.join(cwd, "client_secret.json"), "r"))["web"]["client_secret"]

init_app(app)

flow, GOOGLE_CLIENT_ID = get_flow()

plate_model = tf.keras.models.load_model(os.path.join(cwd, "models/plate.h5"))
vehicle_model = tf.keras.models.load_model(os.path.join(cwd, "models/vehicle.h5"))


def login_is_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return redirect("/login")
        else:
            return f()

    return wrapper


@app.route("/")
def home():  # put application's code here
    return render_template("index.html")


@app.route("/scan")
@login_is_required
def scan():
    return render_template("scan.html")


@app.route("/guide")
def guide():
    return render_template("guide.html")


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
        id_token=credentials._id_token, request=token_request, audience=GOOGLE_CLIENT_ID
    )

    # Check if user already exists
    user = User.query.filter_by(google_id=id_info["sub"]).first()
    if user is not None:
        return redirect("/")
    else:
        # Add the user to the database
        User.create_user(
            google_id=id_info["sub"],
            name=id_info["name"],
            email=id_info["email"],
            picture=id_info["picture"],
        )

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
        id_token=credentials._id_token, request=token_request, audience=GOOGLE_CLIENT_ID
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


@app.route("/download")
@login_is_required
def download():
    try:
        # Create a zip file
        with zipfile.ZipFile("images.zip", "w") as zip_file:
            # Write each file in the images directory to the zip file
            for filename in os.listdir(os.path.join(cwd, "images")):
                zip_file.write(os.path.join("images", filename))

        with open(os.path.join(cwd, "images.zip"), 'rb') as f:
            data = f.readlines()

        response = Response(data, headers={
            'Content-Type': 'application/zip',
            'Content-Disposition': 'attachment; filename=%s;' % "images.zip"
        })

    finally:
        # Delete the zip file
        if os.path.exists(os.path.join(cwd, "images.zip")):
            os.remove("images.zip")

    return response


@app.route("/predict", methods=["POST", "GET"])
@login_is_required
def predict():
    # Get the image from the request
    image = request.files["image"].read()

    # Convert the image to a numpy array
    image = np.frombuffer(image, np.uint8)

    # Create a copy of the image
    image_copy = image.copy()

    # Decode the image using the TIFF flag
    image = cv2.imdecode(
        image, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH
    )

    # Save the image to disk with random filename
    filename = str(uuid.uuid4()) + ".jpg"
    cv2.imwrite(os.path.join(cwd, "images", filename), image)

    # Resize the image to (224, 224)
    image = cv2.resize(image, (224, 224))

    # Normalize the image
    image = image / 255.0

    # Remove the alpha channel if the image has it
    if image.shape[-1] == 4:
        image = image[..., :3]

    # Make a prediction with the model
    vehicle_prediction = vehicle_model.predict(image[np.newaxis, ...])
    xmin_vehicle, ymin_vehicle, xmax_vehicle, ymax_vehicle = vehicle_prediction[0]
    xmin_vehicle, ymin_vehicle, xmax_vehicle, ymax_vehicle = (
        xmin_vehicle * image.shape[1],
        ymin_vehicle * image.shape[0],
        xmax_vehicle * image.shape[1],
        ymax_vehicle * image.shape[0],
    )
    xmin_vehicle, ymin_vehicle, xmax_vehicle, ymax_vehicle = (
        int(xmin_vehicle),
        int(ymin_vehicle),
        int(xmax_vehicle),
        int(ymax_vehicle),
    )

    plate_prediction = plate_model.predict(image[np.newaxis, ...])
    xmin_plate, ymin_plate, xmax_plate, ymax_plate = plate_prediction[0]
    xmin_plate, ymin_plate, xmax_plate, ymax_plate = (
        xmin_plate * image.shape[1],
        ymin_plate * image.shape[0],
        xmax_plate * image.shape[1],
        ymax_plate * image.shape[0],
    )
    xmin_plate, ymin_plate, xmax_plate, ymax_plate = (
        int(xmin_plate),
        int(xmin_plate),
        int(xmax_plate),
        int(ymax_plate),
    )

    image_copy = np.frombuffer(image_copy, np.uint8)
    image_copy = cv2.imdecode(
        image_copy, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH
    )
    image_copy = cv2.cvtColor(image_copy, cv2.COLOR_BGR2GRAY)
    # Get the coordinates of the plate
    xmin_roi, ymin_roi, xmax_roi, ymax_roi = plate_prediction[0]
    # Scale the coordinates according to the image size
    xmin_roi, ymin_roi, xmax_roi, ymax_roi = (
        xmin_roi * image_copy.shape[1],
        ymin_roi * image_copy.shape[0],
        xmax_roi * image_copy.shape[1],
        ymax_roi * image_copy.shape[0],
    )
    # Convert the coordinates to integers
    xmin_roi, ymin_roi, xmax_roi, ymax_roi = (
        int(xmin_roi),
        int(ymin_roi),
        int(xmax_roi),
        int(ymax_roi),
    )

    # Crop the image
    plate = image_copy[ymin_roi - 20: ymax_roi + 20, xmin_roi - 20: xmax_roi + 20]
    reader = easyocr.Reader(["en"])
    result = reader.readtext(plate, detail=0)

    formatted_plate = plate_correction(result)
    print(formatted_plate)

    # Create a CSV file with image name and prediction
    with open(os.path.join(cwd, "images/data.csv"), "a") as f:
        # Write the values to the CSV file
        f.write(
            f"image_{filename}.tiff,{xmin_plate},{ymin_plate},{xmax_plate},{ymax_plate},{formatted_plate},Plate\n",
        )
        f.write(
            f"image_{filename}.tiff,{xmin_vehicle},{ymin_vehicle},{xmax_vehicle},{ymax_vehicle},{formatted_plate},Vehicle\n"
        )

    response = {
        "plate": plate_prediction.tolist(),
        "vehicle": vehicle_prediction.tolist(),
        "license_plate": formatted_plate,
    }
    # Get the users google id
    google_id = session["google_id"]
    # If formatted_plate is not "INVALID PLATE"
    if formatted_plate != "INVALID PLATE":
        p_year(formatted_plate, google_id)
        p_registration(formatted_plate, google_id)

    return jsonify(response)


@app.route("/profile", methods=["GET", "POST"])
@login_is_required
def profile():
    user = User.query.filter_by(google_id=session["google_id"]).first()
    return render_template("profile.html", user=user)


if __name__ == "__main__":
    app.run(debug=True)
