import csv
from pathlib import Path

from core.database import init_db, save_check, get_history, find_cached
from core.ollama_client import check_message
from core.ocr import extract_text_from_image


def check_and_report(message: str, source_input: str = "text", use_cache: bool = True):
    if use_cache:
        cached = find_cached(message)
        if cached:
            print(f"\n[This message was already checked on {cached['timestamp']}]")
            print(f"Result:\n{cached['verdict']}\n")
            return cached["verdict"]

    print("\nAnalyzing...\n")
    verdict, sources = check_message(message)
    print(f"Result:\n{verdict}\n")
    save_check(message, verdict, sources, source_input)
    return verdict


def mode_text_check():
    message = input("Paste the message you want to check: ").strip()
    if message:
        check_and_report(message, source_input="text")


def mode_image_check():
    path = input("Path to the image file (screenshot): ").strip()
    if not Path(path).exists():
        print("File not found.")
        return
    try:
        text = extract_text_from_image(path)
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    if not text:
        print("No text could be read from the image.")
        return

    print(f"\nExtracted text:\n{text}\n")
    check_and_report(text, source_input="image")


def mode_batch_check():
    path = input("Path to a .txt file (1 message per line) or .csv (column 'message'): ").strip()
    file_path = Path(path)
    if not file_path.exists():
        print("File not found.")
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
        print("No messages found in the file.")
        return

    print(f"Found {len(messages)} messages. Processing...\n")
    results = []
    for i, msg in enumerate(messages, 1):
        print(f"--- Message {i}/{len(messages)} ---")
        verdict = check_and_report(msg, source_input="batch")
        results.append({"message": msg, "verdict": verdict})

    output_path = file_path.parent / f"{file_path.stem}_results.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["message", "verdict"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. Summary saved to: {output_path}")


def mode_history():
    limit = input("How many recent entries to show? (default 10): ").strip()
    limit = int(limit) if limit.isdigit() else 10

    history = get_history(limit)
    if not history:
        print("No history yet.")
        return

    for h in history:
        print(f"\n[{h['timestamp']}] ({h['source_input']})")
        print(f"Message: {h['message'][:100]}{'...' if len(h['message']) > 100 else ''}")
        print(f"Verdict: {h['verdict'][:200]}{'...' if len(h['verdict']) > 200 else ''}")
        print("-" * 50)


def main():
    init_db()
    print("=== Hoax Checker ===\n")

    menu = {
        "1": ("Check a text message", mode_text_check),
        "2": ("Check from an image/screenshot (OCR)", mode_image_check),
        "3": ("Batch check from a file", mode_batch_check),
        "4": ("View history", mode_history),
        "5": ("Exit", None),
    }

    while True:
        print("\nMenu:")
        for key, (label, _) in menu.items():
            print(f"  {key}. {label}")

        choice = input("\nChoose: ").strip()
        if choice == "5":
            break
        elif choice in menu:
            _, func = menu[choice]
            func()
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
