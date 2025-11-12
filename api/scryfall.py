"""
Scryfall API Client
Handles all interactions with the Scryfall API for MTG card data
"""

import requests
import asyncio
from typing import Dict, List, Optional
from urllib.parse import quote


class ScryfallClient:
    """Client for interacting with Scryfall API"""

    BASE_URL = "https://api.scryfall.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Tolaria/1.0"
        })

    async def search_card(self, card_name: str, exact: bool = False) -> Dict:
        """
        Search for a card by name

        Args:
            card_name: Name of the card to search
            exact: If True, search for exact match

        Returns:
            Card data including image URIs, oracle text, etc.
        """
        try:
            if exact:
                url = f"{self.BASE_URL}/cards/named?exact={quote(card_name)}"
            else:
                url = f"{self.BASE_URL}/cards/named?fuzzy={quote(card_name)}"

            # Respect Scryfall rate limits (50-100ms between requests)
            await asyncio.sleep(0.1)

            response = self.session.get(url)
            response.raise_for_status()

            card_data = response.json()

            return self._format_card_data(card_data)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Card '{card_name}' not found")
            raise

    async def search_cards_bulk(self, card_names: List[str]) -> List[Dict]:
        """
        Search for multiple cards

        Args:
            card_names: List of card names to search

        Returns:
            List of card data
        """
        cards = []
        for card_name in card_names:
            try:
                card_data = await self.search_card(card_name, exact=False)
                cards.append(card_data)
            except ValueError as e:
                # Card not found, add placeholder
                cards.append({
                    "name": card_name,
                    "error": str(e),
                    "found": False
                })

        return cards

    def _format_card_data(self, raw_data: Dict) -> Dict:
        """
        Format Scryfall card data to our internal format

        Args:
            raw_data: Raw response from Scryfall API

        Returns:
            Formatted card data
        """
        # Extract relevant fields
        formatted = {
            "name": raw_data.get("name"),
            "mana_cost": raw_data.get("mana_cost", ""),
            "cmc": raw_data.get("cmc", 0),
            "type_line": raw_data.get("type_line", ""),
            "oracle_text": raw_data.get("oracle_text", ""),
            "colors": raw_data.get("colors", []),
            "color_identity": raw_data.get("color_identity", []),
            "legalities": raw_data.get("legalities", {}),
            "found": True
        }

        # Get image URIs
        if "image_uris" in raw_data:
            formatted["image_uris"] = {
                "small": raw_data["image_uris"].get("small"),
                "normal": raw_data["image_uris"].get("normal"),
                "large": raw_data["image_uris"].get("large"),
                "png": raw_data["image_uris"].get("png"),
                "art_crop": raw_data["image_uris"].get("art_crop"),
                "border_crop": raw_data["image_uris"].get("border_crop"),
            }
        elif "card_faces" in raw_data:
            # Handle double-faced cards
            formatted["card_faces"] = []
            for face in raw_data["card_faces"]:
                face_data = {
                    "name": face.get("name"),
                    "mana_cost": face.get("mana_cost", ""),
                    "type_line": face.get("type_line", ""),
                    "oracle_text": face.get("oracle_text", ""),
                }
                if "image_uris" in face:
                    face_data["image_uris"] = {
                        "small": face["image_uris"].get("small"),
                        "normal": face["image_uris"].get("normal"),
                        "large": face["image_uris"].get("large"),
                        "png": face["image_uris"].get("png"),
                    }
                formatted["card_faces"].append(face_data)

        # Additional metadata
        formatted["scryfall_uri"] = raw_data.get("scryfall_uri")
        formatted["rulings_uri"] = raw_data.get("rulings_uri")

        # Power/Toughness for creatures
        if "power" in raw_data:
            formatted["power"] = raw_data["power"]
            formatted["toughness"] = raw_data["toughness"]

        # Loyalty for planeswalkers
        if "loyalty" in raw_data:
            formatted["loyalty"] = raw_data["loyalty"]

        return formatted

    async def get_card_rulings(self, card_name: str) -> List[Dict]:
        """
        Get official rulings for a card

        Args:
            card_name: Name of the card

        Returns:
            List of rulings with dates and text
        """
        try:
            # First get the card to find rulings URI
            card_data = await self.search_card(card_name, exact=False)

            if "rulings_uri" not in card_data:
                return []

            # Respect rate limits
            await asyncio.sleep(0.1)

            response = self.session.get(card_data["rulings_uri"])
            response.raise_for_status()

            rulings_data = response.json()

            return rulings_data.get("data", [])

        except Exception:
            return []

    def get_card_types(self, card_data: Dict) -> Dict[str, bool]:
        """
        Parse card types from type line

        Args:
            card_data: Card data with type_line

        Returns:
            Dictionary of card type booleans
        """
        type_line = card_data.get("type_line", "").lower()

        return {
            "is_creature": "creature" in type_line,
            "is_instant": "instant" in type_line,
            "is_sorcery": "sorcery" in type_line,
            "is_enchantment": "enchantment" in type_line,
            "is_artifact": "artifact" in type_line,
            "is_planeswalker": "planeswalker" in type_line,
            "is_land": "land" in type_line,
            "is_tribal": "tribal" in type_line,
        }
