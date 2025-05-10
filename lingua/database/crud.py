from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from lingua.database.models import AlphabetURL, WordUrl, WordDefinition, Base
from dotenv import load_dotenv
import os
import uuid

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
    Soft deletes alphabets (sets is_deleted to True) in AlphabetURL and WordUrl if their count is less than 50.
    """
    session = Session()
    existing_alphabets = session.query(AlphabetURL).filter(AlphabetURL.is_deleted == False).all()

    if len(existing_alphabets) < 50:
        print("⚠️ Less than 50 records, performing soft delete.")
        
        # Soft delete AlphabetURL records
        for alphabet in existing_alphabets:
            alphabet.is_deleted = True
        
        # Soft delete related WordUrl records
        for alphabet in existing_alphabets:
            for word in alphabet.words:
                word.is_deleted = True
        
        session.commit()  # Save changes
        print(f"✅ Soft deleted {len(existing_alphabets)} alphabets and related words.")
    else:
        print("✅ There are enough existing records, no need to delete.")

# ---------- WORD URL CRUD ----------

def add_word(alphabet, word_url, needs_review=True):
    session = Session()
    try:
        word = WordUrl(
            word_uuid=uuid.uuid4(),
            alphabet=alphabet,
            word_url=word_url,
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
        return session.query(WordUrl).filter_by(alphabet=alphabet).all()
    finally:
        session.close()

def get_words_without_definitions(limit=100):
    session = Session()
    try:
        return session.query(WordUrl).filter((WordUrl.definitions == None) | (WordUrl.definitions == [])).limit(limit).all()
    finally:
        session.close()

def update_word_definitions(word_uuid, definitions):
    session = Session()
    try:
        word = session.query(WordUrl).filter_by(word_uuid=word_uuid).first()
        if word:
            word.definitions = definitions
            word.needs_review = False  # optionally set this
            session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_words_for_review():
    session = Session()
    try:
        # Fetch all words with needs_review=True
        return session.query(WordUrl).filter(WordUrl.needs_review == True).all()
    except Exception as e:
        print(f"Error fetching words for review: {e}")
        session.rollback()
        return []

def update_word_needs_review(word_uuid):
    session = Session()
    try:
        # Update the needs_review flag to False for the given word_uuid
        word_url = session.query(WordUrl).filter_by(word_uuid=word_uuid).first()
        if word_url:
            word_url.needs_review = False
            session.commit()
    except Exception as e:
        print(f"Error updating needs_review flag: {e}")
        session.rollback()

# ---------- WORD DEFINITIONS CRUD ----------


def insert_word_definitions(word_uuid, definitions, word_text):
    session = Session()
    try:
        # Insert definitions for the given word_uuid
        for definition in definitions:
            word_def = WordDefinition(
                word_uuid=word_uuid,
                definition=definition,
                word=word_text,
                is_deleted=False  # Default to not deleted
            )
            session.add(word_def)
        session.commit()
    except Exception as e:
        print(f"Error inserting word definitions: {e}")
        session.rollback()
