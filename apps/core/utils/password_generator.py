import string
import random


def generate_password(length=8):
    """
    Generate a secure random password
    """
    characters = string.ascii_letters + string.digits + "@#$%&*"

    password = ''.join(random.choice(characters) for _ in range(length))

    return password
    