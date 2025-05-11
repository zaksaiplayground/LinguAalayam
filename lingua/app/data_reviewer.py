import streamlit as st
from lingua.database.crud import get_words_for_review, insert_word_definitions, update_word_needs_review
from urllib.parse import unquote

def _initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    if "definitions" not in st.session_state:
        st.session_state.definitions = ""

def _get_current_word(words):
    """Get the current word based on the session state index."""
    if st.session_state.current_index >= len(words):
        return None
    
    word_for_review = words[st.session_state.current_index]
    word_url = word_for_review.word_url
    word_uuid = word_for_review.word_uuid
    word_text = unquote(word_url.split("/")[-1])
    
    return {
        "word_for_review": word_for_review,
        "word_url": word_url,
        "word_uuid": word_uuid,
        "word_text": word_text
    }

def _display_word_content(word_data):
    """Display the word content in the UI."""
    st.title("📘 Wiktionary Word Reviewer")
    
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.components.v1.iframe(word_data["word_url"], height=750)
    
    return right_col

def _display_definition_input(container):
    """Display the definition input area."""
    definitions = container.text_area(
        "Definitions",
        value=st.session_state.definitions,
        height=300,
        label_visibility="collapsed"
    )
    
    submit = container.button("✅ Submit")
    skip = container.button("⏭️ Skip")
    
    return definitions, submit, skip

def _handle_submit(definitions, word_data):
    """Handle the submission of definitions."""
    if definitions.strip() == "":
        st.warning("Please enter at least one definition.")
        return False
    
    definitions_list = [d.strip() for d in definitions.strip().splitlines() if d.strip()]
    
    insert_word_definitions(word_data["word_uuid"], definitions_list, word_text=word_data["word_text"])
    update_word_needs_review(word_data["word_uuid"])
    
    st.session_state.current_index += 1
    st.session_state.definitions = ""
    return True

def _handle_skip(word_data):
    """Handle skipping the current word."""
    update_word_needs_review(word_data["word_uuid"])
    st.session_state.current_index += 1
    return True

def main():
    """Main application function."""
    _initialize_session_state()
    
    # Get words for review
    words_for_review = get_words_for_review()

    st.info(f"Number of words to review: {len(words_for_review)}")
    
    current_word_data = _get_current_word(words_for_review)
    if current_word_data is None:
        st.success("🎉 All words reviewed!")
        return
    
    right_column = _display_word_content(current_word_data)
    
    definitions, submit_button, skip_button = _display_definition_input(right_column)
    
    if submit_button:
        if _handle_submit(definitions, current_word_data):
            st.rerun()
    
    if skip_button:
        if _handle_skip(current_word_data):
            st.rerun()

if __name__ == "__main__":
    main()