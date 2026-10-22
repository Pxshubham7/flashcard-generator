import os
import json
import csv
import io
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

st.set_page_config(
    page_title="AI Flashcard Generator",
    page_icon="📚",
    layout="centered"
)

st.title("📚 AI Flashcard Generator")
st.caption("Create smart revision flashcards using AI")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        st.error("Please configure your GROQ_API_KEY.")
        st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

if "cards" not in st.session_state:
    st.session_state.cards = []

if "index" not in st.session_state:
    st.session_state.index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

topic = st.text_area(
    "Enter a topic or paste your notes",
    placeholder="Example: Explain stack and queue in DSA",
    height=140
)

count = st.slider("Number of flashcards", 3, 15, 5)

if st.button("✨ Generate Flashcards", type="primary"):
    if not topic.strip():
        st.warning("Please enter a topic or notes.")
    else:
        prompt = f"""
Create exactly {count} educational flashcards
from these notes or this topic:

{topic}

Return a valid JSON object with a "flashcards" array.
Each item must have "question" and "answer" fields.

Example:
{{
  "flashcards": [
    {{
      "question": "What is a stack?",
      "answer": "A LIFO data structure."
    }}
  ]
}}
"""
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an educational flashcard creator. Return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content
            data = json.loads(raw)

            if isinstance(data, dict):
                cards = data.get("flashcards", [])
            else:
                cards = data

            if not isinstance(cards, list) or not cards:
                raise ValueError("No flashcards returned")

            for card in cards:
                if not isinstance(card, dict):
                    raise ValueError("Invalid flashcard format")
                if not isinstance(card.get("question"), str):
                    raise ValueError("Missing question")
                if not isinstance(card.get("answer"), str):
                    raise ValueError("Missing answer")

            st.session_state.cards = cards
            st.session_state.index = 0
            st.session_state.show_answer = False

        except Exception as e:
            st.error(f"Generation failed: {e}")

cards = st.session_state.cards

if cards:
    index = st.session_state.index
    card = cards[index]

    st.divider()
    st.subheader(f"Flashcard {index + 1} of {len(cards)}")

    with st.container(border=True):
        st.markdown(f"### {card['question']}")

        if st.session_state.show_answer:
            st.success(card["answer"])

    if st.button("🔄 Flip Card"):
        st.session_state.show_answer = (
            not st.session_state.show_answer
        )
        st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅ Previous", disabled=index == 0):
            st.session_state.index -= 1
            st.session_state.show_answer = False
            st.rerun()

    with col2:
        if st.button(
            "Next ➡",
            disabled=index == len(cards) - 1
        ):
            st.session_state.index += 1
            st.session_state.show_answer = False
            st.rerun()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Question", "Answer"])

    for item in cards:
        writer.writerow([
            item["question"],
            item["answer"]
        ])

    st.download_button(
        "📥 Download Flashcards as CSV",
        data=output.getvalue(),
        file_name="flashcards.csv",
        mime="text/csv"
    )