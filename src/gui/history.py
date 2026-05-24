# src/gui/history.py
"""
Invoice History Page for the OpenCart Billing System.

Provides a two-panel view: the top panel lists all historical invoices in
a searchable and sortable treeview; the bottom panel shows the itemised
line-items for the selected invoice. Hovering over history rows shows
a floating customer loyalty profile card.
"""
import os
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.dialogs import Messagebox
from src.utils import logger, sanitize_filename
from src.gui.tooltips import TreeviewTooltip

class HistoryPage(tb.Frame):
    """Transaction and invoice history view with invoice detail expansion and row hover tooltips."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Horizontal Split: Top (Search Panel & Header Table) and Bottom (Selected Invoice Detail)
        self.grid_rowconfigure(0, weight=6) # History list
        self.grid_rowconfigure(1, weight=4) # Details box
        self.grid_columnconfigure(0, weight=1)
        
        # Top Frame
        top_frame = tb.Frame(self, padding=20)
        top_frame.grid(row=0, column=0, sticky="nsew")
        
        lbl_title = tb.Label(top_frame, text="Transaction & Invoice History", font=("Helvetica", 16, "bold"), bootstyle="primary")
        lbl_title.pack(anchor="w", pady=(0, 15))
        
        # Filter controls
        filter_frame = tb.Frame(top_frame)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        tb.Label(filter_frame, text="Search Phone or Invoice ID: ").pack(side="left")
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *args: self.reload_history_table())
        tb.Entry(filter_frame, textvariable=self.var_search, width=25).pack(side="left", padx=5)
        
        # Sorting Options
        tb.Label(filter_frame, text="Sort: ").pack(side="left", padx=(15, 5))
        self.var_sort = tk.StringVar(value="timestamp")
        self.combo_sort = tb.Combobox(filter_frame, textvariable=self.var_sort, values=["timestamp", "invoice_id", "subtotal", "discount_percent", "grand_total"], state="readonly", width=15)
        self.combo_sort.pack(side="left", padx=5)
        self.combo_sort.bind("<<ComboboxSelected>>", lambda e: self.reload_history_table())
        
        self.var_sort_desc = tk.BooleanVar(value=True)
        self.btn_sort_dir = tb.Button(
            filter_frame, 
            text="Desc", 
            bootstyle="secondary-outline", 
            command=self.toggle_sort_dir,
            width=5
        )
        self.btn_sort_dir.pack(side="left", padx=5)
        
        # Table of Invoices
        columns = ("invoice_id", "timestamp", "customer_phone", "subtotal", "discount_percent", "grand_total")
        self.tree = tb.Treeview(top_frame, columns=columns, show="headings", bootstyle="primary")
        self.tree.pack(fill="both", expand=True)
        
        self.tree.heading("invoice_id", text="Invoice ID")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("customer_phone", text="Customer Phone")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.heading("discount_percent", text="Discount %")
        self.tree.heading("grand_total", text="Grand Total")
        
        self.tree.column("invoice_id", width=120, anchor="center")
        self.tree.column("timestamp", width=160, anchor="center")
        self.tree.column("customer_phone", width=110, anchor="center")
        self.tree.column("subtotal", width=90, anchor="e")
        self.tree.column("discount_percent", width=80, anchor="center")
        self.tree.column("grand_total", width=110, anchor="e")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_invoice_select)

        # Bottom Frame (Receipt Line Items viewer)
        bottom_frame = tb.Frame(self, padding=20)
        bottom_frame.grid(row=1, column=0, sticky="nsew")
        
        # Bottom Title & actions row
        det_title_row = tb.Frame(bottom_frame)
        det_title_row.pack(fill="x", pady=(0, 10))
        
        self.lbl_details_title = tb.Label(det_title_row, text="Invoice Itemized Details", font=("Helvetica", 12, "bold"))
        self.lbl_details_title.pack(side="left")
        
        self.btn_open_pdf = tb.Button(det_title_row, text="Open generated PDF bill", bootstyle="info", state="disabled", command=self.open_pdf_receipt)
        self.btn_open_pdf.pack(side="right")
        
        # Detail items Treeview
        det_columns = ("item_id", "name", "price", "quantity", "subtotal")
        self.detail_tree = tb.Treeview(bottom_frame, columns=det_columns, show="headings", bootstyle="secondary", height=6)
        self.detail_tree.pack(fill="both", expand=True)
        
        self.detail_tree.heading("item_id", text="Item ID")
        self.detail_tree.heading("name", text="Product Name")
        self.detail_tree.heading("price", text="Price")
        self.detail_tree.heading("quantity", text="Quantity Purchased")
        self.detail_tree.heading("subtotal", text="Subtotal")
        
        self.detail_tree.column("item_id", width=120, anchor="center")
        self.detail_tree.column("name", width=260, anchor="w")
        self.detail_tree.column("price", width=90, anchor="e")
        self.detail_tree.column("quantity", width=80, anchor="center")
        self.detail_tree.column("subtotal", width=110, anchor="e")

        # Initialize Row Hover Tooltip for Customer profiles
        self.tooltip = TreeviewTooltip(self.tree, self.controller, self.get_customer_hover_card)

    def get_customer_hover_card(self, row_vals):
        """Returns a formatted tooltip string with customer loyalty info for the hovered invoice row."""
        if not row_vals or len(row_vals) < 3:
            return None
        phone = row_vals[2]
        if not phone:
            return "Walk-in Customer\nNo loyalty profile linked."
            
        cust = self.controller.customer_model.get_by_phone(phone)
        if not cust:
            return f"Phone: {phone}\nCustomer profile not found."
            
        purchases = self.controller.transaction_model.get_customer_purchase_count(phone)
        spent = self.controller.transaction_model.get_customer_total_spent(phone)
        
        return (
            f"Customer: {cust['name']}\n"
            f"Phone: {phone}\n"
            f"Address: {cust['address'] if cust['address'] else 'N/A'}\n"
            f"Loyalty Purchases: {purchases}\n"
            f"Total Spend: ₹{spent:.2f}"
        )

    def on_show(self):
        """Reloads the invoice history table and clears the detail panel when the page is shown."""
        self.reload_history_table()
        self.detail_tree.delete(*self.detail_tree.get_children())
        self.lbl_details_title.configure(text="Invoice Itemized Details")
        self.btn_open_pdf.configure(state="disabled")

    def toggle_sort_dir(self):
        """Toggles the invoice table sort direction between ascending and descending."""
        if self.var_sort_desc.get():
            self.var_sort_desc.set(False)
            self.btn_sort_dir.configure(text="Asc")
        else:
            self.var_sort_desc.set(True)
            self.btn_sort_dir.configure(text="Desc")
        self.reload_history_table()

    def reload_history_table(self):
        """Reloads the invoice list, applying the current search query and column sort order."""
        self.tree.delete(*self.tree.get_children())
        history = self.controller.transaction_model.get_history()
        
        q = self.var_search.get().strip().lower()
        if q:
            history = [
                tx for tx in history 
                if q in tx["invoice_id"].lower() or q in tx["customer_phone"].lower()
            ]
            
        # Apply sorting
        sort_key = self.var_sort.get()
        is_desc = self.var_sort_desc.get()
        
        if sort_key in ("subtotal", "discount_percent", "grand_total"):
            history.sort(key=lambda x: float(x[sort_key]), reverse=is_desc)
        else:
            history.sort(key=lambda x: x[sort_key].lower(), reverse=is_desc)
            
        for idx, tx in enumerate(history):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                tx["invoice_id"],
                tx["timestamp"],
                tx["customer_phone"],
                f"₹{float(tx['subtotal']):.2f}",
                f"{float(tx['discount_percent'])}%",
                f"₹{float(tx['grand_total']):.2f}"
            ), tags=(tag,))
        self.controller.apply_striped_tags(self.tree)

    def on_invoice_select(self, event):
        """Populates the bottom detail table with line-items for the selected invoice."""
        selected = self.tree.selection()
        if not selected:
            return
        
        row = self.tree.item(selected[0])["values"]
        invoice_id = row[0]
        
        tx_details = self.controller.transaction_model.get_details(invoice_id)
        if tx_details:
            self.detail_tree.delete(*self.detail_tree.get_children())
            self.lbl_details_title.configure(text=f"Itemized Details for Invoice: {invoice_id}")
            
            for idx, item in enumerate(tx_details["items"]):
                tag = "evenrow" if idx % 2 == 0 else "oddrow"
                self.detail_tree.insert("", "end", values=(
                    item["item_id"],
                    item["name"],
                    f"₹{float(item['price_at_sale']):.2f}",
                    item["quantity"],
                    f"₹{float(item['subtotal']):.2f}"
                ), tags=(tag,))
            self.controller.apply_striped_tags(self.detail_tree)
            self.btn_open_pdf.configure(state="normal")

    def open_pdf_receipt(self):
        """Opens the PDF receipt for the selected invoice, or offers to regenerate it if missing."""
        selected = self.tree.selection()
        if not selected:
            return
        
        row = self.tree.item(selected[0])["values"]
        invoice_id = row[0]
        timestamp_str = row[1]
        
        date_str = timestamp_str[:10]
        time_str = timestamp_str[11:19].replace(":", "-")
        pdf_filename = f"{invoice_id}_{date_str}_{time_str}.pdf"
        sanitized_name = sanitize_filename(pdf_filename)
        pdf_path = os.path.join("bills", sanitized_name)
        
        if os.path.exists(pdf_path):
            try:
                os.startfile(pdf_path)
            except Exception as e:
                Messagebox.show_error(f"Failed to open invoice PDF file: {e}", "File Error")
        else:
            tx_details = self.controller.transaction_model.get_details(invoice_id)
            if not tx_details:
                Messagebox.show_error("Transaction metadata not found.", "Database Error")
                return
                
            regenerate = Messagebox.yesno(
                f"Generated PDF file '{pdf_filename}' not found in the bills folder.\nWould you like to regenerate it now?", 
                "File Missing"
            )
            if regenerate == "Yes":
                cust_phone = tx_details["header"]["customer_phone"]
                cust_profile = self.controller.customer_model.get_by_phone(cust_phone)
                cust_details = {
                    "phone": cust_phone,
                    "name": cust_profile["name"] if cust_profile else "Walk-in Customer",
                    "address": cust_profile["address"] if cust_profile else ""
                }
                
                try:
                    new_path = self.controller.pdf_generator.generate(
                        tx_details["header"],
                        tx_details["items"],
                        cust_details,
                        pdf_filename
                    )
                    os.startfile(new_path)
                except Exception as e:
                    Messagebox.show_error(f"Failed to regenerate and open PDF invoice: {e}", "Execution Error")
