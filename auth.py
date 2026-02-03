from sqlalchemy import text
from werkzeug.security import check_password_hash
from db import engine

def authenticate(username, password):
    query = """
    SELECT user_id, username, password, role
    FROM users
    WHERE username = :username AND is_active = TRUE
    """

    with engine.begin() as conn:
        user = conn.execute(
            text(query),
            {"username": username}
        ).fetchone()

    if not user:
        return None

    if check_password_hash(user.password_hash, password):
        return {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role
        }

    return None

