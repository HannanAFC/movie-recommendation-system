from flask import render_template, current_app
from app.email import send_email
from app.models import User


def send_password_reset_email(user: User):
    token = user.get_reset_password_token(expires_in=600)
    send_email(
        "[Movie Recommender] Reset Your Password",
        sender=current_app.config["ADMINS"][0],
        recipients=[user.email],
        text_body=render_template("email/reset-password.txt", user=user, token=token),
        html_body=render_template("email/reset-password.html", user=user, token=token)
    )