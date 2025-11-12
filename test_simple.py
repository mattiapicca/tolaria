"""
Simple test of Tolaria components
Tests Scryfall API integration without heavy dependencies
"""

import asyncio
import sys


async def test_scryfall():
    """Test Scryfall API integration"""
    print("\n" + "=" * 60)
    print("TEST 1: Scryfall API Integration")
    print("=" * 60)

    try:
        from api.scryfall import ScryfallClient

        client = ScryfallClient()

        # Test 1: Search for a simple card
        print("\n1. Searching for 'Lightning Bolt'...")
        card = await client.search_card("Lightning Bolt")

        print(f"   ✓ Found: {card['name']}")
        print(f"   ✓ Type: {card['type_line']}")
        print(f"   ✓ Mana Cost: {card['mana_cost']}")
        print(f"   ✓ Text: {card['oracle_text'][:60]}...")

        # Test 2: Search for multiple cards
        print("\n2. Searching for multiple cards...")
        cards = await client.search_cards_bulk(["Counterspell", "Lightning Bolt"])

        for card in cards:
            if card.get('found'):
                print(f"   ✓ {card['name']} - {card['mana_cost']}")

        # Test 3: Get card types
        print("\n3. Analyzing card types...")
        types = client.get_card_types(card)
        print(f"   ✓ Is Instant: {types['is_instant']}")
        print(f"   ✓ Is Sorcery: {types['is_sorcery']}")

        # Test 4: Get card image
        print("\n4. Getting card image URL...")
        if 'image_uris' in card:
            print(f"   ✓ Image URL: {card['image_uris']['normal'][:50]}...")

        print("\n✅ Scryfall API test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Scryfall API test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rules_parser():
    """Test rules PDF parser"""
    print("\n" + "=" * 60)
    print("TEST 2: Rules PDF Parser")
    print("=" * 60)

    try:
        from rules.parser import RulesParser

        print("\n1. Initializing parser...")
        parser = RulesParser("mtgrules.pdf")

        print("   ✓ Parser initialized")

        print("\n2. Parsing PDF (this may take a minute)...")
        rules_data = parser.parse_pdf()

        print(f"   ✓ Parsed {len(rules_data['rules'])} rules")
        print(f"   ✓ Parsed {len(rules_data['glossary'])} glossary terms")

        # Test search
        print("\n3. Testing rule search...")
        stack_rules = parser.get_stack_rules()
        print(f"   ✓ Found {len(stack_rules)} stack-related rules")

        if stack_rules:
            print(f"   ✓ Example: Rule {stack_rules[0]['number']}")
            print(f"      {stack_rules[0]['text'][:80]}...")

        # Test specific rule lookup
        print("\n4. Testing specific rule lookup...")
        rule = parser.get_rule("100.1")
        if rule:
            print(f"   ✓ Rule 100.1: {rule['text'][:80]}...")

        print("\n✅ Rules Parser test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Rules Parser test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stack_visualization():
    """Test stack visualizer without full resolver"""
    print("\n" + "=" * 60)
    print("TEST 3: Stack Visualizer")
    print("=" * 60)

    try:
        from stack.visualizer import StackVisualizer
        from api.scryfall import ScryfallClient

        client = ScryfallClient()
        visualizer = StackVisualizer()

        print("\n1. Fetching test cards...")
        cards = await client.search_cards_bulk(["Lightning Bolt", "Counterspell"])

        # Create mock stack with CORRECT order:
        # First Lightning Bolt is played (position 0 in list = bottom of stack)
        # Then Counterspell is played in response (position 1 in list = top of stack)
        stack = []

        lightning_bolt = next((c for c in cards if c['name'] == 'Lightning Bolt'), None)
        counterspell = next((c for c in cards if c['name'] == 'Counterspell'), None)

        if lightning_bolt and counterspell:
            # Bottom of stack (played first)
            stack.append({
                "card": lightning_bolt,
                "controller": "Player 1",
                "targets": ["Player 2"],
                "position": 0
            })

            # Top of stack (played second, in response)
            stack.append({
                "card": counterspell,
                "controller": "Player 2",
                "targets": ["Lightning Bolt"],
                "position": 1
            })

        print(f"   ✓ Created stack with {len(stack)} items")
        print(f"   ✓ Stack order (bottom→top): {[s['card']['name'] for s in stack]}")

        print("\n2. Generating HTML visualization...")
        html = visualizer.generate_stack_html(stack)

        print(f"   ✓ Generated {len(html)} characters of HTML")

        # Save to file
        filename = "test_stack.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"   ✓ Saved visualization to {filename}")
        print(f"   → Open {filename} in your browser to view!")

        print("\n   📝 Scenario:")
        print("      1. Player 1 gioca Lightning Bolt con target Player 2")
        print("      2. Player 2 risponde con Counterspell con target Lightning Bolt")
        print("      3. Counterspell risolve per primo (LIFO) e countera Lightning Bolt")
        print("      4. Lightning Bolt viene counterato e non risolve")

        print("\n✅ Stack Visualizer test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Stack Visualizer test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 20 + "TOLARIA TEST SUITE" + " " * 20 + "║")
    print("║" + " " * 14 + "MTG Rules & Stack AI Agent" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")

    results = []

    # Test 1: Scryfall API
    results.append(await test_scryfall())

    # Test 2: Rules Parser (might take a while)
    print("\n⚠️  Note: PDF parsing may take 1-2 minutes...")
    results.append(await test_rules_parser())

    # Test 3: Stack Visualizer
    results.append(await test_stack_visualization())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("\nNext steps:")
        print("  1. Set up your ANTHROPIC_API_KEY in .env file")
        print("  2. Install remaining dependencies: pip3 install langchain chromadb sentence-transformers")
        print("  3. Run the full example: python3 example.py")
        print("  4. Start the API server: python3 main.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
