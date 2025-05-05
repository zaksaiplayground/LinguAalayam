from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from lingua.database.models import AlphabetURL, WordDefinition, Base
from dotenv import load_dotenv
import os
import uuid
import json

load_dotenv()

_USER = os.getenv("user")
_PWD = os.getenv("password")
_HOST = os.getenv("host")
_PORT = os.getenv("port")
_DBNAME = os.getenv("dbname")

DATABASE_URL = f"postgresql+psycopg2://{_USER}:{_PWD}@{_HOST}:{_PORT}/{_DBNAME}?sslmode=require"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Tables created!")


# ---------- ALPHABET CRUD ----------

def upsert_alphabet(alphabet: str, url: str):
    session = Session()
    try:
        obj = session.get(AlphabetURL, alphabet)
        if obj:
            obj.url = url
        else:
            obj = AlphabetURL(alphabet=alphabet, url=url)
            session.add(obj)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_all_alphabets():
    session = Session()
    try:
        return session.query(AlphabetURL).all()
    finally:
        session.close()

def soft_delete_alphabets():
    """
    Soft deletes alphabets (sets is_deleted to True) in AlphabetURL and WordDefinition if their count is less than 50.
    """
    session = Session()
    existing_alphabets = session.query(AlphabetURL).filter(AlphabetURL.is_deleted == False).all()

    if len(existing_alphabets) < 50:
        print("⚠️ Less than 50 records, performing soft delete.")
        
        # Soft delete AlphabetURL records
        for alphabet in existing_alphabets:
            alphabet.is_deleted = True
        
        # Soft delete related WordDefinition records
        for alphabet in existing_alphabets:
            for word in alphabet.words:
                word.is_deleted = True
        
        session.commit()  # Save changes
        print(f"✅ Soft deleted {len(existing_alphabets)} alphabets and related words.")
    else:
        print("✅ There are enough existing records, no need to delete.")

# ---------- WORD CRUD ----------

def add_word(alphabet, word_url, word_text=None, definitions=None, needs_review=False):
    session = Session()
    try:
        word = WordDefinition(
            word_uuid=uuid.uuid4(),
            alphabet=alphabet,
            word=word_text,
            word_url=word_url,
            definitions=json.dumps(definitions) if isinstance(definitions, list) else definitions,
            needs_review=needs_review
        )
        session.add(word)
        session.commit()
        return word.word_uuid
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_words_by_alphabet(alphabet):
    session = Session()
    try:
        return session.query(WordDefinition).filter_by(alphabet=alphabet).all()
    finally:
        session.close()

def get_words_without_definitions(limit=100):
    session = Session()
    try:
        return session.query(WordDefinition).filter((WordDefinition.definitions == None) | (WordDefinition.definitions == [])).limit(limit).all()
    finally:
        session.close()

def update_word_definitions(word_uuid, definitions):
    session = Session()
    try:
        word = session.query(WordDefinition).filter_by(word_uuid=word_uuid).first()
        if word:
            word.definitions = definitions
            word.needs_review = False  # optionally set this
            session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()