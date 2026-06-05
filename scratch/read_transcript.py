import json
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    path = r'C:\Users\RICARDO\.gemini\antigravity\brain\285582ac-de2b-40d3-aa1c-dd34f049d374\.system_generated\logs\transcript.jsonl'
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            if data.get('type') == 'USER_INPUT':
                print(f"=== STEP {data.get('step_index')} ===")
                print(data.get('content'))
                print("-" * 40)

if __name__ == '__main__':
    main()
