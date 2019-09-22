import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
 
class Categories(Base):
    __tablename__ = 'categories'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    items = relationship("Items")
    
    
#We added this serialize function to be able to send JSON objects in a serializable format

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'items': [item.serialize for item in self.items]
        }
    


 
class Items(Base):
    __tablename__ = 'items'
    

    id = Column(Integer, primary_key = True)
    name =Column(String(80), nullable = False)
    description = Column(String(250), nullable = False)
    price = Column(String(50),nullable = False)
    manufacture = Column(String(50),nullable = False)
    createdate = Column(DateTime, default=datetime.datetime.utcnow)
    categories_id = Column(Integer,ForeignKey('categories.id'))
    category = relationship(Categories, back_populates='items')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       #Returns object data in easily serializeable format
       return {
           'id'           : self.id,
           'name'         : self.name,
           'description'  : self.description,
           'price'        : self.price,
           'manufacture'  : self.manufacture,
           'category_id' : self.categories_id,
           
           }


engine = create_engine('postgres+psycopg2://catalog:catalog@localhost:5432/catalogapp')
 

Base.metadata.create_all(engine)

print "Table had created!!"
