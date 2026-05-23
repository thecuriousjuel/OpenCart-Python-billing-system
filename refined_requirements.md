# OpenCart - Python Billing System
## Optimized Blueprint & System Specification for AI Code Generation

This document is a refined, unambiguous specification for a Shopping Mall Billing System built with Python, Tkinter (via `ttkbootstrap`), and CSV database handling. It contains precise schemas, safety checks, architecture definitions, UI layouts, and a core boilerplate to ensure any LLM/AI model can build the application with minimal token consumption and maximum correctness.

---

## 1. Project Specifications

### Tech Stack
*   **Backend:** Python 3.8+ (Strict Object-Oriented Programming).
*   **Frontend:** `ttkbootstrap` wrapper for Python Tkinter (modern styling, dark/light themes, built-in toasts).
*   **Database & Settings:** CSV files (for database) and JSON file (for configurations).
*   **PDF Generation:** `reportlab` or `fpdf2` library.
*   **Logging:** Python standard `logging` library.

### Directory Structure
```text
OpenCart-Billing/
│
├── main.py                 # Application Entry Point & Navigation Controller
├── database.py             # CSV Data Access Layer (CRUD Model Classes)
├── utils.py                # PDF Generator, App Logger, Toast Notifications wrapper
├── data/                   # Database & Configurations Folder
│   ├── settings.json       # Persisted settings (e.g. chosen theme, etc.)
│   ├── inventory.csv       # Inventory Items
│   ├── categories.csv      # Item Categories & Counts
│   ├── customers.csv       # Customer Phone/Name Directory
│   ├── transactions.csv    # Invoice Headers
│   └── transaction_items.csv# Invoice Items Details
├── logs/                   # Daily Log Files (e.g., logs/2026-05-23.log)
└── bills/                  # Generated PDF Bills (e.g., bills/INVO-1234567890_2026-05-23_18-18-00.pdf)
```

---

## 2. Config & Database Schemas

### 1. Persistent Configuration (`data/settings.json`)
Saves configuration details across application reboots.
*   `theme`: String. Theme name from the list of supported `ttkbootstrap` themes (default: `"darkly"`).

### 2. `data/inventory.csv`
Stores the items available for purchase.
*   `item_id`: String. Unique. Format: `ITEM-[10 random digits]` (e.g., `ITEM-9284710482`).
*   `name`: String. Name of the item.
*   `category`: String. Must exist in `categories.csv`.
*   `price`: Float. Price per unit.
*   `quantity`: Integer. Available stock units (e.g., `50`).
*   `date_added`: String. Format: `YYYY-MM-DD`.
*   `mfg_date`: String. Format: `YYYY-MM-DD`.
*   `expiry_date`: String. Format: `YYYY-MM-DD`.

### 3. `data/categories.csv`
Stores item categories and caches the total count of items belonging to each category.
*   `category_name`: String. Unique (e.g., `Vegetables`, `Fruits`, `Meat`, `Dairy`, `Stationery`).
*   `total_items`: Integer. Total number of distinct active items in the inventory mapped to this category. (Must be kept in sync automatically during CRUD inventory operations).

### 4. `data/customers.csv`
Stores buyer records to suggest details on repeat purchases.
*   `phone`: String. Unique key. (e.g., `9876543210`).
*   `name`: String. Customer name.
*   `address`: String. Optional customer address.

### 5. `data/transactions.csv`
Invoice metadata.
*   `invoice_id`: String. Unique. Format: `INVO-[10 random digits]` (e.g., `INVO-3847291048`).
*   `timestamp`: String. Format: `YYYY-MM-DD HH:MM:SS`.
*   `customer_phone`: String. Must map to `customers.csv`.
*   `subtotal`: Float. Total price before discount.
*   `discount_percent`: Float. Discount rate percentage (default: `0.0`).
*   `grand_total`: Float. Final bill amount.

### 6. `data/transaction_items.csv`
Line-item details for invoices.
*   `invoice_id`: String. Foreign key mapping to `transactions.csv`.
*   `item_id`: String. Foreign key mapping to `inventory.csv`.
*   `quantity`: Integer. Units purchased.
*   `price_at_sale`: Float. Price per unit when sold.

---

