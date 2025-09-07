import os

file_path = r"C:\Users\Admin\Documents\BookStore-backend\backend\requests_app\models.py"

with open(file_path, "rb") as f:
    content = f.read()

content = content.replace(b"\x00", b"")

with open(file_path, "wb") as f:
    f.write(content)

print("Null bytes removed from models.py")
