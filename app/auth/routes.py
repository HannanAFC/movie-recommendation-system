from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.auth import bp

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    else:
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
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
        return redirect(url_for("main.index"))
    return render_template("auth/register.html")

@bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    elif request.method == "POST":
        return redirect(url_for("main.index"))
    return render_template("auth/reset-password.html")

@bp.route("/reset-password<token>", methods=["GET", "POST"])
def handle_reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    elif request.method == "POST":
        return redirect(url_for("main.index"))
    return render_template("auth/reset-password.html")