# OpenCart Python Billing System - Task Tracking Checklist

This document tracks the tasks required to implement the entire billing application. Update the task status as progress is made.

## Task Status Coding
- `[ ]` Not Started
- `[/]` In Progress
- `[x]` Completed

---

## 1. Foundation and Utilities
- [x] Install dependencies: `pip install ttkbootstrap reportlab fpdf2` (via uv)
- [x] Implement `utils.py`:
    - [x] AppLogger setup with daily file rotation (`logs/YYYY-MM-DD.log`).
    - [x] `PDFInvoiceGenerator` class using FPDF2 to draw a clean layout.
    - [x] String sanitization utility for filename-friendly timestamps.

---

## 2. CSV Data Access Layer (database.py)
- [x] Create `CSVDatabase` base helper class utilizing temp files for write-replace integrity.
- [x] Implement `InventoryModel` managing CRUD operations on `inventory.csv` and archiving to `deleted_inventory.csv`.
- [x] Implement `CategoryModel` with auto-sync triggers to maintain `total_items` in `categories.csv`.
- [x] Implement `CustomerModel` managing customer profile suggestions.
- [x] Implement `TransactionModel` ensuring atomic writes to both `transactions.csv` and `transaction_items.csv` alongside inventory count deductions.

---

## 3. UI Framework and Shell (main.py)
- [x] Set up `MainApplication` window inheriting from `tb.Window`.
- [x] Implement configurations loading and dynamic saving of selected themes.
- [x] Build left navigation Sidebar and main content switcher container.
- [x] Integrate non-blocking toast alerts via `ttkbootstrap.toast.ToastNotification`.

---

## 4. UI Views Implementation
- [x] **Home Dashboard:**
    - [x] Dynamic KPI stats (total items, low stock warnings, sales today, revenue today).
    - [x] Quick navigation shortcuts.
- [x] **Inventory Manager:**
    - [x] Search and sortable Item table (Treeview).
    - [x] Insert, Update, and Delete forms with input validators.
    - [x] New Category popup model.
- [x] **Billing / Multi-Cart Console:**
    - [x] Multi-cart tabs/switching setup.
    - [x] Customer phone search & auto-suggest database autocomplete.
    - [x] Real-time item search suggestions dropdown.
    - [x] Cart item grid, modifications (updating quantity, deleting items).
    - [x] Checkout drawer with live calculations (subtotal, discount %, grand total).
    - [x] Finalize order routine (stock verification, CSV records append, PDF generation, Toast notification).
- [x] **Invoice History:**
    - [x] Search invoices by phone or invoice number.
    - [x] Row selector showing purchase details.
    - [x] Reprint/open invoice PDF button.
- [x] **Settings & Logs:**
    - [x] Theme selection dropdown modifying `settings.json` live.
    - [x] Category table management (CRUD categories).
    - [x] Read-only log viewer displaying the tail end of today's log file.

---

## 5. Verification & Testing
- [x] Verify CSV database generation on app start.
- [x] Test input form validators (prices > 0, expiration date > manufacture date, discount bounds, phone normalization).
- [x] Verify thread-safe multi-cart checkouts (stock depletion validation).
- [x] Verify PDF outputs styling and layouts in the `bills/` folder.
- [x] Check logs rolling format correctness.
