"""
LATTE LAB - Square POS Integration Backend (Belize Cash-Only Edition)
=====================================================================
"""

import os
import uuid
import json
import requests
import traceback
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# ===================== CONFIG =====================
SQUARE_ENV = os.environ.get('SQUARE_ENV', 'sandbox')
SQUARE_ACCESS_TOKEN = os.environ.get('SQUARE_ACCESS_TOKEN', '')
SQUARE_LOCATION_ID = os.environ.get('SQUARE_LOCATION_ID', '')
SQUARE_CURRENCY = os.environ.get('SQUARE_CURRENCY', 'BZD')

BASE_URL = 'https://connect.squareupsandbox.com' if SQUARE_ENV == 'sandbox' else 'https://connect.squareup.com'
HEADERS = {
    'Square-Version': '2024-08-21',
    'Authorization': f'Bearer {SQUARE_ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

orders_db = {}

app = Flask(__name__)
CORS(app)


def square_post(endpoint, payload):
    url = f'{BASE_URL}{endpoint}'
    try:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=15)
        try:
            data = resp.json()
        except Exception:
            data = {"raw_response": resp.text}
        return data, resp.status_code
    except Exception as e:
        return {'errors': [{'detail': str(e)}]}, 500


def square_get(endpoint):
    url = f'{BASE_URL}{endpoint}'
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        try:
            data = resp.json()
        except Exception:
            data = {"raw_response": resp.text}
        return data, resp.status_code
    except Exception as e:
        return {'errors': [{'detail': str(e)}]}, 500


MENU_CATEGORIES = [
    {"id": "coffee", "name": "Coffee"},
    {"id": "smoothies", "name": "Smoothies / Slush"},
    {"id": "milktea", "name": "Milk Tea"},
    {"id": "matcha", "name": "Matcha"},
    {"id": "tea", "name": "Tea & Lemonade"},
]

