import mysql.connector
from datetime import datetime, timedelta
import math  # Import math for rounding

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",  # Change this to your MySQL username
    password="mysql@123",  # Change this to your MySQL password
    database="smart_parking"
)

cursor = db.cursor()

# ---------------------- Create Tables ----------------------

def create_tables():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            plate_number VARCHAR(20) NOT NULL,
            entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            exit_time DATETIME NULL,
            amount_due FLOAT DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            id INT AUTO_INCREMENT PRIMARY KEY,
            plate_number VARCHAR(20) UNIQUE NOT NULL,
            reason VARCHAR(255) NOT NULL,
            added_on DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            plate_number VARCHAR(20) NOT NULL,
            amount FLOAT NOT NULL,
            payment_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            payment_method VARCHAR(50) NOT NULL
        )
    """)

    db.commit()
    print("✅ Tables Created Successfully!")


# ---------------------- Blacklist Check ----------------------

def check_blacklist(plate_number):
    """Check if a vehicle is in the blacklist."""
    cursor.execute("SELECT * FROM blacklist WHERE plate_number = %s", (plate_number,))
    result = cursor.fetchone()
    return bool(result)  # Returns True if blacklisted, False otherwise


# ---------------------- Log Vehicle Entry ----------------------

def log_entry(plate_number):
    """Log vehicle entry into the database."""
    cursor.execute("INSERT INTO vehicle_logs (plate_number) VALUES (%s)", (plate_number,))
    db.commit()
    print(f"🚗 Vehicle {plate_number} entered.")


# ---------------------- Log Vehicle Exit & Calculate Fee ----------------------

def log_exit(plate_number):
    """Log vehicle exit and calculate fee based on duration."""
    plate_number = str(plate_number)  # Ensure plate_number is a string

    # Fetch entry time
    cursor.execute("SELECT entry_time FROM vehicle_logs WHERE plate_number = %s AND exit_time IS NULL", (plate_number,))
    entry_data = cursor.fetchone()

    if entry_data is None:
        print(f"❌ No active parking session found for plate: {plate_number}")
        return {"status": "error", "message": "Vehicle has not entered the parking lot."}

    entry_time = entry_data[0]
    exit_time = datetime.now()

    # Calculate total time parked in minutes
    parked_minutes = (exit_time - entry_time).total_seconds() / 60

    # Round up to the nearest 5 minutes
    parked_5min_blocks = math.ceil(parked_minutes / 5)  # Always rounds up

    # Parking Fee Calculation (₹5 per 5-minute block)
    amount_due = round(parked_5min_blocks * 5, 2)  # ₹5 per 5 minutes

    # Check if payment is already made
    cursor.execute("SELECT SUM(amount) FROM payments WHERE plate_number = %s", (plate_number,))
    total_paid = cursor.fetchone()[0] or 0  # Default to 0 if no payment found

    # Debugging: Print payment check results
    print(f"🔍 Plate: {plate_number}, Amount Due: ₹{amount_due}, Total Paid: ₹{total_paid}")

    # If payment is insufficient, deny exit and return remaining amount to be paid
    if total_paid < amount_due:
        amount_remaining = amount_due - total_paid
        print(f"🚨 Payment required! Vehicle {plate_number} needs to pay ₹{amount_remaining} before exit.")
        return {"status": "error", "message": f"Payment required: ₹{amount_remaining}"}

    # Log the exit time and update vehicle log
    cursor.execute(
        "UPDATE vehicle_logs SET exit_time = %s, amount_due = %s WHERE plate_number = %s AND exit_time IS NULL",
        (exit_time, amount_due, plate_number)
    )
    db.commit()

    print(f"✅ Vehicle {plate_number} exited. Total Fee: ₹{amount_due} (Paid: ₹{total_paid})")
    return {"status": "success", "message": f"Exit allowed. Paid ₹{total_paid}"}



# ---------------------- Store Payment ----------------------

def process_payment(plate_number, amount, method):

    plate_number = str(plate_number)

    # Check if vehicle has an active entry without exit
    cursor.execute("SELECT entry_time FROM vehicle_logs WHERE plate_number = %s AND exit_time IS NULL", (plate_number,))
    entry_data = cursor.fetchone()

    if entry_data is None:
        print(f"🚨 Payment Denied! Vehicle {plate_number} has no active entry.")
        return {"status": "error", "message": "Vehicle has not entered the parking lot."}

    """Store payment record in database."""
    cursor.execute("INSERT INTO payments (plate_number, amount, payment_method) VALUES (%s, %s, %s)",
                   (plate_number, amount, method))
    db.commit()
    print(f"💰 Payment of ₹{amount} recorded for {plate_number} using {method}.")
    return {"status": "success", "message": f"Payment of ₹{amount} recorded."}


# ---------------------- Get Parking Status ----------------------

def get_parking_status():
    """Retrieve current number of occupied and available parking slots."""
    total_slots = 50  # Assume 50 total parking slots
    cursor.execute("SELECT COUNT(*) FROM vehicle_logs WHERE exit_time IS NULL")
    occupied_slots = cursor.fetchone()[0]
    available_slots = total_slots - occupied_slots
    return {"occupied": occupied_slots, "available": available_slots}


# ---------------------- Run Table Creation ----------------------

if __name__ == "__main__":
    create_tables()
