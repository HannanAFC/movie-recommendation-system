import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app
from app.models import User, MovieRating
from app.extensions import db, socketio

app = create_app()

# Allows you to run a python shell in the terminal (run "flask shell") and access key objects like the db, useful for testing in the shell
@app.shell_context_processor
def make_shell_context():
    return {
        "sa": sa,
        "so": so,
        "db": db,
        "User": User,
        "MovieRatings": MovieRating
    }

if __name__ == "__main__":
    socketio.run(app, debug=True, log_output=True)