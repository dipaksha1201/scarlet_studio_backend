# main.py
import json
from generation import content

def main():
    print("\n=== QUIZ GENERATOR ===")
    output = content.generate_quizzes_from_static()
    if output:
        print(f"All quizzes written to: {output}")

if __name__ == "__main__":
    main()