MENU_ITEMS = [
    {"id": "americano", "category": "coffee", "name": "Americano", "price": 1000, "customizable": True},
    {"id": "latte", "category": "coffee", "name": "Latte", "price": 1100, "customizable": True},
    {"id": "cappuccino", "category": "coffee", "name": "Cappuccino", "price": 1300, "customizable": True},
    {"id": "espresso_double", "category": "coffee", "name": "Espresso (Double)", "price": 600, "customizable": True},
    {"id": "brown_sugar_shaken", "category": "coffee", "name": "Brown Sugar Shaken", "price": 1200, "customizable": True},
    {"id": "vietnamese_coffee", "category": "coffee", "name": "Vietnamese Coffee", "price": 1200, "customizable": True},
    {"id": "frappuccino", "category": "coffee", "name": "Frappuccino", "price": 1100, "customizable": True},
    {"id": "strawberry_banana_smoothie", "category": "smoothies", "name": "Strawberry Banana Smoothie", "price": 1200, "customizable": False},
    {"id": "mango_smoothie", "category": "smoothies", "name": "Mango Smoothie", "price": 1200, "customizable": False},
    {"id": "mango_dragonfruit_slush", "category": "smoothies", "name": "Mango DragonFruit Slush", "price": 1200, "customizable": False},
    {"id": "mango_passionfruit_slush", "category": "smoothies", "name": "Mango PassionFruit Slush", "price": 1200, "customizable": False},
    {"id": "passionfruit_slush", "category": "smoothies", "name": "PassionFruit Slush", "price": 1200, "customizable": False},
    {"id": "taro_smoothie", "category": "smoothies", "name": "Taro Smoothie", "price": 1200, "customizable": False},
    {"id": "watermelon_slush", "category": "smoothies", "name": "Watermelon Slush", "price": 1200, "customizable": False},
    {"id": "boba_milk_tea", "category": "milktea", "name": "Boba Milk Tea", "price": 1200, "customizable": True},
    {"id": "banana_milk_tea", "category": "milktea", "name": "Banana Milk Tea", "price": 1100, "customizable": True},
    {"id": "strawberry_milk_tea", "category": "milktea", "name": "Strawberry Milk Tea", "price": 1100, "customizable": True},
    {"id": "taro_milk_tea", "category": "milktea", "name": "Taro Milk Tea", "price": 1100, "customizable": True},
    {"id": "brown_sugar_milk_tea", "category": "milktea", "name": "Brown Sugar Milk Tea", "price": 1100, "customizable": True},
    {"id": "coffee_milk_tea", "category": "milktea", "name": "Coffee Milk Tea", "price": 1100, "customizable": True},
    {"id": "jasmine_milk_tea", "category": "milktea", "name": "Jasmine Milk Tea", "price": 1100, "customizable": True},
    {"id": "original_matcha", "category": "matcha", "name": "Original Matcha", "price": 1500, "customizable": True},
    {"id": "strawberry_matcha", "category": "matcha", "name": "Strawberry Matcha", "price": 1500, "customizable": True},
    {"id": "mango_matcha", "category": "matcha", "name": "Mango Matcha", "price": 1500, "customizable": True},
    {"id": "blueberry_matcha", "category": "matcha", "name": "Blueberry Matcha", "price": 1500, "customizable": True},
    {"id": "mango_berry_green_tea", "category": "tea", "name": "Mango Berry Green Tea", "price": 1000, "customizable": True},
    {"id": "strawberry_green_tea", "category": "tea", "name": "Strawberry Green Tea", "price": 1000, "customizable": True},
    {"id": "watermelon_green_tea", "category": "tea", "name": "Watermelon Green Tea", "price": 1000, "customizable": True},
    {"id": "pink_lemonade", "category": "tea", "name": "Pink Lemonade", "price": 1100, "customizable": False},
    {"id": "kiwi_lemonade", "category": "tea", "name": "Kiwi Lemonade", "price": 1100, "customizable": False},
    {"id": "passionfruit_soda", "category": "tea", "name": "PassionFruit Soda", "price": 1100, "customizable": False},
    {"id": "ice_tea", "category": "tea", "name": "Ice Tea", "price": 1100, "customizable": True},
    {"id": "honey_green_tea", "category": "tea", "name": "Honey Green Tea", "price": 1100, "customizable": True},
    {"id": "thai_tea", "category": "tea", "name": "Thai Tea", "price": 1100, "customizable": True},
]

MODIFIER_LISTS = {
    "syrups": {
        "name": "Syrups (+BZ$2)",
        "modifiers": [
            {"name": "Mocha", "price": 200},
            {"name": "White Chocolate", "price": 200},
            {"name": "Caramel", "price": 200},
            {"name": "Salted Caramel", "price": 200},
            {"name": "Hazelnut", "price": 200},
            {"name": "Vanilla", "price": 200},
        ]
    },
    "cold_foam": {
        "name": "Cold Foam (+BZ$2)",
        "modifiers": [
            {"name": "Vanilla Cold Foam", "price": 200},
            {"name": "Salted Caramel Cold Foam", "price": 200},
            {"name": "Taro Cold Foam", "price": 200},
            {"name": "Matcha Cold Foam", "price": 200},
            {"name": "Tiramisu Cold Foam", "price": 200},
        ]
    },
    "milk": {
        "name": "Milk Alternative (+BZ$2)",
        "modifiers": [
            {"name": "Almond Milk", "price": 200},
            {"name": "Oat Milk", "price": 200},
            {"name": "Soy Milk", "price": 200},
        ]
    },
    "toppings": {
        "name": "Toppings (+BZ$2)",
        "modifiers": [
            {"name": "Boba Pearls", "price": 200},
            {"name": "Strawberry Popping Boba", "price": 200},
            {"name": "Mango Popping Boba", "price": 200},
            {"name": "Lychee Jelly", "price": 200},
        ]
    }
}


