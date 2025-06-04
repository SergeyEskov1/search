from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    email = Column(String(255))

    games = relationship("Game", back_populates="provider")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    price = Column(Numeric(10, 2))
    is_published = Column(Boolean, default=True)
    provider_id = Column(Integer, ForeignKey("providers.id"))

    provider = relationship("Provider", back_populates="games")
