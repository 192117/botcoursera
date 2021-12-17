from sqlalchemy import Column, Integer, String, create_engine, Float
from sqlalchemy.ext.declarative import declarative_base
import os


db = create_engine(os.environ["URI_DB"])
db.connect()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    __tableargs__ = {
        'comment': 'Пользователи.'
    }
    id = Column(Integer, nullable=False, primary_key=True, unique=True, autoincrement=True)
    uid = Column(Integer, comment="id пользователя с телеграмма.")
    adress = Column(String(254), comment="Адрес точки.")
    location_latitude = Column(Float, comment="Широта точки.")
    location_longitude = Column(Float, comment="Долгота точки.")
    photo = Column(String, comment="Ссылка на фото.")


Base.metadata.create_all(db)
# Base.metadata.drop_all(db) # Удалить таблицы в БД.

