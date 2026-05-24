# seed.py
"""
Database Seeder for the OpenCart Billing System.

Run this script once to populate the data/ directory with a realistic
set of sample records for development and demonstration purposes:
  - 10 product categories
  - 100 products (10 per category) with realistic prices and dates
  - 50 fictional customers with unique phone numbers and addresses
  - 100+ historical transactions spanning the last 60 days
  - Pre-loaded cart sessions for 2 active terminals
  - Low-stock items for testing stock warning indicators

Warning: Running this script will WIPE all existing data in data/ and
replace it with fresh generated records.

Usage:
    uv run python seed.py
"""
import os
import csv
import random
import json
from datetime import datetime, timedelta

def seed_database():
    """Wipes the existing data directory and populates it with a full set of synthetic sample records."""
    print("Initializing database seeder...")
    
    # 1. Setup Directories
    DIRS = ["data", "logs", "bills"]
    for d in DIRS:
        os.makedirs(d, exist_ok=True)

    # 2. Define 10 Categories
    categories_list = [
        "Beverages", "Snacks", "Dairy", "Bakery", "Produce",
        "Meat", "Personal Care", "Household", "Stationery", "Electronics"
    ]
    
    # 3. Define 100 Products (10 per category)
    products_by_category = {
        "Beverages": [
            ("Coke 500ml", 45.00), ("Pepsi 500ml", 42.00), ("Sprite 500ml", 45.00),
            ("Orange Juice 1L", 120.00), ("Apple Juice 1L", 130.00), ("Mineral Water 1L", 20.00),
            ("Green Tea Bag 25s", 150.00), ("Roasted Coffee 250g", 320.00),
            ("Energy Drink 250ml", 110.00), ("Lemon Tea 1L", 90.00)
        ],
        "Snacks": [
            ("Potato Chips 150g", 60.00), ("Chocolate Cookies", 80.00), ("Salted Peanuts 200g", 110.00),
            ("Nacho Chips 150g", 95.00), ("Cheese Crackers 100g", 50.00), ("Popcorn Caramel 80g", 75.00),
            ("Gummy Bears 100g", 85.00), ("Mixed Nuts 150g", 250.00), ("Pretzel Sticks 100g", 55.00),
            ("Oats Bar 40g", 35.00)
        ],
        "Dairy": [
            ("Whole Milk 1L", 66.00), ("Cheddar Cheese 200g", 240.00), ("Butter 500g", 280.00),
            ("Greek Yogurt 150g", 60.00), ("Sour Cream 200g", 90.00), ("Mozzarella 200g", 220.00),
            ("Cottage Cheese 250g", 115.00), ("Whipping Cream 250ml", 140.00),
            ("Soy Milk 1L", 150.00), ("Ice Cream Vanilla 1L", 250.00)
        ],
        "Bakery": [
            ("Sliced White Bread", 40.00), ("Whole Wheat Bread", 50.00), ("Chocolate Croissant", 65.00),
            ("Blueberry Muffin", 70.00), ("Bagels 4pk", 120.00), ("Garlic Bread", 85.00),
            ("Chocolate Cake 500g", 450.00), ("Apple Pie 300g", 180.00), ("Pita Bread 5pk", 60.00),
            ("Cinnamon Rolls 2pk", 95.00)
        ],
        "Produce": [
            ("Fresh Apples 1kg", 180.00), ("Banana 1 Dozen", 60.00), ("Fresh Oranges 1kg", 120.00),
            ("Tomatoes 1kg", 40.00), ("Potatoes 1kg", 30.00), ("Red Onions 1kg", 35.00),
            ("Fresh Spinach 250g", 25.00), ("Carrots 1kg", 60.00), ("Broccoli 500g", 90.00),
            ("Strawberries 250g", 150.00)
        ],
        "Meat": [
            ("Chicken Breast 1kg", 280.00), ("Ground Beef 500g", 350.00), ("Pork Chops 500g", 300.00),
            ("Salmon Fillet 250g", 650.00), ("Bacon 200g", 195.00), ("Turkey Breast 500g", 420.00),
            ("Lamb Chops 500g", 550.00), ("Tuna Canned 150g", 120.00), ("Chicken Sausages 300g", 180.00),
            ("Beef Steak 400g", 480.00)
        ],
        "Personal Care": [
            ("Herbal Shampoo 400ml", 220.00), ("Shower Gel 250ml", 180.00), ("Toothpaste 150g", 95.00),
            ("Toothbrush Medium", 40.00), ("Hand Soap 250ml", 85.00), ("Deodorant Spray 150ml", 210.00),
            ("Body Lotion 400ml", 320.00), ("Shaving Cream 100g", 90.00), ("Face Wash 150ml", 150.00),
            ("Mouthwash 500ml", 190.00)
        ],
        "Household": [
            ("Dishwash Liquid 500ml", 105.00), ("Laundry Detergent 1.5L", 350.00), ("Toilet Paper 4pk", 120.00),
            ("Garbage Bags 30s", 90.00), ("Glass Cleaner 500ml", 85.00), ("Paper Towels 2pk", 95.00),
            ("Fabric Softener 1L", 210.00), ("Multi-Purpose Spray", 130.00), ("Air Freshener", 150.00),
            ("Sponges 3pk", 45.00)
        ],
        "Stationery": [
            ("Notebook A5 Ruler", 80.00), ("Blue Ballpoint Pens 5pk", 50.00), ("Pencil HB 10pk", 60.00),
            ("Eraser & Sharpener", 30.00), ("Sticky Notes 3x3", 45.00), ("Highlight Pens 4pk", 120.00),
            ("A4 Copy Paper 500s", 320.00), ("Plastic Folder A4", 25.00), ("Scissors Office", 75.00),
            ("Ruler Steel 30cm", 40.00)
        ],
        "Electronics": [
            ("USB Flash Drive 64GB", 550.00), ("Wireless Mouse", 699.00), ("Bluetooth Headphones", 1499.00),
            ("Charging Cable Type-C", 199.00), ("AA Batteries 4pk", 150.00), ("LED Desk Lamp", 899.00),
            ("Smartphone Stand", 149.00), ("HDMI Cable 2m", 299.00), ("USB Hub 4-Port", 450.00),
            ("Wall Charger 20W", 499.00)
        ]
    }
    
    # 4. Generate 50 Fictional Customers
    fictional_customers_data = [
        ("Alice Liddell", "Rabbit Hole, Wonderland"),
        ("Sherlock Holmes", "221B Baker Street, London"),
        ("Bruce Wayne", "Wayne Manor, Gotham City"),
        ("Clark Kent", "344 Clinton Street, Metropolis"),
        ("Peter Parker", "20 Ingram Street, Queens, New York"),
        ("Tony Stark", "10880 Malibu Point, California"),
        ("Harry Potter", "4 Privet Drive, Little Whinging, Surrey"),
        ("Frodo Baggins", "Bag End, Hobbiton, The Shire"),
        ("SpongeBob SquarePants", "124 Conch Street, Bikini Bottom"),
        ("Homer Simpson", "742 Evergreen Terrace, Springfield"),
        ("Fred Flintstone", "301 Cobblestone Way, Bedrock"),
        ("Willy Wonka", "Chocolate Factory, Munich"),
        ("Peter Pan", "Hangman's Tree, Neverland"),
        ("Captain Jack Sparrow", "The Black Pearl Cabin, Caribbean"),
        ("Luke Skywalker", "Lars Homestead, Tatooine"),
        ("Princess Leia", "Royal Palace, Alderaan"),
        ("Winnie the Pooh", "100 Acre Wood, Sussex"),
        ("Indiana Jones", "502 Forest Road, Connecticut"),
        ("James Bond", "MI6 Headquarters, London"),
        ("Bilbo Baggins", "Rivendell, Middle-earth"),
        ("Donald Duck", "313 Quack Street, Duckburg"),
        ("Mickey Mouse", "123 Mickey Mouse Club House"),
        ("Mario Plumber", "Peach's Castle, Mushroom Kingdom"),
        ("Sonic Hedgehog", "Green Hill Zone, South Island"),
        ("Shrek Ogre", "The Swamp, Far Far Away"),
        ("Ash Ketchum", "Pallet Town, Kanto Region"),
        ("Arthur Dent", "Country Lane, Cottington"),
        ("Barbie Roberts", "Dreamhouse, Malibu, California"),
        ("Katniss Everdeen", "Victor's Village, District 12"),
        ("Percy Jackson", "Camp Half-Blood, Long Island"),
        ("Jon Snow", "Castle Black, The Wall, Westeros"),
        ("Daenerys Targaryen", "Great Pyramid, Meereen"),
        ("Gandalf Grey", "Middle-earth Transit, The Road"),
        ("Dorothy Gale", "Emerald City Palace, Land of Oz"),
        ("Tarzan Ape", "Treehouse, African Jungle"),
        ("Hercules DemiGod", "Mount Olympus, Greece"),
        ("Robin Hood", "Major Oak, Sherwood Forest"),
        ("Mary Poppins", "17 Cherry Tree Lane, London"),
        ("Aladdin Agrabah", "Cave of Wonders, Agrabah"),
        ("Simba Lion", "Pride Rock, Pride Lands"),
        ("Pikachu Pokemon", "Ash's Backpack, Pallet Town"),
        ("Dracula Count", "Castle Dracula, Transylvania"),
        ("Frankenstein Monster", "Castle Frankenstein, Geneva"),
        ("Robin Boy Wonder", "Batcave, Gotham City"),
        ("Legolas Greenleaf", "Woodland Realm, Mirkwood"),
        ("Katara Waterbender", "Southern Water Tribe"),
        ("Aang Avatar", "Southern Air Temple"),
        ("Walter White", "308 Negra Arroyo Lane, Albuquerque"),
        ("Scooby Doo", "Mystery Machine, Coolsville"),
        ("Kermit Frog", "Swamp Log, Mississippi")
    ]
    
    customers = []
    for i, (name, address) in enumerate(fictional_customers_data):
        # Phone number starting with 0123 (exactly 10 digits)
        phone = f"0123000{i:03d}"
        customers.append({"phone": phone, "name": name, "address": address})
        
    print(f"Generated {len(customers)} fictional customers.")

    # 5. Build Inventory Records (100 products, start with high stock to accommodate transaction generation)
    products = []
    item_idx = 1
    
    # Track inventory lookup by item_id
    inventory_by_id = {}
    
    for cat, items in products_by_category.items():
        for item_name, price in items:
            item_id = f"ITEM-{item_idx:010d}"
            item_idx += 1
            # stock starts at 150 to ensure we don't run out during transaction checks
            stock = 150 
            
            # Dates
            date_added = (datetime.now() - timedelta(days=random.randint(15, 30))).strftime("%Y-%m-%d")
            mfg_date = (datetime.now() - timedelta(days=random.randint(60, 90))).strftime("%Y-%m-%d")
            exp_date = (datetime.now() + timedelta(days=random.randint(180, 365))).strftime("%Y-%m-%d")
            
            p_data = {
                "item_id": item_id,
                "name": item_name,
                "category": cat,
                "price": f"{price:.2f}",
                "quantity": stock,
                "date_added": date_added,
                "mfg_date": mfg_date,
                "expiry_date": exp_date
            }
            products.append(p_data)
            inventory_by_id[item_id] = p_data
            
    print(f"Generated {len(products)} products across 10 categories.")

    # 6. Generate 100 Transactions spread over the last 10 days (10 per day)
    transactions = []
    transaction_items = []
    
    invoice_idx = 1
    
    for day_offset in range(10):
        # target date
        target_date = datetime.now() - timedelta(days=9 - day_offset)
        
        for tx_in_day in range(10):
            invoice_id = f"INVO-{invoice_idx:010d}"
            invoice_idx += 1
            
            # Timestamp
            hour = random.randint(9, 21)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            timestamp = target_date.replace(hour=hour, minute=minute, second=second).strftime("%Y-%m-%d %H:%M:%S")
            
            # Customer
            cust = random.choice(customers)
            cust_phone = cust["phone"]
            
            # Select 1 to 5 random products to purchase
            cart_items = random.sample(products, k=random.randint(1, 5))
            
            subtotal = 0.0
            tx_items_list = []
            
            for p in cart_items:
                qty = random.randint(1, 3)
                price_at_sale = float(p["price"])
                subtotal += qty * price_at_sale
                
                # Deduct stock
                p_id = p["item_id"]
                inventory_by_id[p_id]["quantity"] -= qty
                
                tx_items_list.append({
                    "invoice_id": invoice_id,
                    "item_id": p_id,
                    "quantity": str(qty),
                    "price_at_sale": f"{price_at_sale:.2f}"
                })
                
            subtotal = round(subtotal, 2)
            discount_percent = random.choice([0.0, 5.0, 10.0, 15.0])
            grand_total = round(subtotal * (1 - (discount_percent / 100.0)), 2)
            
            transactions.append({
                "invoice_id": invoice_id,
                "timestamp": timestamp,
                "customer_phone": cust_phone,
                "subtotal": f"{subtotal:.2f}",
                "discount_percent": f"{discount_percent}",
                "grand_total": f"{grand_total:.2f}"
            })
            transaction_items.extend(tx_items_list)
            
    print(f"Generated {len(transactions)} transaction invoices and {len(transaction_items)} line items.")

    # 7. Generate 2 pre-filled Carts and 3 empty Carts
    carts = []
    cart_items = []
    
    # Cart 1 pre-filled (index 1)
    cart1_invoice = f"INVO-CART000001"
    cart1_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    carts.append({
        "cart_index": "1",
        "invoice_id": cart1_invoice,
        "timestamp": cart1_timestamp,
        "customer_phone": customers[0]["phone"],
        "customer_name": customers[0]["name"],
        "customer_address": customers[0]["address"],
        "discount": "5"
    })
    # Add 3 items to Cart 1
    cart_items.append({"cart_index": "1", "item_id": products[0]["item_id"], "quantity": "2"}) # Beverages Coke
    cart_items.append({"cart_index": "1", "item_id": products[10]["item_id"], "quantity": "3"}) # Snacks Potato Chips
    cart_items.append({"cart_index": "1", "item_id": products[20]["item_id"], "quantity": "1"}) # Dairy Whole Milk

    # Cart 2 pre-filled (index 2)
    cart2_invoice = f"INVO-CART000002"
    cart2_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    carts.append({
        "cart_index": "2",
        "invoice_id": cart2_invoice,
        "timestamp": cart2_timestamp,
        "customer_phone": customers[5]["phone"],
        "customer_name": customers[5]["name"],
        "customer_address": customers[5]["address"],
        "discount": "10"
    })
    # Add 2 items to Cart 2
    cart_items.append({"cart_index": "2", "item_id": products[80]["item_id"], "quantity": "3"}) # Stationery Notebook
    cart_items.append({"cart_index": "2", "item_id": products[90]["item_id"], "quantity": "1"}) # Electronics USB Flash Drive

    # Cart 3, 4, 5 Empty headers (indexes 3, 4, 5)
    for c_idx in range(3, 6):
        carts.append({
            "cart_index": str(c_idx),
            "invoice_id": f"INVO-CART00000{c_idx}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer_phone": "",
            "customer_name": "",
            "customer_address": "",
            "discount": "0"
        })
        
    print("Generated 5 billing carts configuration (Cart 1 and Cart 2 pre-filled).")

    # 8. Compute Category Counts based on active products
    category_counts = {}
    for cat in categories_list:
        category_counts[cat] = 0
        
    for p in products:
        cat = p["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        
    categories_data = []
    for cat in categories_list:
        categories_data.append({
            "category_name": cat,
            "total_items": str(category_counts[cat])
        })

    # Force 8 random products to have stock between 1 and 4 for low stock warnings
    low_stock_indices = random.sample(range(len(products)), 8)
    for idx in low_stock_indices:
        products[idx]["quantity"] = random.randint(1, 4)

    # Convert product quantities back to string for writing
    for p in products:
        p["quantity"] = str(p["quantity"])

    # 9. Write all to CSV files
    print("Writing files to data/ folder...")
    
    # write categories.csv
    with open("data/categories.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category_name", "total_items"])
        writer.writeheader()
        writer.writerows(categories_data)
        
    # write inventory.csv
    with open("data/inventory.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "name", "category", "price", "quantity", "date_added", "mfg_date", "expiry_date"])
        writer.writeheader()
        writer.writerows(products)
        
    # write deleted_inventory.csv (empty headers)
    with open("data/deleted_inventory.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "name", "category", "price", "quantity", "date_added", "mfg_date", "expiry_date"])
        writer.writeheader()
        
    # write customers.csv
    with open("data/customers.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["phone", "name", "address"])
        writer.writeheader()
        writer.writerows(customers)
        
    # write transactions.csv
    with open("data/transactions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["invoice_id", "timestamp", "customer_phone", "subtotal", "discount_percent", "grand_total"])
        writer.writeheader()
        writer.writerows(transactions)
        
    # write transaction_items.csv
    with open("data/transaction_items.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["invoice_id", "item_id", "quantity", "price_at_sale"])
        writer.writeheader()
        writer.writerows(transaction_items)
        
    # write carts.csv
    with open("data/carts.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["cart_index", "invoice_id", "timestamp", "customer_phone", "customer_name", "customer_address", "discount"])
        writer.writeheader()
        writer.writerows(carts)
        
    # write cart_items.csv
    with open("data/cart_items.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["cart_index", "item_id", "quantity"])
        writer.writeheader()
        writer.writerows(cart_items)

    # 10. Write settings.json to ROOT folder
    print("Writing settings.json configuration to root folder...")
    with open("settings.json", "w", encoding="utf-8") as f:
        json.dump({"theme": "cosmo"}, f, indent=4)
        
    # Remove old settings file if exists to prevent confusion
    old_settings = "data/settings.json"
    if os.path.exists(old_settings):
        try:
            os.remove(old_settings)
        except Exception:
            pass

    print("Database seeding completed successfully! Wiped existing records and populated clean mock retail datasets.")

if __name__ == "__main__":
    seed_database()
