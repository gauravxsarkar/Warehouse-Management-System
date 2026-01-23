from sqlalchemy import text
from werkzeug.security import check_password_hash
from db import engine

def authenticate(username, password):
    query = """
    SELECT user_id, username, password, role
    FROM users
    WHERE username = :username
    """

    with engine.begin() as conn:
        user = conn.execute(
            text(query),
            {"username": username}
        ).fetchone()

    if user is None:
        return None

    if not check_password_hash(user.password, password):
        return None

    return {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role
    }
