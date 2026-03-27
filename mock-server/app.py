import json
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# Load customers from JSON file (not hardcoded)
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "customers.json")

def load_customers():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data["customers"]


# GET /api/health - Health check endpoint
@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


# GET /api/customers - Return paginated list of customers
@app.route("/api/customers")
def get_customers():
    customers = load_customers()

    # Read pagination params from query string (default: page=1, limit=10)
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))

    # Basic validation
    if page < 1:
        page = 1
    if limit < 1:
        limit = 10

    total = len(customers)

    # Calculate slice start and end
    start = (page - 1) * limit
    end = start + limit

    paginated = customers[start:end]

    return jsonify({
        "data": paginated,
        "total": total,
        "page": page,
        "limit": limit
    })


# GET /api/customers/<id> - Return a single customer by customer_id
@app.route("/api/customers/<customer_id>")
def get_customer(customer_id):
    customers = load_customers()

    # Search for customer by ID
    for customer in customers:
        if customer["customer_id"] == customer_id:
            return jsonify(customer)

    # Customer not found
    return jsonify({"error": "Customer not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
