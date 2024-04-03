import random
import secrets
import string

RANDOM_TOKEN = lambda length: "".join(
    secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
)

TWO_FA_CODE = lambda length: "".join(str(random.randint(0, 9)) for i in range(length))
