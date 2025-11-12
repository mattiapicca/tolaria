"""
Stack Visualizer
Creates visual representations of the stack using card images
"""

from typing import List, Dict
import base64
import requests
from io import BytesIO


class StackVisualizer:
    """
    Creates visual representations of the MTG stack
    """

    def __init__(self):
        self.card_spacing = 20  # pixels between cards

    def generate_stack_html(
        self,
        stack: List[Dict],
        current_step: int = 0
    ) -> str:
        """
        Generate HTML representation of the stack

        Args:
            stack: Stack items with card data
            current_step: Current resolution step (0 = unresolved)

        Returns:
            HTML string for rendering
        """
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }

                .stack-container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 16px;
                    padding: 30px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }

                h1 {
                    text-align: center;
                    color: #1e3c72;
                    margin-bottom: 10px;
                }

                .subtitle {
                    text-align: center;
                    color: #666;
                    margin-bottom: 30px;
                    font-style: italic;
                }

                .stack {
                    display: flex;
                    justify-content: center;
                    align-items: flex-start;
                    margin: 50px 0;
                    position: relative;
                    min-height: 400px;
                }

                .stack-label {
                    position: absolute;
                    left: 20px;
                    top: -40px;
                    font-weight: bold;
                    color: #1e3c72;
                    font-size: 24px;
                    letter-spacing: 2px;
                }

                .cards-wrapper {
                    position: relative;
                    width: 280px;
                    height: 390px;
                }

                .stack-item {
                    position: absolute;
                    transition: all 0.3s ease;
                    cursor: pointer;
                }

                .stack-item.resolved {
                    opacity: 0.3;
                    filter: grayscale(100%);
                }

                .stack-item.resolving {
                    box-shadow: 0 0 40px rgba(255, 215, 0, 0.9);
                    z-index: 1000 !important;
                }

                .card-wrapper {
                    position: relative;
                    display: inline-block;
                }

                .card-image {
                    width: 250px;
                    height: auto;
                    border-radius: 12px;
                    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
                    transition: all 0.3s ease;
                    border: 3px solid rgba(255, 255, 255, 0.8);
                }

                .stack-item:hover {
                    transform: translateY(-20px) scale(1.05);
                    z-index: 999 !important;
                }

                .stack-item:hover .card-image {
                    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.6);
                }

                .position-badge {
                    position: absolute;
                    top: -15px;
                    right: -15px;
                    background: linear-gradient(135deg, #ff4757 0%, #e84545 100%);
                    color: white;
                    border-radius: 50%;
                    width: 45px;
                    height: 45px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 20px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                    border: 3px solid white;
                    z-index: 10;
                }

                .top-label {
                    position: absolute;
                    top: -25px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #ff4757;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 12px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                }

                .controller-label {
                    position: absolute;
                    bottom: -35px;
                    left: 0;
                    right: 0;
                    text-align: center;
                    font-weight: 700;
                    color: #2a5298;
                    font-size: 14px;
                    background: rgba(255, 255, 255, 0.9);
                    padding: 5px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }

                .resolution-order {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-top: 30px;
                }

                .resolution-order h2 {
                    color: #1e3c72;
                    margin-top: 0;
                }

                .resolution-order ol {
                    margin: 0;
                    padding-left: 25px;
                }

                .resolution-order li {
                    margin: 10px 0;
                    padding: 10px;
                    background: white;
                    border-radius: 6px;
                    border-left: 4px solid #2a5298;
                }

                .resolution-order li.done {
                    background: #d4edda;
                    border-left-color: #28a745;
                    opacity: 0.7;
                }

                .resolution-order li.current {
                    background: #fff3cd;
                    border-left-color: #ffc107;
                    font-weight: bold;
                }

                .info-box {
                    background: #e7f3ff;
                    border-left: 4px solid #2196F3;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }

                .info-box strong {
                    color: #1976D2;
                }
            </style>
        </head>
        <body>
            <div class="stack-container">
                <h1>The Stack</h1>
                <div class="subtitle">Spells and abilities resolve from top to bottom (Last In, First Out)</div>

                <div class="info-box">
                    <strong>How the Stack Works:</strong> In Magic: The Gathering, spells and abilities go on the stack.
                    The last spell or ability put on the stack is the first to resolve (LIFO).
                    Players can respond to items on the stack by adding more spells or abilities.
                </div>

                <div class="stack">
                    <div class="stack-label">STACK</div>
                    <div class="cards-wrapper">
        """

        # Calculate offset for overlapping cards
        # Cards are shown with the LAST played (top of stack) fully visible
        overlap_offset = 80  # pixels offset between cards

        # Add cards to stack - REVERSE order so last played is on top visually
        for idx, item in enumerate(reversed(stack)):
            card = item["card"]
            actual_position = len(stack) - idx  # Position in stack (higher = top)

            # Calculate positioning
            # Last card played (top of stack) should be most visible
            z_index = len(stack) - idx  # Higher z-index for cards on top
            top_offset = idx * overlap_offset  # Offset from top

            # Determine state class
            state_class = ""
            if current_step > 0:
                if actual_position > (len(stack) - current_step):
                    state_class = "resolved"
                elif actual_position == (len(stack) - current_step + 1):
                    state_class = "resolving"

            # Get card image URL
            image_url = self._get_card_image_url(card)

            # Add "TOP" label for the first card (last played)
            top_label = '<div class="top-label">TOP OF STACK</div>' if idx == 0 else ''

            html += f"""
                    <div class="stack-item {state_class}" style="top: {top_offset}px; z-index: {z_index};">
                        <div class="card-wrapper">
                            {top_label}
                            <img src="{image_url}" alt="{card['name']}" class="card-image">
                            <div class="position-badge">{actual_position}</div>
                            <div class="controller-label">{item['controller']}: {card['name']}</div>
                        </div>
                    </div>
            """

        html += """
                    </div>
                </div>

                <div class="resolution-order">
                    <h2>Sequenza di Gioco e Risoluzione</h2>
                    <ol>
        """

        # Add play order FIRST (bottom to top of stack)
        html += "<h3 style='color: #1e3c72; margin-top: 20px;'>Ordine di Gioco:</h3>"
        for idx, item in enumerate(stack):
            card = item["card"]
            targets = f" (target: {', '.join(item['targets'])})" if item.get('targets') else ""
            html += f"""
                        <li style="background: #e3f2fd; border-left-color: #2196F3;">
                            <strong>{item['controller']}</strong> gioca <strong>{card['name']}</strong>{targets}
                            <br><small style="color: #666;">{card.get('oracle_text', '')[:80]}...</small>
                        </li>
            """

        # Then show RESOLUTION order (top to bottom of stack)
        html += "<h3 style='color: #1e3c72; margin-top: 20px;'>Ordine di Risoluzione (LIFO):</h3>"

        # Analyze the stack to determine what gets countered
        countered_spells = set()

        for idx, item in enumerate(reversed(stack), 1):
            card = item["card"]
            oracle_text = card.get('oracle_text', '').lower()

            # Check if this is a counterspell
            if 'counter target' in oracle_text:
                # Find what it targets from the targets list
                targets = item.get('targets', [])
                countered_spells.update(targets)

            step_class = ""
            if current_step > 0:
                if idx < current_step:
                    step_class = "done"
                elif idx == current_step:
                    step_class = "current"

            # Check if this spell gets countered
            is_countered = card['name'] in countered_spells

            if is_countered:
                html += f"""
                        <li class="{step_class}" style="background: #ffebee; border-left-color: #f44336;">
                            <strong>{card['name']}</strong> viene counterato e non risolve
                            <br><small style="color: #666;">❌ Questo spell è stato counterato e va al cimitero senza risolvere</small>
                        </li>
            """
            else:
                effect = card.get('oracle_text', '')[:80]
                html += f"""
                        <li class="{step_class}">
                            <strong>{card['name']}</strong> risolve
                            <br><small style="color: #666;">✓ Effetto: {effect}...</small>
                        </li>
            """

        html += """
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _get_card_image_url(self, card: Dict) -> str:
        """
        Get card image URL from card data

        Args:
            card: Card data from Scryfall

        Returns:
            Image URL
        """
        # Try to get normal image
        if "image_uris" in card:
            return card["image_uris"].get("normal") or card["image_uris"].get("large")

        # Handle double-faced cards
        if "card_faces" in card and len(card["card_faces"]) > 0:
            face = card["card_faces"][0]
            if "image_uris" in face:
                return face["image_uris"].get("normal") or face["image_uris"].get("large")

        # Fallback to placeholder
        return "https://via.placeholder.com/250x350?text=Card+Image"

    def generate_step_visualization(
        self,
        stack: List[Dict],
        step_number: int,
        step_data: Dict
    ) -> str:
        """
        Generate visualization for a specific resolution step

        Args:
            stack: Full stack
            step_number: Current step number
            step_data: Data for current step

        Returns:
            HTML string
        """
        html = self.generate_stack_html(stack, step_number)

        # Add step description
        step_description = f"""
        <div style="margin-top: 20px; padding: 20px; background: #fff3cd; border-radius: 8px;">
            <h3 style="margin-top: 0; color: #856404;">Step {step_number}</h3>
            <p><strong>{step_data['action']}</strong></p>
            <p>{step_data['description']}</p>
            <p style="margin-bottom: 0;"><em>{step_data['state_after']}</em></p>
        </div>
        """

        # Insert before closing div
        html = html.replace(
            "</div>\n        </body>",
            f"{step_description}</div>\n        </body>"
        )

        return html
