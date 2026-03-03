import unittest
from app import create_app, db
from app.models import User, MovieRating
from config import Config
from sqlalchemy.exc import IntegrityError

class TestConfig(Config):
    Testing = True
    # Redirect SQLAlchemy to special in-memory database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite://"

class TestUserModel(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self):
        user = User(username="testuser", email="testuser@example.com")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "testuser@example.com")

    def test_password_hashing(self):
        user = User(username="testuser", email="testuser@example.com")
        user.set_password("password")
        self.assertFalse(user.password_hash is None)
        self.assertTrue(user.check_password("password"))
        self.assertFalse(user.check_password("wrongpassword"))

    def test_reset_password_token(self):
        user = User(username="testuser", email="testuser@example.com")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        token = user.get_password_reset_token()
        self.assertIsNotNone(token)

        user.verify_reset_password_token(token)
        self.assertEqual(user.id, 1)
    
    def test_no_passord(self):
        user = User(username="testuser", email="testuser@example.com")
        db.session.add(user)
        self.assertRaises(IntegrityError, db.session.commit)

    def test_no_username(self):
        user = User(email="testuser@example.com")
        user.set_password("password")
        db.session.add(user)
        self.assertRaises(IntegrityError, db.session.commit)

    def test_no_email(self):
        user = User(username="testuser")
        user.set_password("password")
        db.session.add(user)
        self.assertRaises(IntegrityError, db.session.commit)

class TestMovieRatingModel(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_movie_rating_creation(self):
        user = User(username="testuser", email="test@example.com")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        movie_rating = MovieRating(user_id=user.id, movie_id=1, rating=5)
        db.session.add(movie_rating)
        db.session.commit()
        self.assertEqual(movie_rating.rating_author, user)

if __name__ == "__main__":
    unittest.main()