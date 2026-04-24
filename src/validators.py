import re


def is_email(value):
    if not isinstance(value, str):
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, value))


def is_strong_password(password):
    if not isinstance(password, str):
        return False
    if len(password) < 8:
        return False
    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))
    return has_upper and has_lower and has_digit and has_special


def clamp(value, min_val, max_val):
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value


def normalize_email(email):
    if not isinstance(email, str):
        return None
    return email.lower()


def is_valid_username(username):
    if not isinstance(username, str):
        return False
    if len(username) < 3 or len(username) > 20:
        return False
    pattern = r"^[a-zA-Z0-9_]+$"
    return bool(re.match(pattern, username))
