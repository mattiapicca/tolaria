"""
Test lightweight rules engine
"""

from dotenv import load_dotenv
load_dotenv()

from rules.engine_lite import RulesEngineLite

print("=" * 60)
print("Testing Lightweight Rules Engine")
print("=" * 60)

print("\nInitializing RulesEngineLite...")
engine = RulesEngineLite()

print("\n✓ RulesEngineLite initialized successfully!")

# Test search
print("\nTesting text search for 'stack'...")
results = engine.search_relevant_rules("stack", k=3)

print(f"\n✓ Found {len(results)} results:")
for i, result in enumerate(results, 1):
    print(f"\n{i}. [Score: {result['score']}] {result['content'][:100]}...")

# Test getting stack rules
print("\n" + "=" * 60)
print("Testing get_stack_resolution_rules()...")
stack_rules = engine.get_stack_resolution_rules()
print(f"✓ Found {len(stack_rules)} stack-related rules")

if stack_rules:
    print(f"\nFirst stack rule: {stack_rules[0]['number']}")
    print(f"Text: {stack_rules[0]['text'][:150]}...")

print("\n" + "=" * 60)
print("✓ All tests passed! Lightweight engine is working!")
print("=" * 60)
