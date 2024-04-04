import random
import secrets
import string


def generate_random_token(length):
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


def generate_two_fa_code(length):
    return "".join(str(random.randint(0, 9)) for _ in range(length))
