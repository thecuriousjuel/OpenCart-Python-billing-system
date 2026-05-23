# src/gui/billing.py
"""
Billing / Cashier Terminal Page for the OpenCart Billing System.

Manages up to 5 concurrent cart sessions (persisted to CSV), handles
customer autocomplete lookups, item search and quantity management,
discount application, stock validation, and PDF receipt generation on checkout.
Includes safeguards for customer name mismatches and double-step checkout confirmation.
"""
import os
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from datetime import datetime
from src.utils import logger

class BillingPage(tb.Frame):
    """Multi-cart cashier terminal supporting customer lookup, item selection, and invoice checkout."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Cart structure: Up to 5 carts concurrent support (now loaded from CSV)
        self.active_cart_index = 1
        self.carts = self.load_carts()
            
        # Top Panel: Cart tabs and Invoice ID display
        top_frame = tb.Frame(self, padding=15)
        top_frame.pack(fill="x")
        
        tb.Label(top_frame, text="Active Billing Terminals: ", font=("Helvetica", 12, "bold"), bootstyle="primary").pack(side="left")
        
        self.cart_buttons = {}
        for idx in range(1, 6):
            btn = tb.Button(
                top_frame, 
                text=f"Cart {idx}", 
                bootstyle="light-outline" if idx != 1 else "success",
                command=lambda val=idx: self.switch_cart(val)
            )
            btn.pack(side="left", padx=5)
            self.cart_buttons[idx] = btn
            
        # Invoice indicator on top right
        self.lbl_invoice_meta = tb.Label(
            top_frame, 
            text="Invoice ID: N/A | Time: N/A", 
            font=("Helvetica", 11, "bold"), 
            bootstyle="warning"
        )
        self.lbl_invoice_meta.pack(side="right", padx=10)
        
        # Grid partitions: Left (Customer + Item Picker + Cart list) and Right (Total Summary Box)
        main_billing_split = tb.Frame(self)
        main_billing_split.pack(fill="both", expand=True, padx=15, pady=5)
        
        main_billing_split.grid_columnconfigure(0, weight=7) # Left Panel
        main_billing_split.grid_columnconfigure(1, weight=3) # Right Panel
        main_billing_split.grid_rowconfigure(0, weight=1)
        
        left_layout = tb.Frame(main_billing_split)
        left_layout.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Section A: Customer Details
        cust_frame = tb.Labelframe(left_layout, text="Buyer Information Details", padding=10, bootstyle="primary")
        cust_frame.pack(fill="x", pady=(0, 10))
        cust_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.var_c_phone = tk.StringVar()
        self.var_c_name = tk.StringVar()
        self.var_c_address = tk.StringVar()
        self.var_c_purchases = tk.StringVar(value="0")
        
        # Handle phone and name traces to trigger matching customer suggestions
        self.var_c_phone.trace_add("write", lambda *args: self.handle_customer_suggestions("phone"))
        self.var_c_name.trace_add("write", lambda *args: self.handle_customer_suggestions("name"))
        
        # Phone
        p_frame = tb.Frame(cust_frame)
        p_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        tb.Label(p_frame, text="Phone Number * (Type to query)", font=("Helvetica", 9)).pack(anchor="w")
        tb.Entry(p_frame, textvariable=self.var_c_phone).pack(fill="x")
        
        # Name
        n_frame = tb.Frame(cust_frame)
        n_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        tb.Label(n_frame, text="Customer Name * (Type to query)", font=("Helvetica", 9)).pack(anchor="w")
        tb.Entry(n_frame, textvariable=self.var_c_name).pack(fill="x")
        
        # Address
        a_frame = tb.Frame(cust_frame)
        a_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        tb.Label(a_frame, text="Address (Optional)", font=("Helvetica", 9)).pack(anchor="w")
        tb.Entry(a_frame, textvariable=self.var_c_address).pack(fill="x")

        # Loyalty Purchases Count (Read Only uneditable field)
        purch_frame = tb.Frame(cust_frame)
        purch_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=(5, 5), sticky="w")
        tb.Label(purch_frame, text="Loyalty Purchases Count: ", font=("Helvetica", 9, "bold")).pack(side="left")
        self.ent_purchases = tb.Entry(purch_frame, textvariable=self.var_c_purchases, state="readonly", width=8)
        self.ent_purchases.pack(side="left")
        
        tb.Button(
            purch_frame, 
            text="Clear Customer Details", 
            bootstyle="secondary-outline", 
            padding=2,
            command=self.clear_customer_fields
        ).pack(side="left", padx=15)

        # Customer Suggestions dropdown container (grids on row 2, columnspan=3)
        self.cust_suggestion_container = tb.Frame(cust_frame)
        self.list_cust_suggestions = tk.Listbox(
            self.cust_suggestion_container, 
            height=4, 
            font=("Segoe UI", 10),
            highlightthickness=0
        )
        self.list_cust_suggestions.pack(fill="both", expand=True)
        self.list_cust_suggestions.bind("<Double-Button-1>", lambda e: self.select_suggested_customer())
        self.list_cust_suggestions.bind("<Return>", lambda e: self.select_suggested_customer())

        # Section B: Item Search & Selection Bar
        item_picker_frame = tb.Labelframe(left_layout, text="Search & Insert Product to Cart", padding=10, bootstyle="primary")
        item_picker_frame.pack(fill="x", pady=10)
        
        tb.Label(item_picker_frame, text="Type Item Name or ID:", font=("Helvetica", 10)).pack(anchor="w", pady=(0, 2))
        
        self.var_item_search = tk.StringVar()
        self.var_item_search.trace_add("write", lambda *args: self.handle_item_suggestion())
        self.ent_item_search = tb.Entry(item_picker_frame, textvariable=self.var_item_search)
        self.ent_item_search.pack(fill="x")
        
        # Dynamic Suggestion Listbox (packed below input when searching)
        self.suggestion_container = tb.Frame(item_picker_frame)
        self.list_suggestions = tk.Listbox(
            self.suggestion_container, 
            height=4, 
            font=("Segoe UI", 10),
            highlightthickness=0
        )
        self.list_suggestions.pack(fill="both", expand=True)
        self.list_suggestions.bind("<Double-Button-1>", lambda e: self.add_suggested_item())
        self.list_suggestions.bind("<Return>", lambda e: self.add_suggested_item())
        
        # Section C: Active Cart Table view
        cart_table_frame = tb.Labelframe(left_layout, text="Active Checkout Cart items", padding=10, bootstyle="primary")
        cart_table_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("item_id", "name", "price", "quantity", "subtotal")
        self.cart_tree = tb.Treeview(cart_table_frame, columns=columns, show="headings", bootstyle="primary", height=10)
        self.cart_tree.pack(fill="both", expand=True)
        
        self.cart_tree.heading("item_id", text="Item ID")
        self.cart_tree.heading("name", text="Name")
        self.cart_tree.heading("price", text="Price")
        self.cart_tree.heading("quantity", text="Cart Qty")
        self.cart_tree.heading("subtotal", text="Subtotal")
        
        self.cart_tree.column("item_id", width=120, anchor="center")
        self.cart_tree.column("name", width=220, anchor="w")
        self.cart_tree.column("price", width=90, anchor="e")
        self.cart_tree.column("quantity", width=80, anchor="center")
        self.cart_tree.column("subtotal", width=110, anchor="e")
        
        self.cart_tree.bind("<Double-Button-1>", self.modify_cart_qty_popup)
        
        # Row action buttons
        row_actions = tb.Frame(cart_table_frame)
        row_actions.pack(fill="x", pady=(8, 0))
        
        tb.Button(row_actions, text="Remove Selected Item", bootstyle="danger", command=self.remove_cart_item).pack(side="left")
        tb.Label(row_actions, text="* Double-click a row to update quantity", font=("Helvetica", 9, "italic")).pack(side="right")

        # Right Panel (Receipt Totals Drawer) - Adapt to Theme
        right_panel = tb.Frame(main_billing_split, padding=20)
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        tb.Label(right_panel, text="Receipt Summary", font=("Helvetica", 14, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 20))
        
        # Summary totals labels
        self.lbl_subtotal = tb.Label(right_panel, text="Subtotal: ₹0.00", font=("Helvetica", 12))
        self.lbl_subtotal.pack(anchor="w", pady=10)
        
        # Discount field
        disc_frame = tb.Frame(right_panel)
        disc_frame.pack(fill="x", pady=10)
        tb.Label(disc_frame, text="Discount (%): ", font=("Helvetica", 11)).pack(side="left")
        
        self.var_discount = tk.StringVar(value="0")
        self.var_discount.trace_add("write", lambda *args: self.recalculate_totals())
        self.ent_discount = tb.Entry(disc_frame, textvariable=self.var_discount, width=8)
        self.ent_discount.pack(side="right")
        
        # Grand total
        self.lbl_grand = tb.Label(right_panel, text="Grand Total: ₹0.00", font=("Helvetica", 16, "bold"), bootstyle="primary")
        self.lbl_grand.pack(anchor="w", pady=(30, 20))
        
        # Checkout buttons
        tb.Button(
            right_panel, 
            text="Confirm checkout & Print PDF", 
            bootstyle="success", 
            padding=12,
            command=self.process_checkout
        ).pack(fill="x", pady=10)
        
        tb.Button(
            right_panel, 
            text="Cancel Checkout Order", 
            bootstyle="danger-outline", 
            command=self.reset_active_cart
        ).pack(fill="x")
        
        # Initial colors for suggestions
        self.update_listbox_colors()

    def get_empty_cart_structure(self):
        """Returns a freshly initialised empty cart dictionary with a new invoice ID and timestamp."""
        invoice_id = self.controller.transaction_model.generate_invoice_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "invoice_id": invoice_id,
            "timestamp": timestamp,
            "customer": {"phone": "", "name": "", "address": ""},
            "items": [],
            "discount": 0.0
        }

    def load_carts(self):
        """Reads all cart header and cart item records from CSV and reconstructs in-memory cart structures."""
        carts = {}
        # Initialize default structures
        for idx in range(1, 6):
            carts[idx] = self.get_empty_cart_structure()
            
        try:
            # Load cart headers & line items from CSV databases
            headers = self.controller.cart_model.read_all()
            items_data = self.controller.cart_item_model.read_all()
            
            # Group items by cart_index
            items_by_cart = {}
            for item in items_data:
                idx = int(item["cart_index"])
                items_by_cart.setdefault(idx, []).append(item)
                
            # Populate cart structures
            for h in headers:
                idx = int(h["cart_index"])
                if idx in carts:
                    carts[idx]["invoice_id"] = h["invoice_id"]
                    carts[idx]["timestamp"] = h["timestamp"]
                    carts[idx]["customer"]["phone"] = h["customer_phone"]
                    carts[idx]["customer"]["name"] = h["customer_name"]
                    carts[idx]["customer"]["address"] = h["customer_address"]
                    try:
                        carts[idx]["discount"] = float(h["discount"])
                    except ValueError:
                        carts[idx]["discount"] = 0.0
                        
                    raw_items = items_by_cart.get(idx, [])
                    carts[idx]["items"] = []
                    for ri in raw_items:
                        item_id = ri["item_id"]
                        qty = ri["quantity"]
                        
                        # Fetch current details from active catalog
                        item_info = self.controller.inventory_model.get_by_id(item_id)
                        if item_info:
                            carts[idx]["items"].append({
                                "item_id": item_id,
                                "name": item_info["name"],
                                "price": item_info["price"],
                                "quantity": qty
                            })
                        else:
                            carts[idx]["items"].append({
                                "item_id": item_id,
                                "name": "Deleted/Unknown Item",
                                "price": "0.00",
                                "quantity": qty
                            })
        except Exception as e:
            logger.error(f"Failed to read carts from CSV: {e}")
            
        return carts

    def save_carts(self):
        """Serialises the current in-memory cart states to the CSV databases atomically."""
        # Sync currently active cart variables before saving
        idx = self.active_cart_index
        self.carts[idx]["customer"]["phone"] = self.var_c_phone.get()
        self.carts[idx]["customer"]["name"] = self.var_c_name.get()
        self.carts[idx]["customer"]["address"] = self.var_c_address.get()
        try:
            self.carts[idx]["discount"] = float(self.var_discount.get())
        except ValueError:
            self.carts[idx]["discount"] = 0.0
            
        headers_to_write = []
        items_to_write = []
        
        for idx, cart in self.carts.items():
            headers_to_write.append({
                "cart_index": str(idx),
                "invoice_id": cart["invoice_id"],
                "timestamp": cart["timestamp"],
                "customer_phone": cart["customer"]["phone"],
                "customer_name": cart["customer"]["name"],
                "customer_address": cart["customer"]["address"],
                "discount": str(cart["discount"])
            })
            
            for item in cart["items"]:
                items_to_write.append({
                    "cart_index": str(idx),
                    "item_id": item["item_id"],
                    "quantity": item["quantity"]
                })
                
        try:
            self.controller.cart_model.write_all(headers_to_write)
            self.controller.cart_item_model.write_all(items_to_write)
        except Exception as e:
            logger.error(f"Failed to write carts to CSV: {e}")

    def on_show(self):
        """Reloads carts from CSV and updates the active cart display when navigating to this page."""
        self.carts = self.load_carts() # Reload to stay synced
        self.switch_cart(self.active_cart_index)
        self.suggestion_container.pack_forget()
        self.cust_suggestion_container.grid_forget()
        self.update_listbox_colors()

    def handle_customer_suggestions(self, source_field):
        """Queries customer suggestions as the user types in the phone or name fields and shows a dropdown."""
        if hasattr(self, "_updating_customer_fields") and self._updating_customer_fields:
            return
            
        q = ""
        if source_field == "phone":
            q = self.var_c_phone.get().strip()
        else:
            q = self.var_c_name.get().strip()
            
        if not q:
            self.cust_suggestion_container.grid_forget()
            self.var_c_purchases.set("0")
            return
            
        # Immediate autocomplete if 10-digit phone
        if source_field == "phone":
            digits_only = "".join(filter(str.isdigit, q))
            if len(digits_only) == 10:
                cust = self.controller.customer_model.get_by_phone(digits_only)
                if cust:
                    self._updating_customer_fields = True
                    self.var_c_name.set(cust["name"])
                    self.var_c_address.set(cust["address"])
                    count = self.controller.transaction_model.get_customer_purchase_count(digits_only)
                    self.var_c_purchases.set(str(count))
                    self._updating_customer_fields = False
                    self.cust_suggestion_container.grid_forget()
                    self.controller.show_toast("Buyer Found", f"Autocompleted details for customer: {cust['name']}", "info")
                    return
                else:
                    self.var_c_purchases.set("0")
            else:
                self.var_c_purchases.set("0")
        else:
            self.var_c_purchases.set("0")
            
        matches = self.controller.customer_model.search_customers(q)
        
        self.list_cust_suggestions.delete(0, tk.END)
        if matches:
            for c in matches:
                self.list_cust_suggestions.insert(tk.END, f"{c['phone']} - {c['name']}")
            self.cust_suggestion_container.grid(row=2, column=0, columnspan=3, pady=(5, 5), sticky="ew")
        else:
            self.cust_suggestion_container.grid_forget()

    def select_suggested_customer(self):
        """Autofills buyer information fields from the selected customer in the suggestion dropdown."""
        selected = self.list_cust_suggestions.curselection()
        if not selected:
            return
            
        val = self.list_cust_suggestions.get(selected[0])
        phone = val.split(" - ")[0]
        
        cust = self.controller.customer_model.get_by_phone(phone)
        if cust:
            self._updating_customer_fields = True
            
            self.var_c_phone.set(cust["phone"])
            self.var_c_name.set(cust["name"])
            self.var_c_address.set(cust["address"])
            
            # Fetch purchase counts
            count = self.controller.transaction_model.get_customer_purchase_count(phone)
            self.var_c_purchases.set(str(count))
            
            self._updating_customer_fields = False
            self.cust_suggestion_container.grid_forget()
            
            self.controller.show_toast("Buyer Selected", f"Details loaded for {cust['name']}", "info")

    def switch_cart(self, index):
        """Saves the current cart state and switches the active cart terminal to the given index."""
        old_idx = self.active_cart_index
        self.carts[old_idx]["customer"]["phone"] = self.var_c_phone.get()
        self.carts[old_idx]["customer"]["name"] = self.var_c_name.get()
        self.carts[old_idx]["customer"]["address"] = self.var_c_address.get()
        try:
            self.carts[old_idx]["discount"] = float(self.var_discount.get())
        except ValueError:
            self.carts[old_idx]["discount"] = 0.0
            
        self.active_cart_index = index
        
        # Render active tab state
        for idx, btn in self.cart_buttons.items():
            if idx == index:
                btn.configure(bootstyle="success")
            else:
                btn.configure(bootstyle="light-outline")
                
        # Load variables of new active cart
        cart = self.carts[index]
        self.lbl_invoice_meta.configure(text=f"Invoice ID: {cart['invoice_id']} | Date: {cart['timestamp'][:10]}")
        
        # Temporarily disable autocomplete checks while filling fields
        self._updating_customer_fields = True
        self.var_c_phone.set("")
        self.var_c_name.set(cart["customer"]["name"])
        self.var_c_address.set(cart["customer"]["address"])
        self.var_c_phone.set(cart["customer"]["phone"])
        
        # Reload purchases count
        if cart["customer"]["phone"]:
            count = self.controller.transaction_model.get_customer_purchase_count(cart["customer"]["phone"])
            self.var_c_purchases.set(str(count))
        else:
            self.var_c_purchases.set("0")
            
        self._updating_customer_fields = False
        
        self.var_discount.set(str(int(cart["discount"]) if cart["discount"].is_integer() else cart["discount"]))
        self.var_item_search.set("")
        self.suggestion_container.pack_forget()
        self.cust_suggestion_container.grid_forget()
        
        self.reload_cart_table()

    def reload_cart_table(self):
        """Refreshes the cart Treeview from the in-memory cart structure, recalculates totals, and saves."""
        self.cart_tree.delete(*self.cart_tree.get_children())
        cart = self.carts[self.active_cart_index]
        for idx, item in enumerate(cart["items"]):
            sub = round(int(item["quantity"]) * float(item["price"]), 2)
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.cart_tree.insert("", "end", values=(
                item["item_id"],
                item["name"],
                f"₹{float(item['price']):.2f}",
                item["quantity"],
                f"₹{sub:.2f}"
            ), tags=(tag,))
        self.controller.apply_striped_tags(self.cart_tree)
        self.recalculate_totals()
        self.save_carts() # Auto save changes to disk

    def recalculate_totals(self):
        """Recomputes and displays the subtotal and grand total from the active cart items and discount."""
        cart = self.carts[self.active_cart_index]
        subtotal = 0.0
        for item in cart["items"]:
            subtotal += int(item["quantity"]) * float(item["price"])
            
        subtotal = round(subtotal, 2)
        
        # Get discount
        try:
            disc = float(self.var_discount.get())
            if not (0 <= disc <= 100):
                disc = 0.0
        except ValueError:
            disc = 0.0
            
        grand = round(subtotal * (1 - (disc / 100.0)), 2)
        
        self.lbl_subtotal.configure(text=f"Subtotal: ₹{subtotal:.2f}")
        self.lbl_grand.configure(text=f"Grand Total: ₹{grand:.2f}")

    def handle_item_suggestion(self):
        """Queries the inventory for items matching the search text and populates the suggestion listbox."""
        q = self.var_item_search.get().strip().lower()
        if not q:
            self.suggestion_container.pack_forget()
            return
            
        items = self.controller.inventory_model.get_all()
        matches = [
            item for item in items 
            if q in item["item_id"].lower() or q in item["name"].lower()
        ]
        
        self.list_suggestions.delete(0, tk.END)
        if matches:
            for item in matches[:5]:
                self.list_suggestions.insert(tk.END, f"{item['item_id']} - {item['name']} [Stock: {item['quantity']}]")
            self.suggestion_container.pack(fill="x", pady=2)
        else:
            self.suggestion_container.pack_forget()

    def add_suggested_item(self):
        """Adds the selected suggested item to the active cart, enforcing stock limits."""
        selected = self.list_suggestions.curselection()
        if not selected:
            return
        
        val = self.list_suggestions.get(selected[0])
        item_id = val.split(" - ")[0]
        
        item = self.controller.inventory_model.get_by_id(item_id)
        if item:
            avail_stock = int(item["quantity"])
            if avail_stock <= 0:
                Messagebox.show_warning(f"Item '{item['name']}' is out of stock.", "Stock Warning")
                return
                
            cart = self.carts[self.active_cart_index]
            
            found_item = None
            for cart_item in cart["items"]:
                if cart_item["item_id"] == item_id:
                    found_item = cart_item
                    break
                    
            if found_item:
                if int(found_item["quantity"]) + 1 > avail_stock:
                    Messagebox.show_error(f"Cannot exceed available stock of {avail_stock} units.", "Stock Overflow")
                    return
                found_item["quantity"] = str(int(found_item["quantity"]) + 1)
            else:
                cart["items"].append({
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "price": item["price"],
                    "quantity": "1"
                })
                
            self.var_item_search.set("")
            self.suggestion_container.pack_forget()
            self.reload_cart_table()
            self.controller.show_toast("Cart Updated", f"Added '{item['name']}' to Cart.", "info")

    def remove_cart_item(self):
        """Removes the selected row from the active cart and refreshes the table."""
        selected = self.cart_tree.selection()
        if not selected:
            return
        
        row = self.cart_tree.item(selected[0])["values"]
        item_id = row[0]
        
        cart = self.carts[self.active_cart_index]
        cart["items"] = [item for item in cart["items"] if item["item_id"] != item_id]
        
        self.reload_cart_table()
        self.controller.show_toast("Item Removed", "Product removed from cart.", "warning")

    def modify_cart_qty_popup(self, event):
        """Opens a popup to update the quantity of the double-clicked cart item, validating against stock."""
        selected = self.cart_tree.selection()
        if not selected:
            return
        
        row = self.cart_tree.item(selected[0])["values"]
        item_id = row[0]
        current_qty = int(row[3])
        
        item_info = self.controller.inventory_model.get_by_id(item_id)
        if not item_info:
            return
        max_stock = int(item_info["quantity"])
        
        dialog = tb.Toplevel(self, title="Update Quantity")
        dialog.geometry("320x160")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        tb.Label(dialog, text=f"Update quantity for:\n{item_info['name']}\n(Available stock: {max_stock})", font=("Helvetica", 10), justify="center").pack(pady=10)
        
        var_q = tk.StringVar(value=str(current_qty))
        ent = tb.Entry(dialog, textvariable=var_q, width=10)
        ent.pack()
        ent.focus_set()
        
        btn_frame = tb.Frame(dialog)
        btn_frame.pack(pady=15)
        
        def save_qty():
            try:
                new_q = int(var_q.get())
                if new_q <= 0:
                    Messagebox.show_error("Quantity must be a positive integer.", "Error", parent=dialog)
                    return
                if new_q > max_stock:
                    Messagebox.show_error(f"Stock limit exceeded. Maximum available is {max_stock}.", "Error", parent=dialog)
                    return
                
                # Apply changes
                cart = self.carts[self.active_cart_index]
                for item in cart["items"]:
                    if item["item_id"] == item_id:
                        item["quantity"] = str(new_q)
                        break
                        
                self.reload_cart_table()
                dialog.destroy()
            except ValueError:
                Messagebox.show_error("Invalid quantity. Enter integer digits.", "Error", parent=dialog)
                
        tb.Button(btn_frame, text="Confirm", bootstyle="success", command=save_qty).pack(side="left", padx=5)
        tb.Button(btn_frame, text="Cancel", bootstyle="secondary-outline", command=dialog.destroy).pack(side="left", padx=5)

    def reset_active_cart(self):
        """Confirms with the user then clears all items and buyer details from the active cart."""
        confirm = Messagebox.okcancel("Are you sure you want to discard the active cart details?", "Discard Cart")
        if confirm == "OK":
            self.carts[self.active_cart_index] = self.get_empty_cart_structure()
            self.switch_cart(self.active_cart_index)
            self.controller.show_toast("Cart Reset", "Cart contents cleared.", "info")

    def process_checkout(self):
        """Validates inputs, checks for customer name mismatches, confirms the order total, executes checkout, and generates a PDF receipt."""
        cart = self.carts[self.active_cart_index]
        
        if not cart["items"]:
            Messagebox.show_error("Cannot proceed to checkout. Cart is empty.", "Cart Empty")
            return
            
        phone = self.var_c_phone.get().strip()
        name = self.var_c_name.get().strip()
        address = self.var_c_address.get().strip()
        
        digits_phone = "".join(filter(str.isdigit, phone))
        if len(digits_phone) != 10:
            Messagebox.show_error("Phone number must be exactly 10 digits.", "Validation Error")
            return
        if not name:
            Messagebox.show_error("Customer Name is mandatory.", "Validation Error")
            return
            
        try:
            discount_percent = float(self.var_discount.get())
            if not (0 <= discount_percent <= 100):
                Messagebox.show_error("Discount percentage must be between 0 and 100.", "Validation Error")
                return
        except ValueError:
            Messagebox.show_error("Discount percentage must be a numeric value.", "Validation Error")
            return
            
        # Check if customer exists but has a different name registered
        existing_cust = self.controller.customer_model.get_by_phone(digits_phone)
        if existing_cust:
            existing_name = existing_cust.get("name", "").strip()
            if existing_name and existing_name.lower() != name.lower():
                confirm_name = Messagebox.yesno(
                    f"The phone number '{digits_phone}' is already registered to '{existing_name}'.\n\n"
                    f"Do you want to update the registered name to '{name}'?",
                    "Update Customer Name?"
                )
                if confirm_name == "No":
                    # Restore the original name in fields and active cart, and abort
                    self._updating_customer_fields = True
                    self.var_c_name.set(existing_name)
                    self._updating_customer_fields = False
                    cart["customer"]["name"] = existing_name
                    self.save_carts()
                    return

        # Double confirmation dialog before checkout
        subtotal = sum(int(item["quantity"]) * float(item["price"]) for item in cart["items"])
        grand = round(subtotal * (1 - (discount_percent / 100.0)), 2)
        
        confirm_checkout = Messagebox.okcancel(
            f"Are you sure you want to finalize checkout and print the PDF receipt?\n\n"
            f"Customer: {name} ({digits_phone})\n"
            f"Grand Total: ₹{grand:.2f}",
            "Confirm Checkout"
        )
        if confirm_checkout != "OK":
            return

        success, res = self.controller.transaction_model.checkout(
            digits_phone,
            cart["items"],
            discount_percent
        )
        
        if success:
            invoice_data = res
            invoice_id = invoice_data["invoice_id"]
            
            # Save customer profile
            self.controller.customer_model.add_or_update(digits_phone, name, address)
            
            # Map item names for PDF
            items_list = []
            for item in cart["items"]:
                items_list.append({
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "price_at_sale": item["price"],
                    "quantity": item["quantity"],
                    "subtotal": round(int(item["quantity"]) * float(item["price"]), 2)
                })
                
            # Compile PDF receipt
            pdf_filename = f"{invoice_id}_{invoice_data['timestamp'][:10]}_{invoice_data['timestamp'][11:19].replace(':', '-')}.pdf"
            customer_details = {"phone": digits_phone, "name": name, "address": address}
            
            pdf_path = self.controller.pdf_generator.generate(
                invoice_data,
                items_list,
                customer_details,
                pdf_filename
            )
            
            logger.info(f"Checkout transaction finalized: Invoice {invoice_id}, Customer: {name}")
            self.controller.show_toast("Checkout Finalized", f"PDF Generated. Invoice ID: {invoice_id}", "success")
            
            # Clear active cart structure
            self.carts[self.active_cart_index] = self.get_empty_cart_structure()
            self.switch_cart(self.active_cart_index)
            
            open_pdf = Messagebox.yesno(f"Checkout successful!\nInvoice ID: {invoice_id}\n\nWould you like to open the generated PDF receipt?", "Open Receipt")
            if open_pdf == "Yes":
                try:
                    os.startfile(pdf_path)
                except Exception as e:
                    logger.error(f"Failed to open generated PDF file: {e}")
                    Messagebox.show_error(f"Failed to open PDF file: {e}", "File Error")
        else:
            Messagebox.show_error(res, "Checkout Transaction Failed")

    def clear_customer_fields(self):
        """Clears all buyer information fields and resets the active cart customer data."""
        self._updating_customer_fields = True
        self.var_c_phone.set("")
        self.var_c_name.set("")
        self.var_c_address.set("")
        self.var_c_purchases.set("0")
        self._updating_customer_fields = False
        self.cust_suggestion_container.grid_forget()
        
        # Save change to active cart data structure
        idx = self.active_cart_index
        self.carts[idx]["customer"]["phone"] = ""
        self.carts[idx]["customer"]["name"] = ""
        self.carts[idx]["customer"]["address"] = ""
        self.save_carts()
        
        self.controller.show_toast("Customer Cleared", "Customer details have been cleared from this cart.", "info")

    def update_listbox_colors(self):
        """Applies theme-aware background and foreground colours to both suggestion listboxes."""
        style = self.controller.style
        bg_color = style.colors.get("inputbg") or style.colors.get("bg") or "#ffffff"
        fg_color = style.colors.get("inputfg") or style.colors.get("fg") or "#000000"
        select_bg = style.colors.get("selectbg") or style.colors.get("primary") or "#007fff"
        select_fg = style.colors.get("selectfg") or "#ffffff"
        
        self.list_suggestions.configure(
            bg=bg_color,
            fg=fg_color,
            selectbackground=select_bg,
            selectforeground=select_fg
        )
        
        self.list_cust_suggestions.configure(
            bg=bg_color,
            fg=fg_color,
            selectbackground=select_bg,
            selectforeground=select_fg
        )
