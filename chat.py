import csv
import sys
from pathlib import Path

from core.database import init_db, save_check, get_history, find_cached
from core.ollama_client import check_message
from core.ocr import extract_text_from_image


def check_and_report(message: str, source_input: str = "text", use_cache: bool = True):
    if use_cache:
        cached = find_cached(message)
        if cached:
            print(f"\n[Pesan ini pernah dicek pada {cached['timestamp']}]")
            print(f"Hasil:\n{cached['verdict']}\n")
            return cached["verdict"]

    print("\nMenganalisis...\n")
    verdict, sources = check_message(message)
    print(f"Hasil:\n{verdict}\n")
    save_check(message, verdict, sources, source_input)
    return verdict


def mode_text_check():
    message = input("Paste pesan yang mau dicek: ").strip()
    if message:
        check_and_report(message, source_input="text")


def mode_image_check():
    path = input("Path ke file gambar (screenshot): ").strip()
    if not Path(path).exists():
        print("File tidak ditemukan.")
        return
    try:
        text = extract_text_from_image(path)
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    if not text:
        print("Tidak ada teks yang terbaca dari gambar.")
        return

    print(f"\nTeks yang terbaca:\n{text}\n")
    check_and_report(text, source_input="image")


def mode_batch_check():
    path = input("Path ke file .txt (1 pesan per baris) atau .csv (kolom 'message'): ").strip()
    file_path = Path(path)
    if not file_path.exists():
        print("File tidak ditemukan.")
        return

    messages = []
    if file_path.suffix == ".csv":
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            messages = [row["message"] for row in reader if row.get("message")]
    else:
        with open(file_path, encoding="utf-8") as f:
            messages = [line.strip() for line in f if line.strip()]

    if not messages:
        print("Tidak ada pesan yang ditemukan di file.")
        return

    print(f"Ditemukan {len(messages)} pesan. Memproses...\n")
    results = []
    for i, msg in enumerate(messages, 1):
        print(f"--- Pesan {i}/{len(messages)} ---")
        verdict = check_and_report(msg, source_input="batch")
        results.append({"message": msg, "verdict": verdict})

    output_path = file_path.parent / f"{file_path.stem}_hasil.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["message", "verdict"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSelesai. Rekap disimpan di: {output_path}")


def mode_history():
    limit = input("Tampilkan berapa entri terakhir? (default 10): ").strip()
    limit = int(limit) if limit.isdigit() else 10

    history = get_history(limit)
    if not history:
        print("Belum ada riwayat.")
        return

    for h in history:
        print(f"\n[{h['timestamp']}] ({h['source_input']})")
        print(f"Pesan: {h['message'][:100]}{'...' if len(h['message']) > 100 else ''}")
        print(f"Verdict: {h['verdict'][:200]}{'...' if len(h['verdict']) > 200 else ''}")
        print("-" * 50)


def main():
    init_db()
    print("=== Cek Hoax ===\n")

    menu = {
        "1": ("Cek pesan teks", mode_text_check),
        "2": ("Cek dari gambar/screenshot (OCR)", mode_image_check),
        "3": ("Batch check dari file", mode_batch_check),
        "4": ("Lihat riwayat", mode_history),
        "5": ("Keluar", None),
    }

    while True:
        print("\nMenu:")
        for key, (label, _) in menu.items():
            print(f"  {key}. {label}")

        choice = input("\nPilih: ").strip()
        if choice == "5":
            break
        elif choice in menu:
            _, func = menu[choice]
            func()
        else:
            print("Pilihan tidak valid.")


if __name__ == "__main__":
    main()
