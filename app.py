
from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Initialize OpenAI client
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    # Do not raise at import time; allow app to start and return a clear error on API calls
    client = None
    print("Warning: OPENAI_API_KEY not set. /api/rent will return an error until it's configured.")
else:
    client = OpenAI(api_key=api_key)
    

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/rent", methods=["POST"])
def estimate_rent():
    data = request.json
    address = data.get("address", "")

    if not address:
        return jsonify({"error": "Address is required"}), 400

    # Ensure OpenAI client is configured
    if client is None:
        return jsonify({"error": "Server misconfiguration: OPENAI_API_KEY not set."}), 500

    # GPT-5.1 request (web-enabled search)
    response = client.responses.create(
        model="gpt-5.1",
        input=f"""
        Search the web and give me the rent price and the square meters 
        for an apartment nearby this address. I want the price in soles (PEN):
        {address}

        Respond in this exact format:
        PRICE: [PEN amount]
        SIZE: [square meters]
        """,
    )

    result_text = response.output_text.strip()
    
    # Parse the response
    price = "N/A"
    size = "N/A"
    price_per_sqm = "N/A"
    
    for line in result_text.split('\n'):
        if line.startswith('PRICE:'):
            price = line.replace('PRICE:', '').strip()
        elif line.startswith('SIZE:'):
            size = line.replace('SIZE:', '').strip()
    
    # Calculate price per square meter
    try:
        # Extract numeric values
        price_value = float(''.join(filter(lambda x: x.isdigit() or x == '.', price)))
        size_value = float(''.join(filter(lambda x: x.isdigit() or x == '.', size)))
        
        if size_value > 0:
            price_per_sqm = f"{price_value / size_value:.2f}"
    except (ValueError, ZeroDivisionError):
        price_per_sqm = "N/A"
    
    return jsonify({
        "estimated_price": price, 
        "average_size": size,
        "price_per_sqm": price_per_sqm
    })



@app.route("/results")
def results_page():
    return render_template("results.html")


if __name__ == "__main__":
    app.run(debug=True)