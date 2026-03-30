from flask import request, session, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, current_user, get_jwt, set_access_cookies, unset_jwt_cookies
from app.auth import bp
from app.utils import sanitise_form_inputs
from email.utils import parseaddr
from app import db, dataset_manager
from app.models import User
import sqlalchemy as sa
from app.auth.password_reset import send_password_reset_email
import datetime
from datetime import datetime, timedelta

@bp.after_request
def refresh_expiring_jwts(response):
    print("Test")
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now()
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=current_user, expires_delta=timedelta(minutes=60))
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # No valid JWT
        return response


@bp.route("/@me", methods=["GET"])
@jwt_required()
def get_current_user():
    dataset_selected = dataset_manager.dataset_exists()
    needs_to_select_movies = len(current_user.get_user_ratings()) == 0 and len(current_user.get_liked_movies()) < 5

    recommender_status = current_app.extensions.get("recommender_status", {
        "is_ready": False,
        "needs_manual_initialisation": False,
        "status_message": "Recommender status is unavailable."
    })

    movie_search_status = current_app.extensions.get("movie_search_status", {
        "is_ready": False,
        "status_message": "Movie search status is unavailable."
    })

    tmdb_status = {
        "api_key_set": current_user.tmdb_api_key is not None,
        "api_key_valid": current_user.tmdb_api_key_valid,
        "api_key_last_validated_at": (
            current_user.tmdb_api_key_last_validated_at.isoformat()
            if current_user.tmdb_api_key_last_validated_at is not None
            else None
        )
    }

    return jsonify({
        "user": {
            "username": current_user.username,
            "email": current_user.email,
            "dataset_selected": dataset_selected,
            "needs_to_select_movies": needs_to_select_movies,
            "recommender": recommender_status,
            "movie_search": movie_search_status,
            "tmdb": tmdb_status
        }
    }), 200

@bp.route("/login", methods=["POST"])
def login():
    values = sanitise_form_inputs(request=request, fields=["username", "password"])
    username = values["username"]
    password = values["password"]

    if not all([username, password]):
        return jsonify({
            "error": f"Please enter a { "username" if not username else "password" }."
        }), 422

    user = User.query.filter_by(username=username).first()
    if not user or type(user) != User or not user.check_password(password):
        return jsonify({
            "error": "Invalid username or password."
        }), 401
    
    session["dek"] = user.unlock_dek(password=password)

    access_token = create_access_token(identity=user, expires_delta=timedelta(minutes=60))
    response = jsonify({"message": "Login successful."})
    set_access_cookies(response, access_token)  # Ensure cookies are set with httponly=True (default)
    return response, 200

@bp.route("/logout", methods=["GET"])
@jwt_required()
def logout():
    response = jsonify({"message": "Logout successful."})
    unset_jwt_cookies(response)  # Ensure cookies are unset properly
    if session.get("dek"):
        session.pop("dek")
    return response, 200

@bp.route("/register", methods=["POST"])
def register():
    values = sanitise_form_inputs(request=request, fields=["email", "username", "password", "repeat_password"])
    email           = values["email"]
    username        = values["username"]
    password        = values["password"]
    repeat_password = values["repeat_password"]
    if not all([username, password, repeat_password, email]) or password != repeat_password or not "@" in parseaddr(email)[1]:
        return jsonify({
            "error": "Invalid details."
        }), 422
    
    elif User.query.filter_by(email=email).first() is not None:
        return jsonify({
            "error": "Email already in use."
        }), 409
    
    elif User.query.filter_by(username=username).first() is not None:
        return jsonify({
            "error": "Username already in use."
        }), 409
    
    else:
        user = User(username=username, email=email)
        user.set_password(password=password)
        db.session.add(user)
        db.session.commit()
        
        access_token = create_access_token(identity=user, expires_delta=timedelta(minutes=60))
        response = jsonify({"message": "Registration successful."})
        set_access_cookies(response, access_token)
        return response, 200

@bp.route("/reset-password-request", methods=["POST"])
def reset_password_request():
    values = sanitise_form_inputs(request=request, fields=["email"])
    email  = values["email"]
    if email != None:
        user = db.session.scalar(
            sa.select(User).where(User.email == email)
        )
        if user:
            send_password_reset_email(user)
        return jsonify({
            "message": "If an account exists with that email address, we have sent an email with instructions to reset your password."
        })
    else:
        return jsonify({"message": "Please enter an email address."})

@bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    user               = User.verify_reset_password_token(token)

    if user:
        values          = sanitise_form_inputs(request=request, fields=["password", "repeat_password"])
        password        = values["password"]
        repeat_password = values["repeat_password"]

        if password == repeat_password:
            user.set_password(password=password)
            db.session.commit()
            return jsonify({
                "message": "Password reset successful. You can now login with your new password."
            })
        
        else:
            return jsonify({
                "message": "Passwords do not match."
            }), 422
        
    else:
        return jsonify({
            "message": "Invalid password reset token."
        }), 401