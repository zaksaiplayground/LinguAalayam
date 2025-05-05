import streamlit as st
import pandas as pd
import os

# Directory and output file
NO_DEF_DATA_DIR = "data/preprocessed/no_def"
REVIEWED_CSV = "data/preprocessed/reviewed_words.csv"

# Get list of CSV files in the data directory (excluding reviewed file)
csv_files = [f for f in os.listdir(NO_DEF_DATA_DIR)]
csv_files.sort()

if not csv_files:
    st.success("🎉 No CSV files left to review!")
    st.stop()

# Track which file is currently being processed
if "current_file_index" not in st.session_state:
    st.session_state.current_file_index = 0

current_file = os.path.join(NO_DEF_DATA_DIR, csv_files[st.session_state.current_file_index])

# Load current CSV
try:
    df = pd.read_csv(current_file, sep="\t")
except Exception as e:
    st.error(f"Error reading {current_file}: {e}")
    st.stop()

# Skip to next file if empty
while df.empty:
    st.session_state.current_file_index += 1
    if st.session_state.current_file_index >= len(csv_files):
        st.success("🎉 All words from all files reviewed!")
        st.stop()
    current_file = os.path.join(NO_DEF_DATA_DIR, csv_files[st.session_state.current_file_index])
    df = pd.read_csv(current_file, sep="\t")

# Display current word
current_word = df.iloc[0]
word = current_word["word"]
url = current_word["url"]

st.title("📘 Wiktionary Word Reviewer")
st.markdown(f"**Source file:** `{os.path.basename(current_file)}`")
st.markdown(f"### Word: **{word}**")
st.markdown(f"[🔗 Open in new tab]({url})")

left_col, right_col = st.columns([2, 1])

with left_col:
    st.components.v1.iframe(url, height=750)

with right_col:
    if "definitions" not in st.session_state:
        st.session_state.definitions = ""

    definitions = st.text_area("Definitions", value=st.session_state.definitions,
                               height=300, label_visibility="collapsed")

    submit = st.button("✅ Submit")
    skip = st.button("⏭️ Skip")

    def advance_to_next():
        df.drop(index=0).reset_index(drop=True).to_csv(current_file, sep="\t", index=False)
        st.session_state.definitions = ""
        st.rerun()

    if submit:
        if definitions.strip() == "":
            st.warning("Please enter at least one definition.")
            st.stop()

        reviewed_rows = [
            {"word": word, "definition": d.strip()}
            for d in definitions.strip().splitlines() if d.strip()
        ]

        reviewed_df = pd.DataFrame(reviewed_rows)
        if os.path.exists(REVIEWED_CSV):
            reviewed_df.to_csv(REVIEWED_CSV, mode='a', index=False, header=False, sep="\t")
        else:
            reviewed_df.to_csv(REVIEWED_CSV, index=False, sep="\t")

        advance_to_next()

    if skip:
        advance_to_next()
