# This test class validates PUBLIC KEYs with JWT Tokens

import jwt

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
[INSERT HERE]
-----END PUBLIC KEY-----"""

token = "[INSERT HERE]"

try:
    decoded_token = jwt.decode(token, PUBLIC_KEY, algorithms=["ES256"])
    print("Decoded token:", decoded_token)
except jwt.ExpiredSignatureError:
    print("The token has expired.")
except jwt.InvalidSignatureError:
    print("Invalid token signature.")
except jwt.DecodeError:
    print("Failed to decode the token. Possible formatting issue.")
except Exception as e:
    print(f"Unexpected error: {e}")
