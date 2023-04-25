from datetime import datetime

from classes.User import User


def p_year(license_plate, user_id):
    # Take the first three characters of the license plate
    plate_year = int(license_plate[:2])
    plate_half = int(license_plate[2])

    # If plate half is 1, set it to 0
    if plate_half == 1:
        plate_half = 0
    elif plate_half == 2:
        plate_half = 1

    # Get the current year
    current_year = datetime.now().year
    # Get the last two digits of the current year
    current_year = int(str(current_year)[-2:])
    # Get the current half of the year
    current_half = int(datetime.now().month / 6)

    # If the plate year is equal to the current year and the plate half is equal to the current half
    if plate_year == current_year and plate_half == current_half:
        # Add 100 points to the user
        User.add_points(user_id, 100)
    # If the plate year is equal to the current year and the plate half is not equal to the current half
    elif plate_year == current_year and plate_half != current_half:
        # Add 75 points to the user
        User.add_points(user_id, 75)
    # If the plate year is 1 less than the current year and the plate half is 1
    elif plate_year == current_year - 1 and plate_half == 1:
        # Add 50 points to the user
        User.add_points(user_id, 50)
    # If the plate year is 1 less than the current year and the plate half is 0
    elif plate_year == current_year - 1 and plate_half == 0:
        # Add 25 points to the user
        User.add_points(user_id, 40)
    # If the plate year is 2 less than the current year and the plate half is 1
    elif plate_year == current_year - 2 and plate_half == 1:
        # Add 25 points to the user
        User.add_points(user_id, 25)
    # If the plate year is 2 less than the current year and the plate half is 0
    elif plate_year == current_year - 2 and plate_half == 0:
        # Add 10 points to the user
        User.add_points(user_id, 15)
    # If the plate year is less than 2 years ago
    elif plate_year < current_year - 2:
        # Add 5 points to the user
        User.add_points(user_id, 10)


def p_registration(license_plate, user_id):
    # Take everything from the 7th character to the end of the license plate
    plate_registration = int(license_plate[6:])

    # If the registration is less than 10
    if plate_registration < 10:
        # Add 1000 points to the user
        User.add_points(user_id, 1000)
    # If the registration is less than 100
    elif plate_registration < 100:
        # Add 500 points to the user
        User.add_points(user_id, 500)
    # If the registration is less than 1000
    elif plate_registration < 1000:
        # Add 250 points to the user
        User.add_points(user_id, 250)
    # If the registration is less than 10000
    elif plate_registration < 10000:
        # Add 100 points to the user
        User.add_points(user_id, 100)
    # If the registration is more than 10000
    else:
        # Add 50 points to the user
        User.add_points(user_id, 50)


def challenges():
    # Structure of the challenges
    daily = {
        "p_year": {
            "1": {
                "name": "Specific Year Challenge",
                "description": "Capturing a license plate of the specified year",
                "points": 500,
                "chance": 0.25
            },
            "2": {
                "name": "Before Specific Year Challenge",
                "description": "Capturing a license plate before the specified year",
                "points": 250,
                "chance": 0.5
            },
            "3": {
                "name": "After Specific Year Challenge",
                "description": "Capturing a license plate after the specified year",
                "points": 250,
                "chance": 0.5
            },
            "4": {
                "name": "Specific Year Range Challenge",
                "description": "Capturing a license plate of the specified year range",
                "points": 300,
                "chance": 0.5
            }
        },
        "p_registration": {
            "1": {
                "name": "Specific Registration Challenge",
                "description": "Capturing a license plate of the specified registration",
                "points": 1500,
                "chance": 0.25
            },
            "2": {
                "name": "Before Specific Registration Challenge",
                "description": "Capturing a license plate before the specified registration",
                "points": 250,
                "chance": 0.5
            },
            "3": {
                "name": "After Specific Registration Challenge",
                "description": "Capturing a license plate after the specified registration",
                "points": 250,
                "chance": 0.5
            },
            "4": {
                "name": "Specific Registration Range Challenge",
                "description": "Capturing a license plate of the specified registration range",
                "points": 500,
                "chance": 0.35
            }
        },
        "p_quantity": {
            "name": "Quantity Challenge",
            "description": "Capture a certain amount of license plates",
            "points": 250,
            "chance": 0.5
        }
    }
    weekly = {
        "p_year": {
            "1": {
                "name": "Quantity of Specific Year Challenge",
                "description": "Capturing a certain amount of license plates of the specified year",
                "points": 1000,
                "chance": 0.25
            }
        },
        "p_registration": {
            "1": {
                "name": "Quantity of Specific Registration Challenge (in range)",
                "description": "Capturing a certain amount of license plates of the specified registration between a range",
                "points": 1500,
                "chance": 0.25
            }
        },
        "p_quantity": {
            "name": "Quantity Challenge",
            "description": "Capture a certain amount of license plates",
            "points": 750,
            "chance": 0.5
        }
    }
