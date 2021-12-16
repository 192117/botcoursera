from sqlalchemy import Column, Integer, String, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


db = create_engine(
    "postgresql://bxoszuiifwaphu:e2c7dbf39cac01d59712859f169ada6ff700f78c45a5c7761fa6bedf7528352f@ec2-44-198-211-34.compute-1.amazonaws.com:5432/d2g7h99rhfeopo"
)
db.connect()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    __tableargs__ = {
        'comment': 'Пользователи.'
    }
    id = Column(Integer, nullable=False, primary_key=True, unique=True, autoincrement=True)
    uid = Column(Integer, unique=True, comment="id пользователя с телеграмма.")


class Location(Base):
    __tablename__ = 'locations'
    __tableargs__ = {
        'comment': 'Лоакции.'
    }
    id = Column(Integer, nullable=False, primary_key=True, unique=True, autoincrement=True)
    adress = Column(String(254), comment="Адрес точки.")
    location_latitude = Column(Integer, comment="Широта точки.")
    location_longitude = Column(Integer, comment="Долгота точки.")
    photo = Column(String, comment="Ссылка на фото.")
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="locations")


User.location = relationship("Location", order_by = Location.id, back_populates = "users")

Base.metadata.create_all(db)

