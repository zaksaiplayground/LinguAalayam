import streamlit as st
import pandas as pd
import os

# File paths
INPUT_CSV = "data/no_definition_df.csv"
REVIEWED_CSV = "data/reviewed_words.csv"

# Load CSV
if os.path.exists(INPUT_CSV):
    df = pd.read_csv(INPUT_CSV, sep="\t")
else:
    st.error("Input CSV not found.")
    st.stop()

if df.empty:
    st.success("🎉 All words reviewed!")
    st.stop()

# Display the first word
current_word = df.iloc[0]
word = current_word["word"]
url = current_word["url"]

st.title("📘 Wiktionary Word Reviewer")
st.markdown(f"### Word: **{word}**")
st.markdown(f"[🔗 Open in new tab]({url})")

# Layout: iframe left, input right
left_col, right_col = st.columns([2, 1])

with left_col:
    st.components.v1.iframe(url, height=750)

with right_col:
    # Use session_state to preserve and clear input
    if "definitions" not in st.session_state:
        st.session_state.definitions = ""

    definitions = st.text_area("Definitions", value=st.session_state.definitions,
                               height=300, label_visibility="collapsed")

    submit = st.button("✅ Submit")
    skip = st.button("⏭️ Skip")

    if submit:
        if definitions.strip() == "":
            st.warning("Please enter at least one definition.")
            st.stop()

        reviewed_rows = [
            {"word": word, "definition": d.strip()}
            for d in definitions.strip().splitlines()
            if d.strip()
        ]

        reviewed_df = pd.DataFrame(reviewed_rows)
        if os.path.exists(REVIEWED_CSV):
            reviewed_df.to_csv(REVIEWED_CSV, mode='a', index=False, header=False, sep="\t")
        else:
            reviewed_df.to_csv(REVIEWED_CSV, index=False, sep="\t")

        df = df.drop(index=0).reset_index(drop=True)
        df.to_csv(INPUT_CSV, index=False, sep="\t")

        st.session_state.definitions = ""  # clear before rerun
        st.rerun()

    if skip:
        df = df.drop(index=0).reset_index(drop=True)
        df.to_csv(INPUT_CSV, index=False, sep="\t")

        st.session_state.definitions = ""  # clear before rerun
        st.rerun()