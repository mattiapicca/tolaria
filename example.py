"""
Example usage of Tolaria
Demonstrates how to use the API to resolve stack interactions
"""

import asyncio
from api.scryfall import ScryfallClient
from rules.engine import RulesEngine
from stack.resolver import StackResolver
from stack.visualizer import StackVisualizer


async def example_counterspell_lightning_bolt():
    """
    Example: Counterspell targeting Lightning Bolt
    Classic stack interaction
    """
    print("=" * 60)
    print("Example: Counterspell vs Lightning Bolt")
    print("=" * 60)

    # Initialize components
    scryfall = ScryfallClient()
    rules = RulesEngine("mtgrules.pdf")
    resolver = StackResolver(scryfall, rules)
    visualizer = StackVisualizer()

    # Define the scenario
    question = "Player 1 casts Lightning Bolt targeting Player 2. Player 2 responds with Counterspell targeting Lightning Bolt. What happens?"

    card_names = ["Lightning Bolt", "Counterspell"]

    player_actions = [
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

    # Resolve the interaction
    print("\nResolving interaction...")
    result = await resolver.resolve_interaction(
        question=question,
        card_names=card_names,
        player_actions=player_actions
    )

    # Display results
    print("\n" + "=" * 60)
    print("EXPLANATION")
    print("=" * 60)
    print(result["explanation"])

    print("\n" + "=" * 60)
    print("RULE REFERENCES")
    print("=" * 60)
    for rule_ref in result["rules_references"]:
        print(f"  - {rule_ref}")

    print("\n" + "=" * 60)
    print("RESOLUTION STEPS")
    print("=" * 60)
    for step in result["resolution_steps"]:
        print(f"\nStep {step['step_number']}: {step['action']}")
        print(f"  {step['description']}")
        print(f"  → {step['state_after']}")

    # Generate HTML visualization
    print("\n" + "=" * 60)
    print("GENERATING VISUALIZATION")
    print("=" * 60)

    html = visualizer.generate_stack_html(result["stack_visualization"])

    # Save to file
    with open("stack_visualization.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✓ Visualization saved to stack_visualization.html")
    print("  Open this file in a browser to see the stack!")


async def example_multiple_responses():
    """
    Example: Multiple responses on the stack
    More complex interaction
    """
    print("\n\n" + "=" * 60)
    print("Example: Multiple Responses")
    print("=" * 60)

    scryfall = ScryfallClient()
    rules = RulesEngine("mtgrules.pdf")
    resolver = StackResolver(scryfall, rules)
    visualizer = StackVisualizer()

    question = """
    Player 1 casts Giant Growth on their creature.
    Player 2 responds with Lightning Bolt targeting that creature.
    Player 1 responds with another Giant Growth.
    What happens to the creature?
    """

    card_names = ["Giant Growth", "Lightning Bolt"]

    player_actions = [
        {
            "card": "Giant Growth",
            "player": "Player 1",
            "targets": ["Grizzly Bears"]
        },
        {
            "card": "Lightning Bolt",
            "player": "Player 2",
            "targets": ["Grizzly Bears"]
        },
        {
            "card": "Giant Growth",
            "player": "Player 1",
            "targets": ["Grizzly Bears"]
        }
    ]

    print("\nResolving interaction...")
    result = await resolver.resolve_interaction(
        question=question,
        card_names=card_names,
        player_actions=player_actions
    )

    print("\n" + "=" * 60)
    print("EXPLANATION")
    print("=" * 60)
    print(result["explanation"])

    print("\n" + "=" * 60)
    print("RESOLUTION STEPS")
    print("=" * 60)
    for step in result["resolution_steps"]:
        print(f"\nStep {step['step_number']}: {step['action']}")
        print(f"  {step['description']}")

    # Generate step-by-step visualizations
    print("\n" + "=" * 60)
    print("GENERATING STEP-BY-STEP VISUALIZATIONS")
    print("=" * 60)

    for idx, step in enumerate(result["resolution_steps"], 1):
        html = visualizer.generate_step_visualization(
            result["stack_visualization"],
            idx,
            step
        )

        filename = f"stack_step_{idx}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✓ Step {idx} saved to {filename}")


async def simple_card_search():
    """
    Simple example: Just search for cards
    """
    print("\n\n" + "=" * 60)
    print("Example: Card Search")
    print("=" * 60)

    scryfall = ScryfallClient()

    # Search for a card
    card = await scryfall.search_card("Black Lotus")

    print(f"\nCard: {card['name']}")
    print(f"Type: {card['type_line']}")
    print(f"Mana Cost: {card['mana_cost']}")
    print(f"Text: {card['oracle_text']}")

    # Get rulings
    rulings = await scryfall.get_card_rulings("Black Lotus")

    print(f"\nRulings ({len(rulings)}):")
    for ruling in rulings[:3]:  # Show first 3
        print(f"  - {ruling.get('comment', 'N/A')}")


async def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 18 + "TOLARIA EXAMPLES" + " " * 24 + "║")
    print("║" + " " * 12 + "MTG Rules & Stack AI Agent" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    # Run examples
    await simple_card_search()
    await example_counterspell_lightning_bolt()
    # await example_multiple_responses()  # Uncomment for more complex example

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
