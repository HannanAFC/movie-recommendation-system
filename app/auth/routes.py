from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app.utils import sanitise_form_inputs
from email.utils import parseaddr
from app import db, current_app
from app.models import User
import sqlalchemy as sa
from urllib.parse import urlsplit
from app.auth.password_reset import send_password_reset_email

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        values = sanitise_form_inputs(request=request, fields=["username", "password", "remember_me"])
        username = values["username"]
        password = values["password"]
        remember_me = values["remember_me"]

        if not all([username, password, remember_me]):
            return redirect(url_for("auth.register"), code=400)

        user = db.session.scalar(
            sa.select(User).where(User.username == username)
        )

        if not user or not user.check_password(password=password):
            return redirect(url_for("auth.login"))
        
        dek = user.unlock_dek(password)
        login_user(user, remember=bool(remember_me))
        session["dek"] = dek
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("main.dashboard")
        return redirect(next_page)

    return render_template("auth/login.html")

@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))

@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    elif request.method == "POST":
        values = sanitise_form_inputs(request=request, fields=["email", "username", "password", "repeat_password"])
        email           = values["email"]
        username        = values["username"]
        password        = values["password"]
        repeat_password = values["repeat_password"]
        if email == None or username == None or password == None or repeat_password == None or password != repeat_password or not "@" in parseaddr(email)[1]:
            return redirect(url_for("auth.register"), code=400)
        else:
            user = User(username=username, email=email)
            user.set_password(password=password)
            db.session.add(user)
            db.session.commit()
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", title="Register")

@bp.route("/reset-password-request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    elif request.method == "POST":
        values = sanitise_form_inputs(request=request, fields=["email"])
        email  = values["email"]
        if email == None:
            return redirect(url_for("auth.reset-password"), code=400)
        else:
            user = db.session.scalar(
                sa.select(User).where(User.email == email)
            )
            if user:
                send_password_reset_email(user)
        return redirect(url_for("auth.login"))
    return render_template("auth/reset-password-request.html", title="Reset Password")

@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    user = User.verify_reset_password_token(token)
    if user and request.method == "POST":
        values = sanitise_form_inputs(request=request, fields=["password", "repeat_password"])
        password        = values["password"]
        repeat_password = values["repeat_password"]
        print(password, repeat_password)
        if password == repeat_password:
            user.set_password(password=password)
            db.session.commit()
            return redirect(url_for("auth.login"))
        else:
            return redirect(url_for("auth.reset-password", token=token))      
    return render_template("auth/reset-password.html", title="Reset Password")