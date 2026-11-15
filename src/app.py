# src/app.py  (Day 11, session-state fix Phase 1)
# Run with: streamlit run src/app.py
# (The full web front end is src/api.py + web/; this is the simple Streamlit UI.)

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

import streamlit as st  # noqa: E402
from src.spellchecker import SpellChecker  # noqa: E402

st.set_page_config(
    page_title="Sindhi-English Dictionary and Spell-Checker",
    page_icon="📖",
    layout="centered",
)
st.markdown("""<style>
textarea, .sd { direction: rtl; font-family: 'Noto Naskh Arabic', 'Segoe UI', serif; font-size: 1.3rem; }
</style>""", unsafe_allow_html=True)


@st.cache_resource
def load_checker():
    return SpellChecker()


checker = load_checker()


def show_entry(word):
    meanings = checker.meanings(word)
    translations = checker.dictionary.get_translations(word)
    if translations:
        st.markdown("**English Translation**")
        for translation in translations[:6]:
            st.write(f"- {translation}")
    if meanings:
        st.markdown("**Sindhi Definition**")
        for meaning in meanings[:3]:
            st.markdown(f"<div class='sd'>{meaning}</div>", unsafe_allow_html=True)
    if not meanings and not translations:
        st.info("No definition or translation recorded for this word.")


st.title("Sindhi-English Dictionary and Spell-Checker")
st.caption("Made by Sneha Haseja and Javeria Jatoi")
st.write("Look up Sindhi words and check spelling.")

text = st.text_area(
    "Enter a Sindhi word or sentence",
    height=120,
    placeholder="سنڌي لفظ هتي لکو...",
)

# Phase 1 fix: results live in session_state, so clicking a "Look up" button
# (which reruns the script) no longer makes the results disappear.
if st.button("Check spelling", type="primary"):
    if not text.strip():
        st.warning("Please enter a Sindhi word or sentence.")
        st.session_state.pop("results", None)
    else:
        st.session_state["results"] = checker.check_text(text)
        st.session_state.pop("lookup_word", None)

results = st.session_state.get("results")
if results:
    st.subheader("Results")
    for index, item in enumerate(r for r in results if r["status"] != "skip"):
        token = item["token"]
        if item["known"]:
            st.success(f"{token} — Recognized word ({item['status']})")
        else:
            st.error(f"{token} — Not found in dictionary")
            if item["suggestions"]:
                st.markdown("**Did you mean?**")
                cols = st.columns(len(item["suggestions"]))
                for col, suggestion in zip(cols, item["suggestions"]):
                    word = suggestion["word"]
                    if col.button(f"{word}", key=f"lookup-{index}-{word}"):
                        st.session_state["lookup_word"] = word

if st.session_state.get("lookup_word"):
    word = st.session_state["lookup_word"]
    st.divider()
    st.subheader(f"Dictionary lookup: {word}")
    show_entry(word)

st.caption("Dictionary data: SindhiLanguage.org, prepared and curated by Amar Fayaz Buriro (CC BY 4.0).")
