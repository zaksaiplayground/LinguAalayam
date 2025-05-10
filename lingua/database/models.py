import uuid
from sqlalchemy import (
    create_engine, Column, String, Text, Boolean, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class AlphabetURL(Base):
    __tablename__ = 'alphabet_url'

    alphabet = Column(String(5), primary_key=True)
    url = Column(Text)
    is_deleted = Column(Boolean, default=False)

    words = relationship("WordUrl", back_populates="alphabet_rel")


class WordUrl(Base):
    __tablename__ = 'word_url'

    word_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alphabet = Column(String(5), ForeignKey("alphabet_url.alphabet"))
    word_url = Column(Text, nullable=False)
    needs_review = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    alphabet_rel = relationship("AlphabetURL", back_populates="words")
    definitions = relationship("WordDefinition", back_populates="word_rel", cascade="all, delete-orphan")


class WordDefinition(Base):
    __tablename__ = 'word_definition'

    definition_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word_uuid = Column(UUID(as_uuid=True), ForeignKey("word_url.word_uuid"), nullable=False)
    definition = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False)
    word = Column(Text, nullable=True)

    word_rel = relationship("WordUrl", back_populates="definitions")

