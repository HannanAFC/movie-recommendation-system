from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app.utils import sanitise_form_inputs
from email.utils import parseaddr
from app import db, current_app
from app.models import User
import sqlalchemy as sa
from urllib.parse import urlsplit

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

        login_user(user, remember=bool(remember_me))
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
            print(f"{email} {username} {password} {repeat_password}")
            return redirect(url_for("auth.register"), code=400)
        else:
            user = User(username=username, email=email)
            user.set_password(password=password)
            db.session.add(user)
            db.session.commit()
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", title="Register")

@bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    elif request.method == "POST":
        return redirect(url_for("main.index"))
    return render_template("auth/reset-password.html", title="Reset Password")

@bp.route("/reset-password<token>", methods=["GET", "POST"])
def handle_reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    elif request.method == "POST":
        return redirect(url_for("main.index"))
    return render_template("auth/reset-password.html", title="Reset Password")