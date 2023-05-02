import re


def plate_correction(plate):
    most_rep = ''

    # If there is more than one plate
    if len(plate) > 0:
        for res in plate:
            # Count the total number of digits in the plate
            digit_count = sum(c.isdigit() for c in res)
            if digit_count > sum(c.isdigit() for c in most_rep):
                # If the current plate has more digits than the previous one
                most_rep = res

    result = most_rep
    result = result.replace("-", " ")

    # Store all characters to the first space
    year = result[:result.find(" ")]
    # Store all characters from the first space to the second space
    county = result[result.find(" ") + 1:result.rfind(" ")]
    # Store all characters from the second space to the end
    registration = result[result.rfind(" ") + 1:]

    # If the year is a digit
    if year.isdigit():
        pass
    else:
        # Find which character is not a digit
        for i, char in enumerate(year):
            if not char.isdigit():
                # If the character is a 'i' or 'I' replace it with a '1'
                if char == "i" or char == "I":
                    year = year[:i] + "1" + year[i + 1:]
                # If the character is a 'o' or 'O' replace it with a '0'
                elif char == "o" or char == "O":
                    year = year[:i] + "0" + year[i + 1:]
                # If the character is a 's' or 'S' replace it with a '5'
                elif char == "s" or char == "S":
                    year = year[:i] + "5" + year[i + 1:]
                # If the character is a 'z' or 'Z' replace it with a '7'
                elif char == "z" or char == "Z":
                    year = year[:i] + "7" + year[i + 1:]
                # If the character is a 'q' or 'Q' replace it with a '9'
                elif char == "q" or char == "Q":
                    year = year[:i] + "9" + year[i + 1:]
                # If the character is a 'b' or 'B' replace it with a '8'
                elif char == "b" or char == "B":
                    year = year[:i] + "8" + year[i + 1:]
                # If the character is a 'g' or 'G' replace it with a '6'
                elif char == "g" or char == "G":
                    year = year[:i] + "6" + year[i + 1:]
                # If the character is a 't' or 'T' replace it with a '7'
                elif char == "t" or char == "T":
                    year = year[:i] + "7" + year[i + 1:]
                # If the character is a 'l' or 'L' replace it with a '1'
                elif char == "l" or char == "L":
                    year = year[:i] + "1" + year[i + 1:]
                # If the character is a 'e' or 'E' replace it with a '3'
                elif char == "e" or char == "E":
                    year = year[:i] + "3" + year[i + 1:]
                # If the character is a 'j' or 'J' replace it with a '1'
                elif char == "j" or char == "J":
                    year = year[:i] + "1" + year[i + 1:]
                # If the character is a 'p' or 'P' replace it with a '9'
                elif char == "p" or char == "P":
                    year = year[:i] + "9" + year[i + 1:]
    # If the county is a letter
    if county.isalpha():
        pass
    else:
        # Find which character is not a character
        for i, char in enumerate(county):
            # If the digit is a '0' replace it with a 'D'
            if char == "0":
                county = county[:i] + "D" + county[i + 1:]
            # If the digit is a '1' replace it with a 'I'
            elif char == "1":
                county = county[:i] + "I" + county[i + 1:]
            # If the digit is a '2' replace it with a 'Z'
            elif char == "2":
                county = county[:i] + "Z" + county[i + 1:]
            # If the digit is a '3' replace it with a 'E'
            elif char == "3":
                county = county[:i] + "E" + county[i + 1:]
            # If the digit is a '4' replace it with a 'A'
            elif char == "4":
                county = county[:i] + "A" + county[i + 1:]
            # If the digit is a '5' replace it with a 'S'
            elif char == "5":
                county = county[:i] + "S" + county[i + 1:]
            # If the digit is a '6' replace it with a 'G'
            elif char == "6":
                county = county[:i] + "G" + county[i + 1:]
            # If the digit is a '7' replace it with a 'T'
            elif char == "7":
                county = county[:i] + "T" + county[i + 1:]
            # If the digit is a '8' replace it with a 'B'
            elif char == "8":
                county = county[:i] + "B" + county[i + 1:]
            # If the digit is a '9' replace it with a 'P'
            elif char == "9":
                county = county[:i] + "P" + county[i + 1:]
    # If the registration is a digit
    if registration.isdigit():
        pass
    else:
        # Find which character is not a digit
        for i, char in enumerate(registration):
            if not char.isdigit():
                # If the character is a 'i' or 'I' replace it with a '1'
                if char == "i" or char == "I":
                    registration = registration[:i] + "1" + registration[i + 1:]
                # If the character is a 'o' or 'O' replace it with a '0'
                elif char == "o" or char == "O":
                    registration = registration[:i] + "0" + registration[i + 1:]
                # If the character is a 's' or 'S' replace it with a '5'
                elif char == "s" or char == "S":
                    registration = registration[:i] + "5" + registration[i + 1:]
                # If the character is a 'z' or 'Z' replace it with a '2'
                elif char == "z" or char == "Z":
                    registration = registration[:i] + "2" + registration[i + 1:]
                # If the character is a 'q' or 'Q' replace it with a '9'
                elif char == "q" or char == "Q":
                    registration = registration[:i] + "9" + registration[i + 1:]
                # If the character is a 'b' or 'B' replace it with a '8'
                elif char == "b" or char == "B":
                    registration = registration[:i] + "8" + registration[i + 1:]
                # If the character is a 'g' or 'G' replace it with a '6'
                elif char == "g" or char == "G":
                    registration = registration[:i] + "6" + registration[i + 1:]
                # If the character is a 't' or 'T' replace it with a '7'
                elif char == "t" or char == "T":
                    registration = registration[:i] + "7" + registration[i + 1:]
                # If the character is a 'l' or 'L' replace it with a '1'
                elif char == "l" or char == "L":
                    registration = registration[:i] + "1" + registration[i + 1:]
                # If the character is a 'e' or 'E' replace it with a '3'
                elif char == "e" or char == "E":
                    registration = registration[:i] + "3" + registration[i + 1:]
                # If the character is a 'j' or 'J' replace it with a '1'
                elif char == "j" or char == "J":
                    registration = registration[:i] + "1" + registration[i + 1:]
                # If the character is a 'p' or 'P' replace it with a '9'
                elif char == "p" or char == "P":
                    registration = registration[:i] + "9" + registration[i + 1:]

    # Format the plate
    formatted_plate = "{}-{}-{}".format(year, county, registration)
    formatted_plate = formatted_plate.replace(" ", "")

    # Pattern format
    pattern = r'^\d{1,2}[1-2]?\-[A-Z]{1,2}\-\d+$'
    # Verify if the plate is valid
    if not re.match(pattern, formatted_plate):
        return "INVALID PLATE"
    else:
        return formatted_plate.upper()
