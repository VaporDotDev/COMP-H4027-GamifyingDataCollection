import hashlib
import os

import cv2
import numpy as np

from classes.Image import Image

cwd = os.path.dirname(os.path.abspath(__file__))


def preprocess_image(image, filename, google_id):
    # Convert the image to a numpy array
    image = np.frombuffer(image, np.uint8)

    # Create a copy of the image
    image_copy = image.copy()

    # Decode the image using the TIFF flag
    image = cv2.imdecode(
        image, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH
    )

    image_copy = cv2.imdecode(
        image_copy, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH
    )

    image_copy = cv2.cvtColor(image_copy, cv2.COLOR_BGR2GRAY)

    # Save the image to disk if unique
    if is_image_unique(image_copy, filename, google_id):
        cv2.imwrite(os.path.join(cwd, "images", filename), image)

    # Resize the image to (224, 224)
    image = cv2.resize(image, (224, 224))

    # Normalize the image
    image = image / 255.0

    # Remove the alpha channel if the image has it
    if image.shape[-1] == 4:
        image = image[..., :3]

    return image, image_copy


def save_to_csv(filename, xmin, ymin, xmax, ymax, formatted_plate, object_type):
    with open(os.path.join(cwd, "../images/data.csv"), "a") as f:
        # Write the values to the CSV file
        f.write(
            f"{filename},{xmin},{ymin},{xmax},{ymax},{formatted_plate},{object_type}\n",
        )


def is_image_unique(image, filename, google_id):
    # Calculate the hash of the image
    image_hash = hashlib.md5(image).hexdigest()

    # Check if the image hash is unique in the database
    if Image.query.filter_by(hash_string=image_hash).first() is not None:
        return False
    else:
        # Create an entry in the database for the image
        Image.create_image(filename=filename, hash_string=image_hash, captured_by=google_id)
        return True
