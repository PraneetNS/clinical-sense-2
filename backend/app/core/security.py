# Custom JWT and Password Auth removed in favor of Firebase Authentication
# This file is kept as a placeholder to avoid breaking imports, but logic is deprecated.

def verify_password(plain_password: str, hashed_password: str) -> bool:
    raise NotImplementedError("Use Firebase Auth on the frontend")

def get_password_hash(password: str) -> str:
    raise NotImplementedError("Use Firebase Auth on the frontend")
