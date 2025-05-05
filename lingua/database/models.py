# models.py
import uuid
from sqlalchemy import (
    create_engine, Column, String, Text, Boolean, ForeignKey, ARRAY
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

    words = relationship("WordDefinition", back_populates="alphabet_rel")

class WordDefinition(Base):
    __tablename__ = 'word_definition'

    word_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alphabet = Column(String(5), ForeignKey("alphabet_url.alphabet"))
    word = Column(Text, nullable=False)
    word_url = Column(Text)
    definitions = Column(ARRAY(Text))
    needs_review = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    alphabet_rel = relationship("AlphabetURL", back_populates="words")
