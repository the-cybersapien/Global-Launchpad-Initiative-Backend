from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# User Entity and it's Attributes
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(75), nullable=False, unique=True)
    photo = Column(String(500), nullable=True)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'email': self.email,
            'photo': self.photo
        }


# Category Entity
class Category(Base):
    """
    The reason to have this in a separate table is to introduce a little
    normalization in the database. The Content table will only thereafter
    store the id of the Category, and adding/removing categories will be much easier
    """
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Content(Base):
    __tablename__ = 'content'

    id = Column(Integer, primary_key=True)
    title = Column(String(75), nullable=False)
    description = Column(String(500), nullable=True)
    timeAdded = Column(Integer, nullable=False)
    date = Column(String(50), nullable=False)
    url = Column(String(250), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship(User, cascade='delete')
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category, cascade='delete')

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category.name,
            'description': self.description,
            'timeAdded': self.timeAdded,
            'date': self.date,
            'url': self.url,
            'author': self.author.name,
            'authorPhoto': self.author.photo,
            'author_email': self.author.email
        }
