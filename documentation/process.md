# OpenCart Python Billing System - Process & Guidelines

This document outlines standard workflows, setup instructions, testing pipelines, and design principles to build, maintain, and verify the application.

## 1. Setup & Installation

### Environment Setup
1.  **Clone / Initialize Workspace:**
    Ensure you are in the workspace root directory containing `main.py`.
2.  **Dependencies Installation:**
    Execute the following commands to install required dependencies:
    ```bash
    pip install ttkbootstrap reportlab fpdf2
    ```
    *(Note: Either `reportlab` or `fpdf2` can be used. This guide defaults to `fpdf2` for ease of use in generating clean, simple invoices).*

### Initial App Boot
Run the application using:
```bash
python main.py
```
On the first boot, the system will automatically create `data/`, `logs/`, and `bills/` folders if they do not exist. It will also generate the empty CSV files with their header configurations and write the default settings JSON file.

---

## 2. Testing & Verification Guide

All developers should perform the following manual and programmatic tests before submitting changes:

### A. Database Verification
1.  Verify that adding a new item creates a row in `data/inventory.csv` with a unique `ITEM-` ID.
2.  Ensure that deleting a row in the UI correctly decrements the count in `data/categories.csv`.
3.  Check that customer autocomplete suggestions are loaded from `data/customers.csv`.

### B. Input Validation Audits
1.  **Price / Quantity Check:** Try entering negative numbers or string alphabets into price/quantity inputs. The UI should block submission and show an error dialog.
2.  **Date Auditing:** Enter an expiration date that is prior to the manufacture date, or formatted as `MM/DD/YYYY`. The system must prompt a format violation.
3.  **Discount Bounds:** Test entering `-5` or `110` in the discount percent field. Checkouts must block.

### C. Multi-Cart Checkout Verification
1.  Add 10 items of "Product X" (available stock: 12) to Cart 1.
2.  Add 5 items of "Product X" to Cart 2.
3.  Proceed to checkout on Cart 1 (reducing available stock of Product X to 2 in the CSV).
4.  Switch to Cart 2 and click checkout. The app must re-query the stock, flag that "Product X only has 2 units available", and abort the checkout.

### D. PDF Layout Inspection
Open the generated PDF under `bills/` and confirm:
1.  The title is "OpenCart - Python Billing System".
2.  The customer phone matches the input.
3.  The item breakdown grid aligns perfectly without clipping margins.
4.  Total, discount, and grand totals are rounded to two decimal places (e.g., `$10.50` instead of `$10.5`).

---

## 3. Developer Standards

*   **Model Isolation (OOP):** Never put raw CSV file access logic inside GUI frame classes. Frame classes must only consume Model interfaces (e.g., `InventoryModel.get_all()`).
*   **Write Safety:** Always use the write-replace utility pattern for file writes to prevent blanking databases during crash interrupts.
*   **Logging:** Every action that mutates state (adding/deleting inventory, customer edits, cart actions, checkouts) must trigger a `logger.info()` record.
*   **Theme Integration:** Do not hardcode widget styles or background colors (e.g., `bg="white"`) in custom widgets. Rely on `ttkbootstrap` dynamic color tokens so they look perfect in both light and dark modes.
