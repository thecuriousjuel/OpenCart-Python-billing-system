# OpenCart — Python Billing System

A fully-featured desktop Point-of-Sale (POS) billing system built with **Python**, **Tkinter / ttkbootstrap**, and **CSV-based flat-file databases**. Designed for small retail environments, it handles product inventory, multi-cart cashier sessions, customer loyalty tracking, invoice history, PDF receipts, and business analytics.

---

## Features

- 📦 **Inventory Manager** — Add, edit, soft-delete products with category filters and sorting.
- 🛒 **Billing Terminal** — Up to 5 concurrent cart sessions with real-time stock checks and PDF invoice generation.
- 👥 **Customer Directory** — Registered customer profiles with purchase count and loyalty spending totals.
- 📜 **Invoice History** — Full transaction ledger with line-item breakdown and PDF receipt regeneration.
- 📊 **Business Analytics** — KPI cards (sales, customers, revenue, stock value), trend line chart, and category pie chart with interactive hover tooltips.
- 🎨 **Dual Theme** — Toggle between **Cosmo** (light) and **Superhero** (dark) modes from the menu bar.
- 🗂️ **CSV Storage** — All data stored in human-readable `.csv` files inside the `data/` folder.

---

## Project Structure

```
OpenCart-Python-billing-system/
├── main.py                   # Lightweight launcher entry point
├── seed.py                   # Database seeder script (creates sample data)
├── settings.json             # Persisted app settings (theme selection)
├── data/                     # All CSV databases (auto-created)
│   ├── categories.csv
│   ├── inventory.csv
│   ├── deleted_inventory.csv
│   ├── customers.csv
│   ├── transactions.csv
│   ├── transaction_items.csv
│   ├── carts.csv
│   └── cart_items.csv
├── bills/                    # Generated PDF invoice receipts
├── logs/                     # Daily rotating application log files
├── documentation/            # Project documentation and diagrams
├── src/
│   ├── database.py           # CSV model classes (Inventory, Customer, Transaction, etc.)
│   ├── utils.py              # Logger setup and PDF invoice generator
│   └── gui/
│       ├── app.py            # Main application window and coordinator
│       ├── home.py           # Dashboard overview page
│       ├── inventory.py      # Inventory management page
│       ├── billing.py        # Billing / cashier terminal page
│       ├── customers.py      # Customer directory page
│       ├── history.py        # Invoice history page
│       ├── analytics.py      # Business analytics page
│       ├── logs.py           # Diagnostics log viewer dialog
│       └── tooltips.py       # Treeview hover tooltip helper
└── tests/
    └── test_backend.py       # Backend model unit tests
```

---

## Prerequisites

- **Python 3.10+**
- **[uv](https://github.com/astral-sh/uv)** — fast Python package manager (recommended)

Install `uv` if you don't have it:

```powershell
pip install uv
```

---

## Installation

### Option A — Using `uv` (recommended)

```powershell
git clone https://github.com/thecuriousjuel/OpenCart-Python-billing-system.git
cd OpenCart-Python-billing-system
uv sync
```

### Option B — Using plain Python & pip

```powershell
git clone https://github.com/thecuriousjuel/OpenCart-Python-billing-system.git
cd OpenCart-Python-billing-system
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux
pip install ttkbootstrap fpdf2
```

> The exact packages required are: `ttkbootstrap`, `fpdf2` (which pulls in `fonttools`, `pillow`, and `defusedxml` automatically).

---

## Seed the Database

Before running the application for the first time, populate the database with realistic sample data (10 categories, 100 products, 50 customers, 100+ transactions, and pre-configured carts).

> ⚠️ **Warning:** Running the seeder will **wipe all existing data** in the `data/` folder and replace it with fresh sample records.

**Using `uv`:**
```powershell
uv run python seed.py
```

**Using plain Python** (with the virtual environment activated):
```powershell
python seed.py
```

The seeder creates:
- **10 product categories** (Beverages, Snacks, Dairy, Bakery, Produce, Meat, Personal Care, Household, Stationery, Electronics)
- **100 products** (10 per category) with realistic prices, manufacture and expiry dates
- **50 fictional customers** with names, phone numbers starting with `0000` or `0123`, and fictional addresses
- **100+ transactions** spanning the last 60 days
- **Pre-loaded cart session data** across 2 active cart terminals
- Low-stock items for testing the stock warning dashboard card

---

## Run the Application

**Using `uv`:**
```powershell
uv run python main.py
```

**Using plain Python** (with the virtual environment activated):
```powershell
python main.py
```

The application window will open maximized. Use the **left sidebar** or the **Navigate** menu to switch between pages.

---

## Run Backend Tests

Execute the test suite to verify all CSV database models are functioning correctly:

**Using `uv`:**
```powershell
uv run python -m unittest tests/test_backend.py
```

**Using plain Python** (with the virtual environment activated):
```powershell
python -m unittest tests/test_backend.py
```

Expected output:
```
Ran 4 tests in ~0.07s

OK
```

---

## Key Workflows

### Adding an Item to Inventory
1. Navigate to **Inventory Manager** from the sidebar.
2. Fill in the product details in the left panel (name, category, price, quantity, dates).
3. Click **Add Product**. The item appears in the table on the right.

### Billing a Customer
1. Navigate to **Billing / Cart** from the sidebar.
2. Type a phone number in the **Buyer Information** section (auto-completes registered customers).
3. Search for items in the **Search & Insert Product** bar and double-click a suggestion.
4. Adjust quantities by double-clicking a cart row.
5. Apply a discount percentage if needed.
6. Click **Confirm Checkout & Print PDF** to finalize the order.

### Viewing Analytics
1. Navigate to **Business Analytics** from the sidebar.
2. Review KPI cards at the top (sales count, revenue, customer count, stock value).
3. Hover over line chart data points and pie chart wedges for interactive tooltips.

---

## Theme Switching

Use the **Theme** menu in the top menu bar to switch between:
- **Light Mode (Cosmo)** — clean white interface
- **Dark Mode (Superhero)** — dark blue-slate interface

---

## License

This project is for educational and personal use.  
Made with ♥ by Biswajit.