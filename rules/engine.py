"""
Rules Engine
Uses Claude AI and vector database for intelligent rule retrieval and reasoning
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import anthropic
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document


class RulesEngine:
    """
    Intelligent rules engine using RAG (Retrieval Augmented Generation)
    for answering MTG rules questions
    """

    def __init__(self, use_preprocessed: bool = True):
        """
        Initialize rules engine

        Args:
            use_preprocessed: Load from pre-processed files (default: True)
        """
        self.use_preprocessed = use_preprocessed
        self.rules_data = None
        self.vector_store = None

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = anthropic.Anthropic(api_key=api_key)

        # Initialize engine
        self._initialize()

    def _initialize(self):
        """Initialize the rules engine - load from pre-processed files"""
        print("Initializing Rules Engine...")

        if self.use_preprocessed:
            # Load from pre-processed files (fast!)
            self._load_preprocessed()
        else:
            # Fallback: parse PDF (slow, for development only)
            print("WARNING: Parsing PDF - this is slow! Use pre-processed files in production.")
            from rules.parser import RulesParser
            self.parser = RulesParser("mtgrules.pdf")
            self.rules_data = self.parser.parse_pdf()
            self._create_vector_store()

        print("Rules Engine initialized!")

    def _load_preprocessed(self):
        """Load rules from pre-processed JSON and vector store"""
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

        # Load vector store
        vector_store_path = rules_dir / "chroma_db"
        print(f"Loading vector store from {vector_store_path}...")

        if not vector_store_path.exists():
            raise FileNotFoundError(
                f"Vector store not found at {vector_store_path}. "
                "Run 'python preprocess_rules.py' first!"
            )

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vector_store = Chroma(
            persist_directory=str(vector_store_path),
            embedding_function=embeddings
        )

        print("✓ Vector store loaded")

    def _create_vector_store(self):
        """Create a vector store from parsed rules for semantic search"""

        # Create documents from rules
        documents = []

        for rule in self.rules_data["rules"]:
            doc_text = f"Rule {rule['number']}: {rule['text']}"
            metadata = {
                "rule_number": rule["number"],
                "section": rule["section"]
            }

            doc = Document(page_content=doc_text, metadata=metadata)
            documents.append(doc)

        # Add glossary terms
        for term, entry in self.rules_data["glossary"].items():
            doc_text = f"Glossary - {entry['term']}: {entry['definition']}"
            metadata = {
                "type": "glossary",
                "term": entry["term"]
            }

            doc = Document(page_content=doc_text, metadata=metadata)
            documents.append(doc)

        # Split documents if needed
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        split_docs = text_splitter.split_documents(documents)

        # Create embeddings and vector store
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vector_store = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings,
            persist_directory="chroma_db"
        )

        print(f"Vector store created with {len(split_docs)} document chunks")

    def search_relevant_rules(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for relevant rules using semantic search

        Args:
            query: Query string
            k: Number of results to return

        Returns:
            List of relevant rules
        """
        if not self.vector_store:
            return []

        # Perform semantic search
        results = self.vector_store.similarity_search(query, k=k)

        # Format results
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })

        return formatted_results

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
