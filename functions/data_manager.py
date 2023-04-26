import os

import cv2
import numpy as np

cwd = os.getcwd()


def preprocess_image(image, filename):
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

    # Save the image to disk
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
    with open(os.path.join(cwd, "images/data.csv"), "a") as f:
        # Write the values to the CSV file
        f.write(
            f"{filename},{xmin},{ymin},{xmax},{ymax},{formatted_plate},{object_type}\n",
        )
