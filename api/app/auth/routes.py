from flask import request, session, jsonify
from flask_jwt_extended import JWTManager, create_access_token
from app.auth import bp
from app.utils import sanitise_form_inputs
from email.utils import parseaddr
from app import db, current_app
from app.models import User
import sqlalchemy as sa
from app.auth.password_reset import send_password_reset_email

@bp.route("/@me", methods=["GET"])
def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "error": "Unauthorised."
        })
    
    user = User.query.filter_by(id=user_id).first()
    access_token = create_access_token(identity=user.username)
    return jsonify(access_token=access_token), 200
    

@bp.route("/login", methods=["POST"])
def login():
    values = sanitise_form_inputs(request=request, fields=["username", "password", "remember_me"])
    username = values["username"]
    password = values["password"]

    if not all([username, password]):
        return jsonify({
            "error": "Invalid details."
        }), 422

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({
            "error": "Unauthorised."
        }), 401
    
    session["user_id"] = user.id
    session["dek"] = user.unlock_dek(password=password)

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200

@bp.route("/logout")
def logout():
    if session.get("user_id"):
        session.pop("user_id")
    if session.get("dek"):
        session.pop("dek")
    return "200"

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
        
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200

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
                "message": "Password reset successful. You can now log in with your new password."
            })
        
        else:
            return jsonify({
                "message": "Passwords do not match."
            }), 422
        
    else:
        return jsonify({
            "message": "Invalid password reset token."
        }), 401