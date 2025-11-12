"""
Test the Tolaria API with a real example
"""

import requests
import json

def test_api():
    url = "http://localhost:8000/api/ask"

    # Test query
    payload = {
        "question": "Player 1 gioca Lightning Bolt con target Player 2. Player 2 risponde con Counterspell su Lightning Bolt. Come si risolve la stack?",
        "cards": ["Lightning Bolt", "Counterspell"],
        "player_actions": [
            {
                "card": "Lightning Bolt",
                "player": "Player 1",
                "targets": ["Player 2"]
            },
            {
                "card": "Counterspell",
                "player": "Player 2",
                "targets": ["Lightning Bolt"]
            }
        ]
    }

    print("🔍 Testing Tolaria API...")
    print(f"Question: {payload['question']}")
    print(f"Cards: {', '.join(payload['cards'])}")
    print("\nSending request...")

    try:
        response = requests.post(url, json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()

            print("\n✅ SUCCESS!\n")
            print("=" * 60)
            print("EXPLANATION")
            print("=" * 60)
            print(data.get('explanation', 'No explanation provided'))

            print("\n" + "=" * 60)
            print("RULES REFERENCES")
            print("=" * 60)
            for ref in data.get('rules_references', []):
                print(f"  • {ref}")

            print("\n" + "=" * 60)
            print("STACK VISUALIZATION")
            print("=" * 60)
            for item in data.get('stack_visualization', []):
                card = item['card']
                print(f"  [{item.get('position', '?')}] {card['name']} - {item['controller']}")

            print("\n" + "=" * 60)
            print("RESOLUTION STEPS")
            print("=" * 60)
            for step in data.get('resolution_steps', []):
                print(f"\n  Step {step.get('step_number', '?')}: {step.get('action', '')}")
                print(f"    {step.get('description', '')}")

            print("\n" + "=" * 60)

        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(response.text)

    except requests.exceptions.Timeout:
        print("\n⏱️  Request timed out (this might happen on first run)")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    test_api()
