import json
import os
from datetime import datetime

QUIZ_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "quiz_output.json")
PERF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "performance.json")

def load_quizzes(path=QUIZ_PATH):
    if not os.path.exists(path):
        print(f"❌ quiz file not found at {path}")
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_performance(entries, path=PERF_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = []
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                existing = json.load(f) or []
        except Exception:
            existing = []
    existing.extend(entries)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)

def _prompt_module_selection(module_ids):
    print("Available modules:")
    for i, m in enumerate(module_ids, 1):
        print(f"  {i}. {m}")
    sel = input("Choose module(s) by number (comma-separated), or 'all': ").strip()
    if sel.lower() == "all":
        return module_ids
    chosen = []
    for part in sel.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            idx = int(part)
            if 1 <= idx <= len(module_ids):
                chosen.append(module_ids[idx - 1])
        except Exception:
            # allow direct module id input
            if part in module_ids and part not in chosen:
                chosen.append(part)
    return chosen

def _prompt_answer(num_options=4):
    prompt = f"Select an option (1-{num_options}) or A-{chr(ord('A')+num_options-1)}: "
    while True:
        ans = input(prompt).strip()
        if not ans:
            continue
        # numeric
        if ans.isdigit():
            n = int(ans)
            if 1 <= n <= num_options:
                return n - 1
        # letter
        a = ans.upper()
        if len(a) == 1 and 'A' <= a <= chr(ord('A')+num_options-1):
            return ord(a) - ord('A')
        print("Invalid choice. Try again.")

def run_interactive_quiz():
    data = load_quizzes()
    if not data:
        return
    module_ids = list(data.keys())
    selected = _prompt_module_selection(module_ids)
    if not selected:
        print("No modules selected. Exiting.")
        return

    perf_entries = []
    for mod in selected:
        mdata = data.get(mod, {})
        quizzes = mdata.get("quizzes", [])
        if not quizzes:
            print(f"⚠️  No quizzes found for module '{mod}'. Skipping.")
            continue
        print(f"\n--- Module: {mod} ---")
        for i, q in enumerate(quizzes, 1):
            question = q.get("question", "").strip()
            options = q.get("options", [])
            correct_idx = q.get("correct_option_index")
            explanation = q.get("explanation", "")
            print(f"\nQuestion {i}: {question}")
            for oi, opt in enumerate(options, 1):
                print(f"  {oi}. {opt}")
            selected_idx = _prompt_answer(num_options=len(options))
            selected_text = options[selected_idx] if 0 <= selected_idx < len(options) else ""
            correct_text = options[correct_idx] if isinstance(correct_idx, int) and 0 <= correct_idx < len(options) else ""
            is_correct = (selected_idx == correct_idx)
            if is_correct:
                print("✅ Correct.")
            else:
                print("❌ Incorrect.")
            print(f"Correct answer: {correct_text}")
            if explanation:
                print(f"Explanation: {explanation}")

            perf_entries.append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "module": mod,
                "question": question,
                "selected_index": selected_idx,
                "selected_text": selected_text,
                "correct_index": correct_idx,
                "correct_text": correct_text,
                "correct": is_correct,
                "explanation": explanation
            })

    if perf_entries:
        save_performance(perf_entries)
        print(f"\n✅ Performance recorded to {PERF_PATH}")
    else:
        print("\nNo responses recorded.")

def main():
    run_interactive_quiz()

if __name__ == "__main__":
    main()