## 3. UI Navigation & Page Specifications
The application must execute in **Full Screen** mode. It uses a **Sidebar + Main Content Frame** layout. Clicking sidebar links replaces the main content frame.

```text
+-----------------------------------------------------------------------------+
|                                  HEADER                                     |
+-----------------------------------------------------------------------------+
|  SIDEBAR   |                            MAIN CONTENT                        |
|            |                                                                |
| [Home]     |                                                                |
| [Inventory]|                                                                |
| [Billing]  |                                                                |
| [History]  |                                                                |
| [Settings] |                                                                |
|            |                                                                |
|            |                                                                |
+------------+----------------------------------------------------------------+
|                                                     [ Toast Notification ]  |
+-----------------------------------------------------------------------------+
```

### Page 1: Dashboard (Home)
*   **KPI Summary Cards:** Four modern, flat panels showing:
    1.  *Total Items:* Count of unique items in inventory.
    2.  *Low Stock Warning:* Count of items with quantity <= 5.
    3.  *Total Transactions (Today):* Number of bills generated today.
    4.  *Daily Revenue:* Cumulative grand totals of today's sales.
*   **Quick Action Buttons:** Large visual buttons to navigate immediately to:
    *   New Billing Cart
    *   Add New Item
    *   View Logs

### Page 2: Inventory Management
*   **Left Input Form Panel:**
    *   Inputs: Item Name, Price, Date of Manufacture, Date of Expiry.
    *   Category Dropdown: Auto-populated from categories list.
    *   "Quick Create Category" button: Opens a popup dialog to create a new category dynamically.
    *   Actions: "Save Item" (adds item), "Update Item" (edits selected item), "Delete Item".
*   **Right List Grid Panel:**
    *   A `ttk.Treeview` showing all inventory columns.
    *   Sorting controls: Dropdown or column-header click handlers to sort by Category, Price, Date Added, Mfg Date, Expiry Date.
    *   Search Bar: Real-time filtering by item name or ID.

### Page 3: Billing & Cart
*   **Top Multi-Cart Navigation:**
    *   Tabbed interface or simple buttons to switch between multiple concurrent carts (e.g., "Cart 1", "Cart 2").
    *   "New Cart" button to instantiate a new cart (assigning a new unique `INVO-[10-digit]` ID).
*   **Customer Information Box:**
    *   Inputs: Phone Number (Mandatory), Name (Mandatory), Address (Optional).
    *   *Dynamic Autocomplete:* As the biller types the phone number, the app checks `customers.csv`. If a match is found, autocomplete the Name and Address fields.
*   **Item Selection Area:**
    *   Search Input: Type item ID or Name.
    *   Auto-suggest drop-down: Lists matching inventory items showing their available quantities.
    *   Pressing `Enter` or clicking an item adds it to the cart list (default quantity = 1).
    *   *Validation:* Prevent adding item if requested quantity exceeds inventory.
*   **Cart Treeview:**
    *   Columns: Item ID, Item Name, Price, Quantity, Subtotal.
    *   Quantity Modification: Double-clicking an item in the cart allows in-line editing or modal editing of quantity with stock validation.
    *   "Remove Item" button.
*   **Billing Actions Sidebar:**
    *   Displays Subtotal, Discount Input (default `0`), Grand Total. Updates live on any cart change.
    *   "Confirm & Print Bill" Button:
        *   Deducts stock from inventory.
        *   Saves customer details if new.
        *   Writes to transactions & transaction items CSV.
        *   Generates invoice PDF.
        *   Clears cart and launches success Toast.

### Page 4: Transaction History
*   **Search Filters:** Search by Customer Phone Number or Invoice ID.
*   **Transactions Treeview:** Displays columns: Invoice ID, Timestamp, Customer Phone, Total Amount.
*   **Detail Panel:** Selecting a transaction displays its complete line-item breakdown (items, quantities, sale price).
*   **Reprint Option:** "Open PDF" button to open/print the generated invoice.

### Page 5: Settings & Logs
*   **Theme Selection Panel:**
    *   Dropdown selector containing all `ttkbootstrap` themes.
    *   Changing the selection immediately applies the style and overwrites `"theme"` in `data/settings.json`.
*   **Category Management Panel:**
    *   View all categories in a table indicating their respective `total_items`.
    *   Buttons to Add New Category, Edit Category Name, and Delete Category.