@app.route('/api/sync-menu-to-square', methods=['POST'])
def sync_menu_to_square():
    if not SQUARE_ACCESS_TOKEN or not SQUARE_LOCATION_ID:
        return jsonify({"error": "Square credentials not configured"}), 400

    results = {"categories": [], "items": [], "modifiers": [], "errors": []}
    modifier_list_ids = {}

    for list_key, list_data in MODIFIER_LISTS.items():
        modifiers = []
        for mod in list_data["modifiers"]:
            modifiers.append({
                "type": "MODIFIER",
                "id": f"#{list_key}_{mod['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')}",
                "modifier_data": {
                    "name": mod["name"],
                    "price_money": {"amount": mod["price"], "currency": SQUARE_CURRENCY}
                }
            })

        payload = {
            "idempotency_key": str(uuid.uuid4()),
            "object": {
                "type": "MODIFIER_LIST",
                "id": f"#{list_key}_list",
                "modifier_list_data": {
                    "name": list_data["name"],
                    "modifiers": modifiers
                }
            }
        }

        data, status = square_post('/v2/catalog/object', payload)
        if status == 200:
            cat_obj = data.get("catalog_object", data.get("object", {}))
            modifier_list_ids[list_key] = cat_obj.get("id", "")
            results["modifiers"].append({"name": list_data["name"], "square_id": cat_obj.get("id", "")})
        else:
            results["errors"].append({"step": f"modifier_list_{list_key}", "detail": data})

    category_ids = {}
    for cat in MENU_CATEGORIES:
        payload = {
            "idempotency_key": str(uuid.uuid4()),
            "object": {
                "type": "CATEGORY",
                "id": f"#{cat['id']}_category",
                "category_data": {"name": cat["name"]}
            }
        }
        data, status = square_post('/v2/catalog/object', payload)
        if status == 200:
            cat_obj = data.get("catalog_object", data.get("object", {}))
            category_ids[cat["id"]] = cat_obj.get("id", "")
            results["categories"].append({"name": cat["name"], "square_id": cat_obj.get("id", "")})
        else:
            results["errors"].append({"step": f"category_{cat['id']}", "detail": data})

    for item in MENU_ITEMS:
        variations = []
        sizes = [
            {"name": "Small", "price": item["price"]},
            {"name": "Medium", "price": item["price"] + 200},
            {"name": "Large", "price": item["price"] + 400},
        ]

        for size in sizes:
            variations.append({
                "type": "ITEM_VARIATION",
                "id": f"#{item['id']}_{size['name'].lower()}",
                "item_variation_data": {
                    "item_id": f"#{item['id']}",
                    "name": size["name"],
                    "pricing_type": "FIXED_PRICING",
                    "price_money": {"amount": size["price"], "currency": SQUARE_CURRENCY}
                }
            })

        modifier_list_info = []
        if item["customizable"]:
            for list_key in ["syrups", "cold_foam", "milk", "toppings"]:
                if list_key in modifier_list_ids and modifier_list_ids[list_key]:
                    modifier_list_info.append({
                        "modifier_list_id": modifier_list_ids[list_key],
                        "min_selected_modifiers": 0,
                        "max_selected_modifiers": 3
                    })

        item_data = {
            "name": item["name"],
            "category_id": category_ids.get(item["category"], ""),
            "variations": variations,
            "description": f"Latte Lab - {item['name']}",
            "available_online": True,
            "available_for_pickup": True,
            "available_for_delivery": True
        }
        if modifier_list_info:
            item_data["modifier_list_info"] = modifier_list_info

        payload = {
            "idempotency_key": str(uuid.uuid4()),
            "object": {
                "type": "ITEM",
                "id": f"#{item['id']}",
                "item_data": item_data
            }
        }

        data, status = square_post('/v2/catalog/object', payload)
        if status == 200:
            cat_obj = data.get("catalog_object", data.get("object", {}))
            results["items"].append({"name": item["name"], "square_id": cat_obj.get("id", "")})
        else:
            results["errors"].append({"step": f"item_{item['id']}", "detail": data})

    return jsonify({
        "success": len(results["errors"]) == 0,
        "summary": {
            "categories_created": len(results["categories"]),
            "items_created": len(results["items"]),
            "modifier_lists_created": len(results["modifiers"]),
            "errors": len(results["errors"])
        },
        "details": results
    })


