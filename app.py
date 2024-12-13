from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)

# Spoonacular API configuration
API_KEY = "07d674f8503a4b8dbafe1c9a6838f770"  # Replace with your API key
BASE_URL = "https://api.spoonacular.com/recipes/findByIngredients"
RECIPE_URL = "https://api.spoonacular.com/recipes/{}/information"  # For detailed recipe info

# Retry function for handling API calls
def fetch_with_retry(url, params, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retrying
            else:
                raise

@app.route("/generate", methods=["POST"])
def generate_recipes():
    data = request.json
    ingredients = data.get("ingredients", "")
    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400

    try:
        print(f"Ingredients received: {ingredients}")
        # Fetch basic recipe info
        response = fetch_with_retry(
            BASE_URL,
            params={"ingredients": ingredients, "number": 3, "apiKey": API_KEY},
        )
        recipes = response.json()

        detailed_recipes = []
        for recipe in recipes:
            recipe_id = recipe["id"]
            print(f"Fetching details for Recipe ID: {recipe_id}")
            try:
                recipe_info_response = fetch_with_retry(
                    RECIPE_URL.format(recipe_id), params={"apiKey": API_KEY}
                )
                recipe_info = recipe_info_response.json()
                instructions = recipe_info.get("instructions", "No instructions available")
                if instructions and not instructions.startswith("<ol>"):
                    instructions = "<ol>" + "".join(
                        [f"<li>{step}</li>" for step in instructions.split("\n") if step]
                    ) + "</ol>"
                detailed_recipes.append({
                    "name": recipe_info["title"],
                    "image": recipe_info["image"],
                    "id": recipe_info["id"],
                    "ingredients": [
                        ingredient["name"] for ingredient in recipe_info["extendedIngredients"]
                    ],
                    "instructions": instructions,
                })
            except Exception as e:
                print(f"Skipping Recipe ID {recipe_id} due to error: {e}")
                continue

        return jsonify({"recipes": detailed_recipes})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

