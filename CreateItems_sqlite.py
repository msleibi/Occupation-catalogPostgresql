#!/usr/bin/env python


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Categories, Base, Items, User
 
engine = create_engine('postgres+psycopg2://catalog:catalog@localhost:5432/catalogapp')


# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create test user
User1 = User(name="Abigail Seligsteinstein", email="abigail_oauewyw_seligsteinstein@tfbnw.net",
             picture='')
session.add(User1)
session.commit()

#Items for Carpenter

category1 = Categories(name = "Carpentry",user_id=1)

session.add(category1)
session.commit()

item1 = Items(user_id=1, name ="Claw Hammer",description = " is a tool primarily used for driving nails into, or pulling nails from, some other object",price = "3.99",manufacture = "Microsun Innovation", category = category1)

session.add(item1)
session.commit()

category2 = Categories(user_id=1, name = "Mechanic")

session.add(category2)
session.commit()

item1 = Items(user_id=1, name ="Impact wrench",description = " An impact wrench is a socket wrench power tool designed to deliver high torque output with minimal exertion by the user, by storing energy in a rotating mass, then delivering it suddenly to the output",price = "196",manufacture = "Bosch", category = category2)

session.add(item1)
session.commit()

category3 = Categories(user_id=1, name = "Painter")

session.add(category3)
session.commit()

item1 = Items(user_id=1, name ="Brush",description = " used to apply paint or sometimes ink. A paintbrush is usually made by clamping the bristles to a handle with a ferrule",price = "8.99",manufacture = "Glart", category = category3)

session.add(item1)
session.commit()



print "added Category items!"
