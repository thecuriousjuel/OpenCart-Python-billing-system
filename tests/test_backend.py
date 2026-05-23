# tests/test_backend.py
import os
import sys
import shutil
import unittest
from datetime import datetime

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import InventoryModel, CategoryModel, CustomerModel, TransactionModel

class TestBackendModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Backup original data files if they exist
        cls.backup_dir = "data_backup_test"
        if os.path.exists("data"):
            shutil.copytree("data", cls.backup_dir, dirs_exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        # Restore backup or cleanup
        if os.path.exists("data"):
            shutil.rmtree("data")
        if os.path.exists(cls.backup_dir):
            shutil.copytree(cls.backup_dir, "data", dirs_exist_ok=True)
            shutil.rmtree(cls.backup_dir)

    def setUp(self):
        # Reset data folder for fresh tests
        if os.path.exists("data"):
            shutil.rmtree("data")
        os.makedirs("data", exist_ok=True)
        
        # Instantiate fresh models
        self.cat_model = CategoryModel()
        self.inv_model = InventoryModel()
        self.cust_model = CustomerModel()
        self.tx_model = TransactionModel()

    def test_category_management(self):
        # Test addition
        success, msg = self.cat_model.add_category("Vegetables")
        self.assertTrue(success)
        
        # Test duplicate block
        success, msg = self.cat_model.add_category("Vegetables")
        self.assertFalse(success)
        
        # Test list
        cats = self.cat_model.get_all()
        self.assertEqual(len(cats), 1)
        self.assertEqual(cats[0]["category_name"], "Vegetables")

    def test_inventory_crud_and_soft_delete(self):
        # Set up a category
        self.cat_model.add_category("Dairy")
        
        # Add item
        success, res = self.inv_model.add_item(
            name="Milk 1L",
            category="Dairy",
            price="2.50",
            quantity="10",
            mfg_date="2026-01-01",
            expiry_date="2026-06-01"
        )
        self.assertTrue(success)
        item_id = res
        self.assertTrue(item_id.startswith("ITEM-"))
        
        # Verify category count sync
        cats = self.cat_model.get_all()
        self.assertEqual(cats[0]["total_items"], "1")
        
        # Update item price & stock
        success, msg = self.inv_model.update_item(
            item_id=item_id,
            name="Milk Premium 1L",
            category="Dairy",
            price="2.99",
            quantity="15",
            mfg_date="2026-01-01",
            expiry_date="2026-06-01"
        )
        self.assertTrue(success)
        
        updated_item = self.inv_model.get_by_id(item_id)
        self.assertEqual(updated_item["name"], "Milk Premium 1L")
        self.assertEqual(updated_item["price"], "2.99")
        self.assertEqual(updated_item["quantity"], "15")

        # Soft Delete Item
        success, msg = self.inv_model.delete_item(item_id)
        self.assertTrue(success)
        
        # Confirm it is no longer in active inventory
        active_items = self.inv_model.get_all()
        self.assertEqual(len(active_items), 0)
        
        # Confirm it is archived in deleted_inventory.csv
        deleted_item = self.inv_model.get_by_id(item_id)
        self.assertIsNotNone(deleted_item)
        self.assertEqual(deleted_item["name"], "Milk Premium 1L")
        
        # Confirm category count synced to 0
        cats = self.cat_model.get_all()
        self.assertEqual(cats[0]["total_items"], "0")

    def test_customer_management(self):
        # Save customer
        success, msg = self.cust_model.add_or_update(
            phone="9876543210",
            name="John Doe",
            address="123 Shopping Lane"
        )
        self.assertTrue(success)
        
        # Lookup exact
        cust = self.cust_model.get_by_phone("9876543210")
        self.assertIsNotNone(cust)
        self.assertEqual(cust["name"], "John Doe")
        
        # Lookup suggestions prefix
        suggs = self.cust_model.suggest_by_phone_prefix("98765")
        self.assertEqual(len(suggs), 1)
        self.assertEqual(suggs[0]["name"], "John Doe")

    def test_transaction_checkout_safeties(self):
        self.cat_model.add_category("Stationery")
        
        # Add notebook
        _, item_id = self.inv_model.add_item(
            name="Notebook A5",
            category="Stationery",
            price="4.99",
            quantity="5",
            mfg_date="2026-01-01",
            expiry_date="2030-01-01"
        )
        
        # Cart with sufficient stock
        cart_items = [{
            "item_id": item_id,
            "name": "Notebook A5",
            "price": "4.99",
            "quantity": "2"
        }]
        
        # Checkout
        success, res = self.tx_model.checkout(
            customer_phone="9876543210",
            items_list=cart_items,
            discount_percent="10"
        )
        self.assertTrue(success)
        self.assertEqual(float(res["subtotal"]), 9.98)
        self.assertEqual(float(res["grand_total"]), 8.98) # 9.98 * 0.90
        
        # Confirm stock depleted to 3
        updated_item = self.inv_model.get_by_id(item_id)
        self.assertEqual(updated_item["quantity"], "3")
        
        # Cart asking for MORE than 3 units
        invalid_cart = [{
            "item_id": item_id,
            "name": "Notebook A5",
            "price": "4.99",
            "quantity": "5" # exceeds stock of 3
        }]
        
        # Checkout should fail
        success, msg = self.tx_model.checkout(
            customer_phone="9876543210",
            items_list=invalid_cart,
            discount_percent="0"
        )
        self.assertFalse(success)
        self.assertIn("Insufficient stock", msg)

if __name__ == "__main__":
    unittest.main()
