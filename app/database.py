from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    salt = Column(LargeBinary, nullable=False)
    ratings = relationship("MovieRating", back_populates="user")

class MovieRating(Base):
    __tablename__ = 'ratings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    movie_id = Column(Integer, nullable=False)
    encrypted_rating = Column(String, nullable=False)
    user = relationship("User", back_populates="ratings")

engine = create_engine('sqlite:///movie_recs.db')
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print("✅ Database 'movie_recs.db' initialized.")