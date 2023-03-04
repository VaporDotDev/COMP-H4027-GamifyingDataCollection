import json
import os
import pathlib
import zipfile
from functools import wraps

import cachecontrol as cachecontrol
import cv2
import google
import numpy as np
import requests
import tensorflow as tf
from flask import Flask, render_template, session, abort, redirect, request, jsonify, send_file
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

app = Flask(__name__)
app.secret_key = json.load(open(client_secrets_file, "r"))["web"]["client_secret"]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = json.load(open(client_secrets_file, "r"))["web"]["client_id"]
flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file,
                                     scopes=["https://www.googleapis.com/auth/userinfo.email",
                                             "openid",
                                             "https://www.googleapis.com/auth/userinfo.profile"],
                                     redirect_uri="http://127.0.0.1:5000/callback")

model = tf.keras.models.load_model('models/vehicle_classification_2022-12-24_14-34-13.h5')


def login_is_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)
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
    return "Logout Page"


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
    prediction = model.predict(image[np.newaxis, ...])

    # Create a CSV file with image name and prediction
    with open('images/data.csv', 'a') as f:
        # Get the prediction values
        xmin, xmax, ymin, ymax = prediction[0]
        # Multiply the values by the image width and height
        xmin, xmax, ymin, ymax = xmin * image.shape[1], xmax * image.shape[1], ymin * image.shape[0], ymax * \
                                 image.shape[0]
        # Convert the values to integers
        xmin, xmax, ymin, ymax = int(xmin), int(xmax), int(ymin), int(ymax)
        # Write the values to the CSV file
        f.write(f"image_{num_files + 1}.tiff,{xmin},{xmax},{ymin},{ymax}\n")

    print(prediction)
    response = {"prediction": prediction.tolist()}
    return jsonify(response)


if __name__ == '__main__':
    app.run(host="192.168.0.94", debug=True)