@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    payment_method = data.get("payment_method", "cash")
    if payment_method not in ["cash", "online_transfer"]:
        return jsonify({"error": "Invalid payment method. Use 'cash' or 'online_transfer'"}), 400

    local_order_id = f"LL{datetime.now().strftime('%H%M%S')}{str(uuid.uuid4())[:4].upper()}"

    square_line_items = []
    for item in data.get("items", []):
        modifiers = []
        for mod in item.get("modifiers", []):
            # FIX: Convert modifier price from dollars to cents
            mod_price_cents = int(round(mod.get("price", 0) * 100))
            modifiers.append({
                "name": mod["name"],
                "base_price_money": {"amount": mod_price_cents, "currency": SQUARE_CURRENCY}
            })

        line_item = {
            "name": item["name"],
            "quantity": str(item.get("qty", 1)),
            "base_price_money": {"amount": item["unit_price"], "currency": SQUARE_CURRENCY},
            "note": item.get("instructions", "")[:500]
        }
        if modifiers:
            line_item["modifiers"] = modifiers

        square_line_items.append(line_item)

    fulfillment_type = "PICKUP" if data.get("order_type") == "pickup" else "DELIVERY"

    if payment_method == "online_transfer":
        payment_note = "ONLINE BANK TRANSFER - verify before prep"
    else:
        payment_note = "CASH - pay on pickup/delivery"

    # FIX: Simplified fulfillment structure, removed placed_at, added uid
    fulfillment = {
        "uid": str(uuid.uuid4())[:8],
        "type": fulfillment_type,
        "state": "PROPOSED"
    }

    if fulfillment_type == "PICKUP":
        fulfillment["pickup_details"] = {
            "recipient": {
                "display_name": data.get("customer_name", "Guest")
            },
            "note": payment_note
        }
    else:
        fulfillment["delivery_details"] = {
            "recipient": {
                "display_name": data.get("customer_name", "Guest")
            },
            "address": {
                "address_line_1": data.get("address", "Belize City"),
                "country": "BZ",
                "locality": "Belize City"
            },
            "note": payment_note
        }

    square_payload = {
        "idempotency_key": str(uuid.uuid4()),
        "order": {
            "location_id": SQUARE_LOCATION_ID,
            "reference_id": local_order_id,
            "source": {"name": "Latte Lab App"},
            "line_items": square_line_items,
            "fulfillments": [fulfillment],
            "metadata": {
                "latte_lab_order_id": local_order_id,
                "customer_name": data.get("customer_name", ""),
                "customer_phone": data.get("phone", ""),
                "order_type": data.get("order_type", "pickup"),
                "payment_method": payment_method
            }
        }
    }

    resp_data, status = square_post('/v2/orders', square_payload)

    if status == 200:
        square_order = resp_data.get("order", {})
        order_record = {
            "id": local_order_id,
            "square_order_id": square_order.get("id"),
            "customer_name": data.get("customer_name"),
            "phone": data.get("phone"),
            "address": data.get("address"),
            "order_type": data.get("order_type"),
            "payment_method": payment_method,
            "items": data.get("items"),
            "total": data.get("total"),
            "status": "pending",
            "square_status": square_order.get("state", "OPEN"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        orders_db[local_order_id] = order_record

        payment_msg = "Customer will pay via online bank transfer." if payment_method == "online_transfer" else "Customer pays cash on pickup/delivery."

        return jsonify({
            "success": True,
            "order_id": local_order_id,
            "square_order_id": square_order.get("id"),
            "status": "pending",
            "payment_method": payment_method,
            "message": payment_msg
        })
    else:
        # Log the exact error for debugging
        print(f"SQUARE ORDER ERROR: {json.dumps(resp_data)}")
        return jsonify({
            "success": False,
            "error": "Failed to create order in Square",
            "square_error": resp_data
        }), 500


@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    local_order = orders_db.get(order_id)
    if not local_order:
        return jsonify({"error": "Order not found"}), 404

    if local_order.get("square_order_id"):
        sq_data, status = square_get(f'/v2/orders/{local_order["square_order_id"]}')
        if status == 200:
            sq_order = sq_data.get("order", {})
            local_order["square_status"] = sq_order.get("state", "UNKNOWN")
            sq_state = sq_order.get("state", "")
            if sq_state == "OPEN":
                local_order["status"] = "pending"
            elif sq_state == "COMPLETED":
                local_order["status"] = "delivered"
            elif sq_state == "CANCELED":
                local_order["status"] = "cancelled"
            local_order["updated_at"] = datetime.utcnow().isoformat()

    return jsonify(local_order)


@app.route('/api/orders', methods=['GET'])
def list_orders():
    status_filter = request.args.get('status', 'all')
    orders_list = list(orders_db.values())
    if status_filter != 'all':
        orders_list = [o for o in orders_list if o["status"] == status_filter]
    orders_list.sort(key=lambda x: x["created_at"], reverse=True)
    return jsonify({"orders": orders_list, "count": len(orders_list)})


@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get("status")

    if order_id not in orders_db:
        return jsonify({"error": "Order not found"}), 404

    order = orders_db[order_id]
    order["status"] = new_status
    order["updated_at"] = datetime.utcnow().isoformat()

    return jsonify({"success": True, "order_id": order_id, "status": new_status})


@app.route('/api/webhooks/square', methods=['POST'])
def square_webhook():
    data = request.get_json()
    event_type = data.get("type", "")
    event_data = data.get("data", {})

    if "order" in event_type or "payment" in event_type:
        order_obj = event_data.get("object", {}).get("order", {})
        square_order_id = order_obj.get("id")

        for local_id, local_order in orders_db.items():
            if local_order.get("square_order_id") == square_order_id:
                sq_state = order_obj.get("state", "")
                if sq_state == "OPEN":
                    local_order["status"] = "pending"
                elif sq_state == "COMPLETED":
                    local_order["status"] = "delivered"
                elif sq_state == "CANCELED":
                    local_order["status"] = "cancelled"

                fulfillments = order_obj.get("fulfillments", [])
                for f in fulfillments:
                    f_state = f.get("state", "")
                    if f_state == "PREPARED":
                        local_order["status"] = "ready"
                    elif f_state == "PROPOSED":
                        local_order["status"] = "pending"
                    elif f_state == "RESERVED":
                        local_order["status"] = "preparing"

                local_order["updated_at"] = datetime.utcnow().isoformat()
                break

    return jsonify({"received": True}), 200


@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        "shop_name": "Latte Lab",
        "currency": SQUARE_CURRENCY,
        "currency_symbol": "BZ$" if SQUARE_CURRENCY == "BZD" else "$",
        "tax_rate": 0.0,
        "delivery_fee": 0,
        "min_order": 0,
        "payment_methods": ["cash", "online_transfer"],
        "payment_note": "Cash on pickup/delivery, or Online Bank Transfer.",
        "open_hours": {
            "mon": "7:00 AM - 8:00 PM",
            "tue": "7:00 AM - 8:00 PM",
            "wed": "7:00 AM - 8:00 PM",
            "thu": "7:00 AM - 8:00 PM",
            "fri": "7:00 AM - 9:00 PM",
            "sat": "8:00 AM - 9:00 PM",
            "sun": "8:00 AM - 7:00 PM"
        },
        "square_connected": bool(SQUARE_ACCESS_TOKEN and SQUARE_LOCATION_ID),
        "version": "1.0.0"
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "square_env": SQUARE_ENV,
        "currency": SQUARE_CURRENCY,
        "payment": "cash_and_transfer"
    })


@app.route('/api/menu', methods=['GET'])
def get_menu():
    return jsonify({
        "categories": MENU_CATEGORIES,
        "items": MENU_ITEMS,
        "modifier_lists": MODIFIER_LISTS
    })


if __name__ == '__main__':
    print("=" * 60)
    print("LATTE LAB - Square Integration Server")
    print("=" * 60)
    print(f"Square Environment: {SQUARE_ENV}")
    print(f"Currency: {SQUARE_CURRENCY}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
