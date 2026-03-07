import os
from flask import Blueprint
import click
from app import db
from app.models import User, MovieRating
from config import Config
from random import randrange

bp = Blueprint("cli", __name__, cli_group=None)


@bp.cli.group()
def seed():
    """Seed the database with fake data."""
    pass


@seed.command()
@click.argument("user_count")
def users(user_count):
    """Seed users."""
    os.system("flask db downgrade base")
    os.system("flask db upgrade")

    for i in range(int(user_count)):
        user = User(username=f"user{i}", email=f"user{i}@example.com")
        user.set_password(f"password{i}")
        db.session.add(user)

    db.session.commit()
    print("Users seeded successfully.")

@seed.command()
@click.argument("user_count")
@click.argument("ratings_per_user")
def all(user_count, ratings_per_user):
    """Seed users and movie ratings."""
    os.system("flask db downgrade base")
    os.system("flask db upgrade")

    users = []

    for i in range(int(user_count)):
        user = User(username=f"user{i}", email=f"user{i}@example.com")
        print(user)
        user.set_password(f"password{i}")
        users.append(user)
        db.session.add(user)
    
    for i in range(int(user_count)):
        for j in range(int(ratings_per_user)):
            movie_rating = MovieRating(movie_id=randrange(1, 100), rating=randrange(1, 6), rating_author=users[i])
            db.session.add(movie_rating)

    db.session.commit()
    print("Users and ratings seeded successfully.")

@seed.command()
def drop():
    """Reset the database."""
    os.system("flask db downgrade base")
    os.system("flask db upgrade")
    print("Table restored to empty.")

@bp.cli.group()
def test_email_server():
    pass

@test_email_server.command()
def start():
    """Start the testing email server"""
    os.system("aiosmtpd -n -c aiosmtpd.handlers.Debugging -l localhost:8025")