*   **Log Viewer:**
    *   Displays the tail end (last 100 lines) of the current day's log file.
    *   Refresh button.

---

## 4. Key Logic & Algorithms

### 1. Unique ID Generation
IDs are generated via Python's standard `random` or `secrets` library to ensure uniqueness:
*   **Item ID:** `f"ITEM-{''.join(random.choices('0123456789', k=10))}"`
*   **Invoice ID:** `f"INVO-{''.join(random.choices('0123456789', k=10))}"`
*   *Validation:* Regenerate if the generated ID already exists in the corresponding CSV file.

### 2. Transaction Integrity & Thread-safe CSV Writes
*   To prevent file corruption during multi-cart writes, use temporary files: write changes to `temp.csv` then rename/replace original database file.
*   When a checkout occurs, the operations must be sequential:
    1. Check inventory quantities of all items in cart. If stock drops below cart quantity, cancel checkout and show an error dialog.
    2. Subtract quantities from `inventory.csv`.
    3. Save customer details to `customers.csv` if phone number does not already exist.
    4. Save invoice details to `transactions.csv` and details to `transaction_items.csv`.
    5. Trigger PDF invoice compilation.

### 3. PDF Invoice Layout File naming
*   Filename format: `INVO-[10-digit-id]_[YYYY-MM-DD]_[HH-MM-SS].pdf`
*   Path: `bills/` folder.
*   PDF content must contain:
    *   Title banner: "OpenCart - Python Billing System".
    *   Invoice metadata (ID, timestamp).
    *   Biller and customer information.
    *   Formatted table showing Item ID, Name, Price, Quantity, Subtotal.
    *   Total, Discount (%), and Grand Total figures.

### 4. Logger Functionality
All CRUD and checkout operations must log events with a standard format:
`[TIMESTAMP] [LEVEL] [USER_ACTION] Message details`
Logs roll over daily into files named `logs/YYYY-MM-DD.log`.

### 5. Theme Settings Persistence
*   **Boot:** Read `data/settings.json`. If missing or parsing fails, write a default `{"theme": "darkly"}` JSON file and launch app with `"darkly"`.
*   **Runtime:** Allow changing themes dynamically. When the user changes the dropdown option on the Settings Page:
    1. Update the root style using `self.style.theme_use(new_theme)` (for `ttkbootstrap` windows: `self.style.theme_use(new_theme)`).
    2. Write the new theme string to `data/settings.json` to persist the setting.

---

## 5. Critical Sanity Checks & Guardrails

To prevent silent failures, database corruption, or application crashes, the implementing code must strictly enforce the following validations:

1.  **CSV Schema Integrity:** 
    *   If a database CSV file is missing or contains corrupt headers, the application must recreate the file with the standard headers rather than crashing on indexing.
2.  **Strict Decimal & Float Precision:**
    *   All pricing calculations must wrap products in `round(value, 2)` or use Python's `decimal.Decimal` to avoid floating-point binary representation artifacts (e.g., `19.99 * 3 = 59.96999999999999`).
3.  **Numerical Boundary Audits:**
    *   *Price:* Must be a positive float (`price > 0`).
    *   *Quantity:* Must be a positive integer (`quantity > 0`).
    *   *Discount:* Must be bounded (`0 <= discount_percent <= 100`).
4.  **Chronological Date Safeguards:**
    *   *Format Enforced:* Enforce `YYYY-MM-DD` via regex or `datetime.strptime`.
    *   *Expiry Date Validation:* `expiry_date` must be strictly later than `mfg_date`, and must be in the future relative to the current local system date.
5.  **Multi-Cart Race Condition Guards:**
    *   Inventory levels must be re-verified from the physical `inventory.csv` file *immediately at checkout*, not just when the item is added to the cart. If another transaction has depleted the items since they were added to the cart, throw a warning dialog and abort the checkout.
6.  **Soft-Delete Safety for Inventory:**
    *   Deleting an item from `inventory.csv` must either:
        *   Be blocked if the item exists in an active (unpaid) cart.
        *   Or use a hidden `is_deleted` column in `inventory.csv` (Soft Delete) so past transaction references do not point to missing keys.
7.  **Category Count Synchronization:**
    *   Adding an item increments `total_items` for its category in `categories.csv`.
    *   Deleting an item decrements `total_items`.
    *   Changing an item's category decrements the count of the old category and increments the new one.
