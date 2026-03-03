from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.main import bp

@bp.route("/")
@bp.route("/index")
def index():
    if current_user.is_authenticated:
        redirect(url_for("main.dashboard"))
    return render_template("index.html")

@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("views/dashboard.html")