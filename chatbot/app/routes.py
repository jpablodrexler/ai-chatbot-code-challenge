from flask import Blueprint, jsonify

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    # Dummy data for demonstration
    order_data = {
        1: {"item": "Laptop", "quantity": 1},
        2: {"item": "Phone", "quantity": 2},
        3: {"item": "Book", "quantity": 5}
    }
    return jsonify({
        "order_id": id,
        "details": order_data.get(id, "Order not found")
    })
