import csv
import io

import streamlit as st

from core.database import init_db, save_check, get_history, find_cached
from core.ollama_client import check_message
from core.ocr import extract_text_from_image

st.set_page_config(page_title="Hoax Checker", page_icon="🔍", layout="centered")
init_db()

st.title("🔍 Hoax Checker")
st.caption("Check viral messages using a local LLM (Ollama) + internet verification.")

tab_text, tab_image, tab_batch, tab_history = st.tabs(
    ["Text Check", "Image Check", "Batch Check", "History"]
)


def run_check(message: str, source_input: str = "text"):
    cached = find_cached(message)
    if cached:
        st.info(f"This message was already checked on {cached['timestamp']}")
        st.markdown(cached["verdict"])
        return cached["verdict"]

    with st.spinner("Analyzing (searching the internet + checking the hoax knowledge base)..."):
        verdict, sources = check_message(message)

    save_check(message, verdict, sources, source_input)
    st.markdown(verdict)
    return verdict


# --- Tab: Text Check ---
with tab_text:
    message = st.text_area("Paste the message you want to check", height=150)
    if st.button("Check now", key="btn_text"):
        if message.strip():
            run_check(message.strip(), source_input="text")
        else:
            st.warning("The message is empty.")


# --- Tab: Image Check ---
with tab_image:
    uploaded_image = st.file_uploader(
        "Upload a message screenshot", type=["png", "jpg", "jpeg"]
    )
    if uploaded_image:
        st.image(uploaded_image, caption="Preview", use_container_width=True)

    if st.button("Extract & Check", key="btn_image"):
        if uploaded_image:
            # save temporarily so pytesseract can read it
            temp_path = f"/tmp/{uploaded_image.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_image.getbuffer())

            try:
                text = extract_text_from_image(temp_path)
            except RuntimeError as e:
                st.error(str(e))
                text = ""

            if text:
                st.text_area("Extracted text", value=text, height=100, disabled=True)
                run_check(text, source_input="image")
            else:
                st.warning("No text could be read from the image.")
        else:
            st.warning("Upload an image first.")


# --- Tab: Batch Check ---
with tab_batch:
    uploaded_file = st.file_uploader(
        "Upload a .txt file (1 message per line) or .csv (column 'message')",
        type=["txt", "csv"],
        key="batch_uploader",
    )

    if st.button("Process batch", key="btn_batch"):
        if not uploaded_file:
            st.warning("Upload a file first.")
        else:
            content = uploaded_file.getvalue().decode("utf-8")
            if uploaded_file.name.endswith(".csv"):
                reader = csv.DictReader(io.StringIO(content))
                messages = [row["message"] for row in reader if row.get("message")]
            else:
                messages = [line.strip() for line in content.splitlines() if line.strip()]

            if not messages:
                st.warning("No messages found in the file.")
            else:
                st.write(f"Found {len(messages)} messages. Processing...")
                progress = st.progress(0)
                results = []

                for i, msg in enumerate(messages):
                    verdict, sources = check_message(msg)
                    save_check(msg, verdict, sources, source_input="batch")
                    results.append({"message": msg, "verdict": verdict})
                    progress.progress((i + 1) / len(messages))

                st.success("Done!")
                for r in results:
                    with st.expander(r["message"][:80]):
                        st.markdown(r["verdict"])

                # CSV summary download button
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=["message", "verdict"])
                writer.writeheader()
                writer.writerows(results)
                st.download_button(
                    "Download CSV summary",
                    data=output.getvalue(),
                    file_name="batch_results.csv",
                    mime="text/csv",
                )


# --- Tab: History ---
with tab_history:
    limit = st.slider("Number of recent entries", 5, 50, 10)
    history = get_history(limit)

    if not history:
        st.info("No history yet.")
    else:
        for h in history:
            with st.expander(f"[{h['timestamp']}] ({h['source_input']}) — {h['message'][:60]}"):
                st.write("**Message:**", h["message"])
                st.markdown("**Result:**")
                st.markdown(h["verdict"])
