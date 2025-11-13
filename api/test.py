"""
Minimal test endpoint to debug Vercel deployment
"""

from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
def test():
    try:
        # Test 1: Basic import
        import json
        result = {"step": 1, "status": "Basic imports OK"}

        # Test 2: Path operations
        from pathlib import Path
        current_dir = Path(__file__).parent
        result["step"] = 2
        result["current_dir"] = str(current_dir)

        # Test 3: Check if rules_data.json exists
        rules_path = current_dir.parent / "rules" / "rules_data.json"
        result["step"] = 3
        result["rules_path"] = str(rules_path)
        result["rules_exists"] = rules_path.exists()

        # Test 4: Try to load it
        if rules_path.exists():
            with open(rules_path, 'r') as f:
                data = json.load(f)
            result["step"] = 4
            result["rules_count"] = len(data.get("rules", []))

        return result

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

handler = app
