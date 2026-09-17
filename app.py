import csv
import io

import streamlit as st

from core.database import init_db, save_check, get_history, find_cached
from core.ollama_client import check_message
from core.ocr import extract_text_from_image

st.set_page_config(page_title="Cek Hoax", page_icon="🔍", layout="centered")
init_db()

st.title("🔍 Cek Hoax")
st.caption("Cek pesan viral pakai LLM lokal (Ollama) + verifikasi internet.")

tab_teks, tab_gambar, tab_batch, tab_riwayat = st.tabs(
    ["Cek Teks", "Cek Gambar", "Batch Check", "Riwayat"]
)


def run_check(message: str, source_input: str = "text"):
    cached = find_cached(message)
    if cached:
        st.info(f"Pesan ini pernah dicek pada {cached['timestamp']}")
        st.markdown(cached["verdict"])
        return cached["verdict"]

    with st.spinner("Menganalisis (search internet + cek database hoax lama)..."):
        verdict, sources = check_message(message)

    save_check(message, verdict, sources, source_input)
    st.markdown(verdict)
    return verdict


# --- Tab: Cek Teks ---
with tab_teks:
    message = st.text_area("Paste pesan yang mau dicek", height=150)
    if st.button("Cek sekarang", key="btn_teks"):
        if message.strip():
            run_check(message.strip(), source_input="text")
        else:
            st.warning("Pesannya masih kosong.")


# --- Tab: Cek Gambar ---
with tab_gambar:
    uploaded_image = st.file_uploader(
        "Upload screenshot pesan", type=["png", "jpg", "jpeg"]
    )
    if uploaded_image:
        st.image(uploaded_image, caption="Preview", use_container_width=True)

    if st.button("Extract & Cek", key="btn_gambar"):
        if uploaded_image:
            # simpan sementara biar bisa dibaca pytesseract
            temp_path = f"/tmp/{uploaded_image.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_image.getbuffer())

            try:
                text = extract_text_from_image(temp_path)
            except RuntimeError as e:
                st.error(str(e))
                text = ""

            if text:
                st.text_area("Teks yang terbaca", value=text, height=100, disabled=True)
                run_check(text, source_input="image")
            else:
                st.warning("Tidak ada teks yang terbaca dari gambar.")
        else:
            st.warning("Upload gambar dulu.")


# --- Tab: Batch Check ---
with tab_batch:
    uploaded_file = st.file_uploader(
        "Upload file .txt (1 pesan per baris) atau .csv (kolom 'message')",
        type=["txt", "csv"],
        key="batch_uploader",
    )

    if st.button("Proses batch", key="btn_batch"):
        if not uploaded_file:
            st.warning("Upload file dulu.")
        else:
            content = uploaded_file.getvalue().decode("utf-8")
            if uploaded_file.name.endswith(".csv"):
                reader = csv.DictReader(io.StringIO(content))
                messages = [row["message"] for row in reader if row.get("message")]
            else:
                messages = [line.strip() for line in content.splitlines() if line.strip()]

            if not messages:
                st.warning("Tidak ada pesan ditemukan di file.")
            else:
                st.write(f"Ditemukan {len(messages)} pesan. Memproses...")
                progress = st.progress(0)
                results = []

                for i, msg in enumerate(messages):
                    verdict, sources = check_message(msg)
                    save_check(msg, verdict, sources, source_input="batch")
                    results.append({"message": msg, "verdict": verdict})
                    progress.progress((i + 1) / len(messages))

                st.success("Selesai!")
                for r in results:
                    with st.expander(r["message"][:80]):
                        st.markdown(r["verdict"])

                # tombol download rekap CSV
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=["message", "verdict"])
                writer.writeheader()
                writer.writerows(results)
                st.download_button(
                    "Download rekap CSV",
                    data=output.getvalue(),
                    file_name="hasil_batch.csv",
                    mime="text/csv",
                )


# --- Tab: Riwayat ---
with tab_riwayat:
    limit = st.slider("Jumlah entri terakhir", 5, 50, 10)
    history = get_history(limit)

    if not history:
        st.info("Belum ada riwayat.")
    else:
        for h in history:
            with st.expander(f"[{h['timestamp']}] ({h['source_input']}) — {h['message'][:60]}"):
                st.write("**Pesan:**", h["message"])
                st.markdown("**Hasil:**")
                st.markdown(h["verdict"])
