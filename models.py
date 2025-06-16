from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Boolean


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# CONFIGURE TABLE
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(1000))
    phone: Mapped[str] = mapped_column(String())
    agent: Mapped[bool] = mapped_column(Boolean())
    admin: Mapped[bool] = mapped_column(Boolean())
    # reset_token: Mapped[str] = mapped_column(String(200), nullable=True)
    # reset_token_expiration: Mapped[db.DateTime] = mapped_column(db.DateTime, nullable=True)