import stripe
from flask import request, jsonify

stripe.api_key = "your_stripe_secret_key"


def process_payment(plate_number, amount, method):
    if not amount:
        return {"status": "failed", "message": "Amount cannot be empty!"}

    # Example logic
    print(f"Processing payment of {amount} via {method} for plate {plate_number}")
    return {"status": "success", "message": "Payment recorded."}

    '''
    payment_intent = stripe.PaymentIntent.create(
        amount=int(amount * 100),  # Convert to cents
        currency="inr",
        payment_method_types=["card"]
    )
    return payment_intent.client_secret
    '''

def calculate_parking_fee(plate_number):
    # Assume ₹50 per hour
    return 50
