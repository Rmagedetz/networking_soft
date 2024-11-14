from sqlalchemy import Column, Integer, String, Date, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager
import pandas as pd
from connections import sql_connection_string

# Создаем подключение к базе данных
engine = create_engine(sql_connection_string)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)


def get_user_list():
    with session_scope() as session:
        users = session.query(User.user_name).all()
        user_list = [user.user_name for user in users]
    return user_list


def check_user_password(username):
    with session_scope() as session:
        result = session.query(User.password).filter(User.user_name == username).first()
        return result[0] if result else None


Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    finally:
        db.close()
