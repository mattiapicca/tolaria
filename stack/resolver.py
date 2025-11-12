"""
Stack Resolver
Handles the logic for resolving the MTG stack and explaining interactions
"""

from typing import List, Dict, Optional
from api.scryfall import ScryfallClient
from rules.engine import RulesEngine


class StackResolver:
    """
    Resolves stack interactions and provides step-by-step explanations
    """

    def __init__(self, scryfall_client: ScryfallClient, rules_engine: RulesEngine):
        """
        Initialize stack resolver

        Args:
            scryfall_client: Scryfall API client for card data
            rules_engine: Rules engine for rule lookups
        """
        self.scryfall = scryfall_client
        self.rules = rules_engine

    async def resolve_interaction(
        self,
        question: str,
        card_names: List[str],
        player_actions: Optional[List[dict]] = None
    ) -> Dict:
        """
        Resolve a stack interaction and provide explanation

        Args:
            question: User's question about the interaction
            card_names: List of card names involved
            player_actions: Optional list of player actions in sequence

        Returns:
            Complete resolution with visualization and explanation
        """

        # Step 1: Fetch card data from Scryfall
        cards = await self.scryfall.search_cards_bulk(card_names)

        # Step 2: Build the stack
        stack = await self._build_stack(cards, player_actions)

        # Step 3: Generate resolution steps
        resolution_steps = await self._generate_resolution_steps(stack, question)

        # Step 4: Get rule-based explanation
        explanation = await self._generate_explanation(
            question=question,
            cards=cards,
            stack=stack,
            resolution_steps=resolution_steps
        )

        # Step 5: Create response
        return {
            "stack_visualization": stack,
            "resolution_steps": resolution_steps,
            "explanation": explanation["answer"],
            "rules_references": explanation.get("rule_references", [])
        }

    async def _build_stack(
        self,
        cards: List[Dict],
        player_actions: Optional[List[dict]] = None
    ) -> List[Dict]:
        """
        Build the stack representation

        Args:
            cards: List of card data
            player_actions: Optional sequence of actions

        Returns:
            Stack representation (LIFO order)
        """
        stack = []

        if player_actions:
            # Build stack from explicit player actions
            for action in player_actions:
                card_name = action.get("card")
                card_data = next(
                    (c for c in cards if c.get("name") == card_name),
                    None
                )

                if card_data:
                    stack_item = {
                        "card": card_data,
                        "controller": action.get("player", "Player"),
                        "targets": action.get("targets", []),
                        "position": len(stack)
                    }
                    stack.append(stack_item)
        else:
            # Build stack from card list (assume order given)
            for idx, card in enumerate(cards):
                if not card.get("found", False):
                    continue

                stack_item = {
                    "card": card,
                    "controller": f"Player {idx % 2 + 1}",
                    "targets": [],
                    "position": idx
                }
                stack.append(stack_item)

        return stack

    async def _generate_resolution_steps(
        self,
        stack: List[Dict],
        question: str
    ) -> List[Dict]:
        """
        Generate step-by-step resolution of the stack

        Args:
            stack: Current stack state
            question: User's question for context

        Returns:
            List of resolution steps
        """
        steps = []

        # The stack resolves from top to bottom (LIFO - Last In First Out)
        # So we reverse the list to show resolution order
        resolution_order = list(reversed(stack))

        # Track what gets countered
        countered_spells = set()

        for idx, stack_item in enumerate(resolution_order, 1):
            card = stack_item["card"]
            card_types = self.scryfall.get_card_types(card)
            oracle_text = card.get('oracle_text', '').lower()

            # Check if this spell counters something
            if 'counter target' in oracle_text:
                targets = stack_item.get('targets', [])
                countered_spells.update(targets)

            # Check if THIS spell is being countered
            is_countered = card['name'] in countered_spells

            if is_countered:
                step = {
                    "step_number": idx,
                    "action": f"{card['name']} is countered",
                    "card": card,
                    "description": f"{card['name']} is countered and does not resolve. It goes to the graveyard without its effect taking place.",
                    "state_after": "This spell was countered and removed from the stack"
                }
            else:
                step = {
                    "step_number": idx,
                    "action": f"Resolve {card['name']}",
                    "card": card,
                    "description": self._generate_step_description(
                        stack_item,
                        card_types,
                        idx == len(resolution_order)
                    ),
                    "state_after": self._describe_state_after_step(
                        resolution_order,
                        idx
                    )
                }

            steps.append(step)

        return steps

    def _generate_step_description(
        self,
        stack_item: Dict,
        card_types: Dict,
        is_last: bool
    ) -> str:
        """
        Generate description for a resolution step

        Args:
            stack_item: Stack item being resolved
            card_types: Card type information
            is_last: Whether this is the last item on stack

        Returns:
            Description string
        """
        card = stack_item["card"]
        controller = stack_item["controller"]

        description = f"{controller} resolves {card['name']}. "

        # Add effect based on card type
        oracle_text = card.get("oracle_text", "")

        if oracle_text:
            # Simplify oracle text for display
            effect = oracle_text.split('.')[0] if '.' in oracle_text else oracle_text
            description += f"Effect: {effect}."

        # Add targeting info
        if stack_item.get("targets"):
            targets = ", ".join(stack_item["targets"])
            description += f" Targeting: {targets}."

        # Note if this resolves the stack
        if is_last:
            description += " The stack is now empty."

        return description

    def _describe_state_after_step(
        self,
        resolution_order: List[Dict],
        current_step: int
    ) -> str:
        """
        Describe the stack state after a step

        Args:
            resolution_order: Full resolution order
            current_step: Current step number (1-indexed)

        Returns:
            State description
        """
        remaining = resolution_order[current_step:]

        if not remaining:
            return "Stack is empty. Priority returns to active player."

        remaining_cards = [item["card"]["name"] for item in remaining]
        return f"Stack contains: {', '.join(remaining_cards)} (top to bottom)"

    async def _generate_explanation(
        self,
        question: str,
        cards: List[Dict],
        stack: List[Dict],
        resolution_steps: List[Dict]
    ) -> Dict:
        """
        Generate comprehensive explanation using rules engine

        Args:
            question: User's question
            cards: Card data
            stack: Stack representation
            resolution_steps: Resolution steps

        Returns:
            Explanation with rule references
        """

        # Build context for rules engine
        context = {
            "cards": [
                {
                    "name": c.get("name"),
                    "type": c.get("type_line"),
                    "text": c.get("oracle_text")
                }
                for c in cards if c.get("found")
            ],
            "stack_order": [
                item["card"]["name"]
                for item in stack
            ],
            "resolution_order": [
                step["card"]["name"]
                for step in resolution_steps
            ]
        }

        # Ask rules engine for explanation
        enhanced_question = f"""
{question}

The stack currently contains (bottom to top): {', '.join(context['stack_order'])}

How does this resolve according to the comprehensive rules?
Please explain:
1. The correct resolution order (LIFO)
2. Whether any spells/abilities counter each other
3. Any relevant priority or timing considerations
4. The final game state after full resolution
"""

        explanation = await self.rules.answer_question(
            question=enhanced_question,
            context=context
        )

        return explanation
