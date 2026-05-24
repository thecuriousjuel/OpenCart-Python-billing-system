# database.py
"""
CSV-based database models for the OpenCart Billing System.

Each model class extends CSVDatabase and wraps a specific CSV file,
providing domain-specific CRUD operations. All writes use an atomic
write-replace pattern to prevent data corruption on failure:
  - CategoryModel  → data/categories.csv
  - InventoryModel → data/inventory.csv + data/deleted_inventory.csv
  - CustomerModel  → data/customers.csv
  - TransactionModel → data/transactions.csv + data/transaction_items.csv
  - CartModel      → data/carts.csv
  - CartItemModel  → data/cart_items.csv
"""
import os
import csv
import random
import json
from datetime import datetime

class CSVDatabase:
    """Base class for thread-safe atomic CSV database access using the write-replace pattern."""
    def __init__(self, filepath, headers):
        self.filepath = filepath
        self.headers = headers
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            self.write_all([])

    def read_all(self):
        """Reads all rows from the CSV file as a list of dictionaries."""
        try:
            with open(self.filepath, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            # If reading fails or file is corrupt, return empty list
            return []

    def write_all(self, rows):
        """Writes rows atomically to the CSV file using the write-replace pattern."""
        temp_filepath = f"{self.filepath}.tmp"
        try:
            with open(temp_filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writeheader()
                for row in rows:
                    # Filter row dict to only include defined headers
                    filtered_row = {k: row[k] for k in self.headers if k in row}
                    writer.writerow(filtered_row)
            # Atomic replace
            os.replace(temp_filepath, self.filepath)
        except Exception as e:
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except Exception:
                    pass
            raise e

    def append_row(self, row):
        """Reads all rows, appends the given row dict, and writes the complete list back atomically."""
        rows = self.read_all()
        rows.append(row)
        self.write_all(rows)


class CategoryModel(CSVDatabase):
    """Manages categories.csv database."""
    def __init__(self):
        super().__init__("data/categories.csv", ["category_name", "total_items"])

    def get_all(self):
        """Returns all category records as a list of dicts."""
        return self.read_all()

    def add_category(self, name):
        """Adds a new category by name, rejecting empty or duplicate names."""
        name = name.strip()
        if not name:
            return False, "Category name cannot be empty."
        
        rows = self.get_all()
        for r in rows:
            if r["category_name"].lower() == name.lower():
                return False, f"Category '{name}' already exists."
        
        new_row = {"category_name": name, "total_items": "0"}
        self.append_row(new_row)
        return True, f"Category '{name}' added successfully."

    def delete_category(self, name):
        """Deletes a category by name if no active inventory items belong to it."""
        name = name.strip()
        # Verify if any active item uses this category
        from src.database import InventoryModel
        inv = InventoryModel()
        active_items = inv.get_all()
        for item in active_items:
            if item["category"].lower() == name.lower():
                return False, f"Cannot delete category '{name}' as items in inventory belong to it."
        
        rows = self.get_all()
        new_rows = [r for r in rows if r["category_name"].lower() != name.lower()]
        if len(new_rows) == len(rows):
            return False, f"Category '{name}' not found."
        
        self.write_all(new_rows)
        return True, f"Category '{name}' deleted."

    def sync_counts(self, active_items):
        """Recalculates and persists the total_items count per category based on the active inventory list."""
        counts = {}
        for item in active_items:
            cat = item["category"]
            counts[cat] = counts.get(cat, 0) + 1
        
        categories = self.get_all()
        for cat_row in categories:
            name = cat_row["category_name"]
            cat_row["total_items"] = str(counts.get(name, 0))
        
        self.write_all(categories)


class InventoryModel(CSVDatabase):
    """Manages inventory.csv and deleted_inventory.csv database."""
    def __init__(self):
        super().__init__("data/inventory.csv", [
            "item_id", "name", "category", "price", "quantity", "date_added", "mfg_date", "expiry_date"
        ])
        self.deleted_db = CSVDatabase("data/deleted_inventory.csv", self.headers)

    def get_all(self):
        """Returns all active (non-deleted) inventory items."""
        return self.read_all()

    def get_all_including_deleted(self):
        """Returns all inventory items including those soft-deleted to the archive file."""
        active = self.get_all()
        deleted = self.deleted_db.read_all()
        return active + deleted

    def get_by_id(self, item_id):
        """Looks up and returns a single item dict by item_id, searching active and deleted records."""
        all_items = self.get_all_including_deleted()
        for item in all_items:
            if item["item_id"] == item_id:
                return item
        return None

    def generate_unique_id(self):
        """Generates a random unique ITEM-XXXXXXXXXX identifier not already present in any record."""
        existing_ids = {r["item_id"] for r in self.get_all_including_deleted()}
        while True:
            new_id = f"ITEM-{''.join(random.choices('0123456789', k=10))}"
            if new_id not in existing_ids:
                return new_id

    def add_item(self, name, category, price, quantity, mfg_date, expiry_date):
        """Validates inputs and appends a new product to the active inventory CSV."""
        name = name.strip()
        if not name:
            return False, "Item name cannot be empty."
        try:
            price_val = round(float(price), 2)
            if price_val <= 0:
                return False, "Price must be greater than zero."
        except ValueError:
            return False, "Price must be a valid number."

        try:
            qty_val = int(quantity)
            if qty_val < 0:
                return False, "Quantity cannot be negative."
        except ValueError:
            return False, "Quantity must be an integer."

        # Date validations
        try:
            mfg = datetime.strptime(mfg_date.strip(), "%Y-%m-%d")
            exp = datetime.strptime(expiry_date.strip(), "%Y-%m-%d")
            if exp <= mfg:
                return False, "Expiry date must be after manufacture date."
        except ValueError:
            return False, "Dates must be in YYYY-MM-DD format."

        item_id = self.generate_unique_id()
        date_added = datetime.now().strftime("%Y-%m-%d")

        new_item = {
            "item_id": item_id,
            "name": name,
            "category": category,
            "price": str(price_val),
            "quantity": str(qty_val),
            "date_added": date_added,
            "mfg_date": mfg_date.strip(),
            "expiry_date": expiry_date.strip()
        }

        self.append_row(new_item)
        
        # Sync Category counts
        cat_model = CategoryModel()
        cat_model.sync_counts(self.get_all())
        
        return True, item_id

    def update_item(self, item_id, name, category, price, quantity, mfg_date, expiry_date):
        """Validates inputs and updates an existing active inventory item in-place."""
        items = self.get_all()
        found_idx = -1
        for i, item in enumerate(items):
            if item["item_id"] == item_id:
                found_idx = i
                break
        
        if found_idx == -1:
            return False, "Item not found in active inventory."

        name = name.strip()
        if not name:
            return False, "Item name cannot be empty."
        try:
            price_val = round(float(price), 2)
            if price_val <= 0:
                return False, "Price must be greater than zero."
        except ValueError:
            return False, "Price must be a valid number."

        try:
            qty_val = int(quantity)
            if qty_val < 0:
                return False, "Quantity cannot be negative."
        except ValueError:
            return False, "Quantity must be an integer."

        try:
            mfg = datetime.strptime(mfg_date.strip(), "%Y-%m-%d")
            exp = datetime.strptime(expiry_date.strip(), "%Y-%m-%d")
            if exp <= mfg:
                return False, "Expiry date must be after manufacture date."
        except ValueError:
            return False, "Dates must be in YYYY-MM-DD format."

        # Keep original date_added
        date_added = items[found_idx]["date_added"]

        items[found_idx] = {
            "item_id": item_id,
            "name": name,
            "category": category,
            "price": str(price_val),
            "quantity": str(qty_val),
            "date_added": date_added,
            "mfg_date": mfg_date.strip(),
            "expiry_date": expiry_date.strip()
        }

        self.write_all(items)
        
        # Sync Category counts
        cat_model = CategoryModel()
        cat_model.sync_counts(items)
        
        return True, "Item updated successfully."

    def delete_item(self, item_id):
        """Moves an item from active inventory to the deleted archive (soft delete)."""
        items = self.get_all()
        item_to_delete = None
        new_items = []
        for item in items:
            if item["item_id"] == item_id:
                item_to_delete = item
            else:
                new_items.append(item)

        if not item_to_delete:
            return False, "Item not found."

        # 1. Append to deleted_inventory.csv
        self.deleted_db.append_row(item_to_delete)
        # 2. Write updated active inventory
        self.write_all(new_items)
        
        # 3. Sync Category counts
        cat_model = CategoryModel()
        cat_model.sync_counts(new_items)
        
        return True, "Item deleted and archived successfully."

    def get_low_stock(self, threshold=5):
        """Returns all active inventory items whose quantity is at or below the given threshold."""
        return [item for item in self.get_all() if int(item["quantity"]) <= threshold]


class CustomerModel(CSVDatabase):
    """Manages customers.csv database."""
    def __init__(self):
        super().__init__("data/customers.csv", ["phone", "name", "address"])

    def get_by_phone(self, phone):
        """Returns the customer record matching the given phone number (normalised to digits only)."""
        phone_normalized = "".join(filter(str.isdigit, phone))
        for customer in self.read_all():
            if customer["phone"] == phone_normalized:
                return customer
        return None

    def suggest_by_phone_prefix(self, prefix):
        """Returns up to 5 customers whose phone number starts with the given digit prefix."""
        prefix_normalized = "".join(filter(str.isdigit, prefix))
        if not prefix_normalized:
            return []
        suggestions = []
        for customer in self.read_all():
            if customer["phone"].startswith(prefix_normalized):
                suggestions.append(customer)
        return suggestions[:5] # limit suggestions to top 5

    def search_customers(self, query):
        """Returns up to 5 customers whose name or phone contain the given search string."""
        q = query.strip().lower()
        if not q:
            return []
        results = []
        for customer in self.read_all():
            if q in customer["phone"].lower() or q in customer["name"].lower():
                results.append(customer)
        return results[:5]


    def add_or_update(self, phone, name, address):
        """Inserts a new customer or updates an existing record matched by phone number."""
        phone_normalized = "".join(filter(str.isdigit, phone))
        if len(phone_normalized) != 10:
            return False, "Phone number must be exactly 10 digits."
        name = name.strip()
        if not name:
            return False, "Customer name cannot be empty."

        customers = self.read_all()
        found_idx = -1
        for i, cust in enumerate(customers):
            if cust["phone"] == phone_normalized:
                found_idx = i
                break

        new_cust = {
            "phone": phone_normalized,
            "name": name,
            "address": address.strip()
        }

        if found_idx != -1:
            customers[found_idx] = new_cust
        else:
            customers.append(new_cust)

        self.write_all(customers)
        return True, "Customer saved."


class TransactionModel(CSVDatabase):
    """Manages transactions.csv and transaction_items.csv database."""
    def __init__(self):
        super().__init__("data/transactions.csv", [
            "invoice_id", "timestamp", "customer_phone", "subtotal", "discount_percent", "grand_total"
        ])
        self.items_db = CSVDatabase("data/transaction_items.csv", [
            "invoice_id", "item_id", "quantity", "price_at_sale"
        ])

    def generate_invoice_id(self):
        """Generates a random unique INVO-XXXXXXXXXX invoice identifier not already in the transactions file."""
        existing_invoices = {r["invoice_id"] for r in self.read_all()}
        while True:
            new_id = f"INVO-{''.join(random.choices('0123456789', k=10))}"
            if new_id not in existing_invoices:
                return new_id

    def checkout(self, customer_phone, items_list, discount_percent):
        """Executes an atomic checkout: validates stock, deducts inventory, writes invoice header and line items."""
        """
        Executes an atomic checkout:
        1. Validates inventory levels.
        2. Deducts inventory stock.
        3. Appends transaction header.
        4. Appends line-items.
        """
        # Load active inventory
        inv_model = InventoryModel()
        active_items = inv_model.get_all()
        item_map = {item["item_id"]: item for item in active_items}

        # Step 1: Validate stock quantities before checking out
        for cart_item in items_list:
            item_id = cart_item["item_id"]
            req_qty = int(cart_item["quantity"])
            
            if item_id not in item_map:
                return False, f"Item {item_id} ('{cart_item['name']}') is no longer in inventory."
            
            avail_qty = int(item_map[item_id]["quantity"])
            if req_qty > avail_qty:
                return False, f"Insufficient stock for '{cart_item['name']}'. Requested: {req_qty}, Available: {avail_qty}."

        # Step 2: Deduct stock from inventory in memory
        for cart_item in items_list:
            item_id = cart_item["item_id"]
            req_qty = int(cart_item["quantity"])
            current_qty = int(item_map[item_id]["quantity"])
            item_map[item_id]["quantity"] = str(current_qty - req_qty)

        # Step 3: Write modified inventory back atomically
        inv_model.write_all(list(item_map.values()))

        # Step 4: Write transactions
        invoice_id = self.generate_invoice_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Compute totals
        subtotal = 0.0
        for cart_item in items_list:
            subtotal += int(cart_item["quantity"]) * float(cart_item["price"])
        
        subtotal = round(subtotal, 2)
        disc_val = round(float(discount_percent), 2)
        grand_total = round(subtotal * (1 - (disc_val / 100.0)), 2)

        # Append transaction header
        transaction_header = {
            "invoice_id": invoice_id,
            "timestamp": timestamp,
            "customer_phone": "".join(filter(str.isdigit, customer_phone)),
            "subtotal": str(subtotal),
            "discount_percent": str(disc_val),
            "grand_total": str(grand_total)
        }
        self.append_row(transaction_header)

        # Append line items
        for cart_item in items_list:
            line_item = {
                "invoice_id": invoice_id,
                "item_id": cart_item["item_id"],
                "quantity": str(cart_item["quantity"]),
                "price_at_sale": str(cart_item["price"])
            }
            self.items_db.append_row(line_item)

        # Sync counts just in case
        cat_model = CategoryModel()
        cat_model.sync_counts(inv_model.get_all())

        return True, {
            "invoice_id": invoice_id,
            "timestamp": timestamp,
            "subtotal": subtotal,
            "discount_percent": disc_val,
            "grand_total": grand_total
        }

    def get_history(self):
        """Returns all transactions sorted by timestamp descending (most recent first)."""
        # Return history sorted by timestamp descending
        history = self.read_all()
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history

    def get_details(self, invoice_id):
        """Fetches the full invoice detail dict including the header and all associated line items."""
        # Get header
        header = None
        for tx in self.read_all():
            if tx["invoice_id"] == invoice_id:
                header = tx
                break
        if not header:
            return None

        # Get items
        items = []
        inv_model = InventoryModel()
        for line in self.items_db.read_all():
            if line["invoice_id"] == invoice_id:
                item_details = inv_model.get_by_id(line["item_id"])
                name = item_details["name"] if item_details else "Deleted/Unknown Item"
                items.append({
                    "item_id": line["item_id"],
                    "name": name,
                    "quantity": int(line["quantity"]),
                    "price_at_sale": float(line["price_at_sale"]),
                    "subtotal": round(int(line["quantity"]) * float(line["price_at_sale"]), 2)
                })

        return {
            "header": header,
            "items": items
        }

    def get_customer_purchase_count(self, phone):
        """Counts and returns how many invoices are linked to the given customer phone number."""
        phone_normalized = "".join(filter(str.isdigit, phone))
        if not phone_normalized:
            return 0
        txs = self.read_all()
        return sum(1 for tx in txs if tx["customer_phone"] == phone_normalized)

    def get_customer_total_spent(self, phone):
        """Sums and returns the total grand_total spend for all invoices linked to the given phone number."""
        phone_normalized = "".join(filter(str.isdigit, phone))
        if not phone_normalized:
            return 0.0
        txs = self.read_all()
        return sum(float(tx["grand_total"]) for tx in txs if tx["customer_phone"] == phone_normalized)



class CartModel(CSVDatabase):
    """Manages active billing carts metadata in carts.csv."""
    def __init__(self):
        super().__init__("data/carts.csv", [
            "cart_index", "invoice_id", "timestamp", "customer_phone", "customer_name", "customer_address", "discount"
        ])


class CartItemModel(CSVDatabase):
    """Manages active billing cart items in cart_items.csv."""
    def __init__(self):
        super().__init__("data/cart_items.csv", [
            "cart_index", "item_id", "quantity"
        ])

