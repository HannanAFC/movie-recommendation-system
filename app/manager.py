import os
from database import Session, User, MovieRating
from security import hash_password, verify_password, derive_key, encrypt_rating

def register_user(username, password):
    session = Session()
    salt = os.urandom(16)
    new_user = User(username=username, password_hash=hash_password(password), salt=salt)
    try:
        session.add(new_user)
        session.commit()
        print(f"👤 User '{username}' registered.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

def login_user(username, password):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    if user and verify_password(password, user.password_hash):
        key = derive_key(password, user.salt)
        return user, key
    return None, None

def remove_user(User):
    session = Session()
    user_db_session = session.object_session(User)
    if user_db_session != None:
        user_db_session.delete(User)
        user_db_session.commit()
        user_db_session.close()
    else:
        print("Can't find user session.")

def add_movie_rating(user, key, movie_id, rating_value):
    session = Session()
    user_db_session = session.object_session(User)
    if user_db_session != None:
        encrypted_val = encrypt_rating(str(rating_value), key)
        new_rating = MovieRating(user_id=user.id, movie_id=movie_id, encrypted_rating=encrypted_val)
        user_db_session.add(new_rating)
        user_db_session.commit()
        user_db_session.close()
        print(f"🔐 Rating for movie {movie_id} saved (Encrypted).")
    else:
        print("Can't find user session.")