8.  **Phone Number Normalization:**
    *   All phone entries must strip non-digit characters (`+`, `-`, spaces) and validate to standard length bounds (e.g., exactly 10 digits) to prevent lookup errors during autocomplete queries.
9.  **File System Sanitization:**
    *   Timestamps in generated PDF filenames must not contain characters invalid for filenames (e.g., replaces `:` with `-` or `_`).

---

## 6. Implementation Starter Template

Provide this code directly to the model as the base template. It leverages `ttkbootstrap` to instantly style standard Tkinter widgets, initializes files, reads/saves themes dynamically, and configures navigation.

### Supported Themes in `ttkbootstrap`
*   **Light Themes:** `cosmo`, `flatly`, `journal`, `litera`, `lumen`, `minty`, `pulse`, `sandstone`, `united`, `yeti`, `simplex`, `morph`
*   **Dark Themes:** `solar`, `cyborg`, `darkly`, `superhero`, `vapor`, `charcoal`

```python
# main_boilerplate.py
import os
import csv
import json
import logging
import random
import time
from datetime import datetime
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.toast import ToastNotification

# --- CONFIG & DIRECTORY SETUP ---
DIRS = ["data", "logs", "bills"]
for d in DIRS:
    os.makedirs(d, exist_ok=True)

SETTINGS_FILE = "data/settings.json"

# Initialize CSV Files with Headers if missing
CSV_HEADERS = {
    "data/inventory.csv": ["item_id", "name", "category", "price", "quantity", "date_added", "mfg_date", "expiry_date"],
    "data/categories.csv": ["category_name", "total_items"],
    "data/customers.csv": ["phone", "name", "address"],
    "data/transactions.csv": ["invoice_id", "timestamp", "customer_phone", "subtotal", "discount_percent", "grand_total"],
    "data/transaction_items.csv": ["invoice_id", "item_id", "quantity", "price_at_sale"]
}

for filepath, headers in CSV_HEADERS.items():
    if not os.path.exists(filepath):
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

# --- DAILY LOGGER ---
log_file = os.path.join("logs", f"{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger()
logger.info("Application starting...")

# --- CONFIGURATION LOAD/SAVE ---
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                config = json.load(f)
                if "theme" in config:
                    return config
        except Exception as e:
            logger.error(f"Error reading configuration file: {e}")
    
    default_config = {"theme": "darkly"}
    save_settings(default_config)
    return default_config

def save_settings(config):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logger.error(f"Error writing configuration file: {e}")

# --- MAIN APP INTERFACE CONSOLE ---
class MainApplication(tb.Window):
    def __init__(self):
        # Load persisted settings
        self.config = load_settings()
        initial_theme = self.config.get("theme", "darkly")
        
        super().__init__(
            title="OpenCart - Python Billing System",
            themename=initial_theme, # Apply saved theme on boot
            size=(1200, 800),
            position=(100, 100),
            state="zoomed"      # Full screen
        )
        
        # Setup Main Frame Structure
        self.sidebar = tb.Frame(self, bootstyle="dark", width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        self.content_area = tb.Frame(self, bootstyle="secondary")
        self.content_area.pack(side="right", expand=True, fill="both")
        
        # Initialize Page States
        self.pages = {}
        for PageClass in (HomePage, InventoryPage, BillingPage, HistoryPage, SettingsPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=self.content_area, controller=self)
            self.pages[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        self.build_sidebar()
        self.show_frame("HomePage")
        
    def build_sidebar(self):
        brand = tb.Label(
            self.sidebar, 
            text="OpenCart\nBilling", 
            bootstyle="inverse-dark", 
            font=("Helvetica", 18, "bold"), 
            justify="center",
            padding=(0, 20)
        )
        brand.pack(fill="x")
        
        nav_items = [
            ("Home Dashboard", "HomePage"),
            ("Inventory Manager", "InventoryPage"),
            ("Billing / Cart", "BillingPage"),
            ("Invoice History", "HistoryPage"),
            ("Settings & Logs", "SettingsPage")
        ]
        
        for text, frame_name in nav_items:
            btn = tb.Button(
                self.sidebar, 
                text=text, 
                bootstyle="light-outline", 
                command=lambda f=frame_name: self.show_frame(f)
            )
            btn.pack(fill="x", padx=15, pady=10)
            
    def show_frame(self, page_name):
        frame = self.pages[page_name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

    def change_theme(self, new_theme):
        # Update current application styling theme
        self.style.theme_use(new_theme)
        # Update settings file
        self.config["theme"] = new_theme
        save_settings(self.config)
        logger.info(f"App theme changed to {new_theme}")

# --- BASE PAGES (PLACEHOLDERS TO BE IMPLEMENTED) ---
class HomePage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bootstyle="secondary")
        self.controller = controller
        lbl = tb.Label(self, text="Home Dashboard Overview", font=("Helvetica", 20, "bold"), bootstyle="inverse-secondary")
        lbl.pack(pady=20)
        
        btn = tb.Button(
            self, 
            text="Simulate Toast", 
            bootstyle="success", 
            command=self.trigger_toast
        )
        btn.pack()

    def trigger_toast(self):
        toast = ToastNotification(
            title="Notification",
            message="Welcome back, Biller!",
            duration=3000,
            position=(950, 750, 'se')
        )
        toast.show_toast()

    def on_show(self):
        pass

class InventoryPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bootstyle="secondary")
        self.controller = controller
        lbl = tb.Label(self, text="Inventory Management Panel", font=("Helvetica", 20, "bold"), bootstyle="inverse-secondary")
        lbl.pack(pady=20)

class BillingPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bootstyle="secondary")
        self.controller = controller
        lbl = tb.Label(self, text="Billing & Multi-Cart System", font=("Helvetica", 20, "bold"), bootstyle="inverse-secondary")
        lbl.pack(pady=20)

class HistoryPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bootstyle="secondary")
        self.controller = controller
        lbl = tb.Label(self, text="Transaction & Invoice History", font=("Helvetica", 20, "bold"), bootstyle="inverse-secondary")
        lbl.pack(pady=20)

class SettingsPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bootstyle="secondary")
        self.controller = controller
        
        lbl = tb.Label(self, text="Settings & Daily Log Viewer", font=("Helvetica", 20, "bold"), bootstyle="inverse-secondary")
        lbl.pack(pady=20)
        
        # Theme Selector Widget Group
        theme_frame = tb.Frame(self, padding=10)
        theme_frame.pack(fill="x", padx=20, pady=10)
        
        theme_lbl = tb.Label(theme_frame, text="Select Application Theme:", font=("Helvetica", 12))
        theme_lbl.pack(side="left", padx=10)
        
        # Comprehensive list of standard ttkbootstrap themes
        self.themes = [
            # Light Themes
            "cosmo", "flatly", "journal", "litera", "lumen", "minty", 
            "pulse", "sandstone", "united", "yeti", "simplex", "morph",
            # Dark Themes
            "solar", "cyborg", "darkly", "superhero", "vapor", "charcoal"
        ]
        
        # Combobox selector linked to active controller configuration
        current_theme = self.controller.config.get("theme", "darkly")
        self.theme_combo = tb.Combobox(theme_frame, values=self.themes, state="readonly", width=15)
        self.theme_combo.set(current_theme)
        self.theme_combo.pack(side="left", padx=10)
        
        # Bind change event
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)

    def on_theme_change(self, event):
        selected_theme = self.theme_combo.get()
        self.controller.change_theme(selected_theme)
        
        toast = ToastNotification(
            title="Theme Updated",
            message=f"Theme set to '{selected_theme}' and saved successfully.",
            duration=2500,
            position=(950, 750, 'se')
        )
        toast.show_toast()

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
```

---

## 7. Optimization Rules for the Target AI Builder
When using this blueprint to generate the final application:
1.  **Do Not Explain:** Generate code directly; skip introductions, code explanations, or usage notes.
2.  **Modular Implementation:** Put CSV models in `database.py`, PDF generation/Logger in `utils.py`, and screens/main execution in `main.py`.
3.  **Strict Error Handling:** Wrap all CSV read/write operations in `try-except` blocks. If files are locked or inaccessible, gracefully log it and display a Toast alert instead of crashing.
4.  **No Mock Lists:** Pull all category lists, customer detail checks, and item details directly from the CSV databases. Do not hardcode lists.
