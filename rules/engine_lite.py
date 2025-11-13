"""
Lightweight Rules Engine for Vercel
Uses simple text search instead of vector embeddings to reduce dependencies
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import anthropic


class RulesEngineLite:
    """
    Lightweight rules engine using simple text search
    No ChromaDB or sentence-transformers needed
    """

    def __init__(self):
        """Initialize lightweight rules engine"""
        self.rules_data = None

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = anthropic.Anthropic(api_key=api_key)

        # Load pre-processed rules
        self._load_preprocessed()

    def _load_preprocessed(self):
        """Load rules from pre-processed JSON"""
        rules_dir = Path(__file__).parent

        # Load rules data from JSON
        rules_json_path = rules_dir / "rules_data.json"
        print(f"Loading rules from {rules_json_path}...")

        if not rules_json_path.exists():
            raise FileNotFoundError(
                f"Pre-processed rules not found at {rules_json_path}. "
                "Run 'python preprocess_rules.py' first!"
            )

        with open(rules_json_path, "r", encoding="utf-8") as f:
            self.rules_data = json.load(f)

        print(f"✓ Loaded {len(self.rules_data['rules'])} rules")
        print(f"✓ Loaded {len(self.rules_data['glossary'])} glossary terms")

    def search_relevant_rules(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for relevant rules using simple text matching

        Args:
            query: Query string
            k: Number of results to return

        Returns:
            List of relevant rules
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Score each rule based on keyword matches
        scored_results = []

        # Search in rules
        for rule in self.rules_data["rules"]:
            rule_text_lower = rule["text"].lower()
            rule_words = set(rule_text_lower.split())

            # Calculate relevance score
            score = 0

            # Exact phrase match (highest score)
            if query_lower in rule_text_lower:
                score += 100

            # Word overlap
            common_words = query_words & rule_words
            score += len(common_words) * 10

            # Bonus for rule number match (if query contains numbers)
            if any(char.isdigit() for char in query):
                if rule["number"] in query:
                    score += 50

            if score > 0:
                scored_results.append({
                    "content": f"Rule {rule['number']}: {rule['text']}",
                    "metadata": {
                        "rule_number": rule["number"],
                        "section": rule["section"]
                    },
                    "score": score
                })

        # Search in glossary
        for term, entry in self.rules_data["glossary"].items():
            entry_text_lower = entry["definition"].lower()
            entry_words = set(entry_text_lower.split())

            score = 0

            # Exact term match
            if query_lower in term or term in query_lower:
                score += 150

            # Phrase match in definition
            if query_lower in entry_text_lower:
                score += 80

            # Word overlap
            common_words = query_words & entry_words
            score += len(common_words) * 8

            if score > 0:
                scored_results.append({
                    "content": f"Glossary - {entry['term']}: {entry['definition']}",
                    "metadata": {
                        "type": "glossary",
                        "term": entry["term"]
                    },
                    "score": score
                })

        # Sort by score and return top k
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        return scored_results[:k]

    async def answer_question(
        self,
        question: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Answer a question about MTG rules using Claude AI

        Args:
            question: User's question
            context: Optional context (card data, game state, etc.)

        Returns:
            Answer with explanation and rule references
        """

        # Search for relevant rules
        relevant_rules = self.search_relevant_rules(question, k=8)

        # Build context for Claude
        rules_context = "\n\n".join([
            f"{r['content']}"
            for r in relevant_rules
        ])

        # Build prompt
        system_prompt = """You are Tolaria, an expert MTG judge and rules advisor.
Your role is to provide clear, accurate explanations of Magic: The Gathering rules and card interactions.

When answering questions:
1. Cite specific rule numbers when applicable
2. Explain the reasoning step-by-step
3. Use clear, accessible language
4. Address common misconceptions if relevant
5. Consider the stack order and priority carefully

Always be precise and refer to the official comprehensive rules provided."""

        user_prompt = f"""Question: {question}

Relevant Rules:
{rules_context}
"""

        if context:
            user_prompt += f"\n\nAdditional Context:\n{context}"

        user_prompt += """

Please provide a detailed answer that:
1. Directly answers the question
2. References specific rules by number
3. Explains the reasoning step-by-step
4. Addresses how this would play out in a game

Format your response as JSON with these fields:
- answer: The main explanation
- rule_references: List of rule numbers referenced
- step_by_step: List of steps if explaining a sequence of events
- summary: Brief one-sentence summary
"""

        # Call Claude
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        # Parse response
        response_text = message.content[0].text

        # Try to extract JSON, otherwise return as plain text
        try:
            import json
            # Try to find JSON in response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                result = json.loads(response_text[json_start:json_end])
            else:
                # Fallback: structure the response
                result = {
                    "answer": response_text,
                    "rule_references": [r["metadata"].get("rule_number", "")
                                       for r in relevant_rules
                                       if "rule_number" in r["metadata"]],
                    "step_by_step": [],
                    "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text
                }

        except Exception:
            # Fallback to plain text response
            result = {
                "answer": response_text,
                "rule_references": [],
                "step_by_step": [],
                "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text
            }

        return result

    def get_stack_resolution_rules(self) -> List[Dict]:
        """
        Get all rules relevant to stack resolution

        Returns:
            List of stack resolution rules
        """
        # Stack rules are in section 405
        stack_rules = []

        for rule in self.rules_data["rules"]:
            if rule["number"].startswith("405") or "stack" in rule["text"].lower():
                stack_rules.append(rule)

        return stack_rules
