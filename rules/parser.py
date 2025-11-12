"""
MTG Rules PDF Parser
Extracts and indexes rules from the official MTG Comprehensive Rules PDF
"""

import pdfplumber
import re
from typing import List, Dict, Optional
from pathlib import Path


class RulesParser:
    """Parser for MTG Comprehensive Rules PDF"""

    def __init__(self, pdf_path: str):
        """
        Initialize parser with PDF path

        Args:
            pdf_path: Path to the mtgrules.pdf file
        """
        self.pdf_path = Path(pdf_path)
        self.rules = []
        self.rules_dict = {}
        self.glossary = {}

    def parse_pdf(self) -> Dict:
        """
        Parse the entire PDF and extract rules

        Returns:
            Dictionary with parsed rules organized by section
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found at {self.pdf_path}")

        with pdfplumber.open(self.pdf_path) as pdf:
            full_text = ""

            print(f"Parsing {len(pdf.pages)} pages...")

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

                # Progress indicator every 50 pages
                if page_num % 50 == 0:
                    print(f"Processed {page_num} pages...")

        # Parse rules from full text
        self._extract_rules(full_text)
        self._extract_glossary(full_text)

        print(f"Extracted {len(self.rules)} rules")
        print(f"Extracted {len(self.glossary)} glossary terms")

        return {
            "rules": self.rules,
            "rules_dict": self.rules_dict,
            "glossary": self.glossary
        }

    def _extract_rules(self, text: str):
        """
        Extract individual rules from text

        Args:
            text: Full text of the PDF
        """
        # Pattern for rule numbers: 100.1, 100.1a, etc.
        rule_pattern = r'^(\d{3}\.\d+[a-z]?)\s+(.+?)(?=^\d{3}\.\d+[a-z]?|\Z)'

        # Find all rules
        matches = re.finditer(rule_pattern, text, re.MULTILINE | re.DOTALL)

        for match in matches:
            rule_number = match.group(1)
            rule_text = match.group(2).strip()

            # Clean up the text
            rule_text = re.sub(r'\s+', ' ', rule_text)

            rule_entry = {
                "number": rule_number,
                "text": rule_text,
                "section": self._get_section(rule_number)
            }

            self.rules.append(rule_entry)
            self.rules_dict[rule_number] = rule_entry

    def _extract_glossary(self, text: str):
        """
        Extract glossary terms

        Args:
            text: Full text of the PDF
        """
        # Find glossary section
        glossary_match = re.search(
            r'Glossary\s*\n(.+?)(?=Credits|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )

        if not glossary_match:
            return

        glossary_text = glossary_match.group(1)

        # Extract terms (terms are usually in bold or at start of line)
        # This is a simplified pattern - may need adjustment
        term_pattern = r'^([A-Z][A-Za-z\s,\-\']+)\s*\n(.+?)(?=^[A-Z][A-Za-z\s,\-\']+\s*\n|\Z)'

        matches = re.finditer(term_pattern, glossary_text, re.MULTILINE | re.DOTALL)

        for match in matches:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            definition = re.sub(r'\s+', ' ', definition)

            self.glossary[term.lower()] = {
                "term": term,
                "definition": definition
            }

    def _get_section(self, rule_number: str) -> str:
        """
        Get section name from rule number

        Args:
            rule_number: Rule number like "100.1"

        Returns:
            Section name
        """
        section_map = {
            "1": "Game Concepts",
            "2": "Parts of a Card",
            "3": "Card Types",
            "4": "Zones",
            "5": "Turn Structure",
            "6": "Spells, Abilities, and Effects",
            "7": "Additional Rules",
            "8": "Multiplayer Rules",
            "9": "Casual Variants"
        }

        section_num = rule_number[0]
        return section_map.get(section_num, "Unknown")

    def search_rules(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search rules by keyword

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching rules
        """
        query_lower = query.lower()
        results = []

        for rule in self.rules:
            if query_lower in rule["text"].lower():
                results.append(rule)

                if len(results) >= limit:
                    break

        return results

    def get_rule(self, rule_number: str) -> Optional[Dict]:
        """
        Get a specific rule by number

        Args:
            rule_number: Rule number like "100.1"

        Returns:
            Rule dictionary or None
        """
        return self.rules_dict.get(rule_number)

    def search_glossary(self, term: str) -> Optional[Dict]:
        """
        Search glossary for a term

        Args:
            term: Term to search for

        Returns:
            Glossary entry or None
        """
        return self.glossary.get(term.lower())

    def get_stack_rules(self) -> List[Dict]:
        """
        Get all rules related to the stack

        Returns:
            List of stack-related rules
        """
        # Stack rules are in section 405
        stack_rules = []

        for rule in self.rules:
            if rule["number"].startswith("405") or "stack" in rule["text"].lower():
                stack_rules.append(rule)

        return stack_rules
