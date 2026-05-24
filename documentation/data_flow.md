# OpenCart Billing System — High-Level Data Flow Diagram

This document describes how data moves between the UI views, the backend models, the CSV databases, and the utility components within the OpenCart Python Billing System.

---

## Application Entry Flow

```mermaid
flowchart TD
    A["main.py\n(Launcher)"] --> B["src/gui/app.py\nMainApplication\n(Controller)"]
    B --> B1["Load settings.json\n(theme config)"]
    B --> B2["Instantiate all\nCSV Models"]
    B --> B3["Build Sidebar\n& Menu Bar"]
    B --> B4["Initialize all\nPage Frames"]
    B4 --> C1["HomePage"]
    B4 --> C2["InventoryPage"]
    B4 --> C3["BillingPage"]
    B4 --> C4["CustomersPage"]
    B4 --> C5["HistoryPage"]
    B4 --> C6["AnalyticsPage"]
```

---

## Full System Data Flow

```mermaid
flowchart LR
    subgraph GUI["UI Layer (src/gui/)"]
        direction TB
        HOME["HomePage\nDashboard KPIs"]
        INV["InventoryPage\nProduct Catalog"]
        BILL["BillingPage\nCashier Terminal"]
        CUST["CustomersPage\nDirectory"]
        HIST["HistoryPage\nInvoice Ledger"]
        ANA["AnalyticsPage\nCharts & Metrics"]
    end

    subgraph CTRL["Application Controller (app.py)"]
        SHOW["show_frame()"]
        STRIPE["apply_striped_tags()"]
        THEME["change_theme()"]
        TOAST["show_toast()"]
    end

    subgraph MODELS["Database Models (src/database.py)"]
        CAT["CategoryModel\ncategories.csv"]
        INVM["InventoryModel\ninventory.csv\ndeleted_inventory.csv"]
        CUSTM["CustomerModel\ncustomers.csv"]
        TXM["TransactionModel\ntransactions.csv\ntransaction_items.csv"]
        CARTM["CartModel\ncarts.csv"]
        CARTIM["CartItemModel\ncart_items.csv"]
    end

    subgraph UTILS["Utilities (src/utils.py)"]
        LOG["Logger\nlogs/YYYY-MM-DD.log"]
        PDF["PDFInvoiceGenerator\nbills/*.pdf"]
    end

    subgraph HELPERS["GUI Helpers"]
        TIP["TreeviewTooltip\n(tooltips.py)"]
        LOGS["SystemLogsDialog\n(logs.py)"]
    end

    GUI --> CTRL
    CTRL --> GUI

    HOME --> INVM
    HOME --> TXM

    INV --> CAT
    INV --> INVM

    BILL --> CUSTM
    BILL --> INVM
    BILL --> TXM
    BILL --> CARTM
    BILL --> CARTIM
    BILL --> PDF
    BILL --> LOG

    CUST --> CUSTM
    CUST --> TXM

    HIST --> TXM
    HIST --> CUSTM
    HIST --> PDF
    HIST --> TIP

    ANA --> TXM
    ANA --> CUSTM
    ANA --> INVM

    CTRL --> LOG
    LOGS --> LOG
```

---

## Billing Checkout Flow

```mermaid
sequenceDiagram
    actor Cashier
    participant BillingPage
    participant CustomerModel
    participant TransactionModel
    participant InventoryModel
    participant PDFGenerator
    participant CartModel

    Cashier->>BillingPage: Enter phone number
    BillingPage->>CustomerModel: get_by_phone()
    CustomerModel-->>BillingPage: Return customer profile (auto-fill)

    Cashier->>BillingPage: Search & add items to cart
    BillingPage->>InventoryModel: get_all() / get_by_id()
    InventoryModel-->>BillingPage: Return item details & stock

    Cashier->>BillingPage: Click "Confirm Checkout & Print PDF"
    BillingPage->>BillingPage: Validate phone, name, discount
    BillingPage->>CustomerModel: get_by_phone() (name mismatch check)
    
    alt Name mismatch found
        BillingPage-->>Cashier: Show "Update Customer Name?" dialog
        Cashier->>BillingPage: Confirm Yes / No
    end

    BillingPage-->>Cashier: Show checkout confirmation dialog (grand total)
    Cashier->>BillingPage: Click OK

    BillingPage->>TransactionModel: checkout() (validate stock → deduct → write invoice)
    TransactionModel->>InventoryModel: write_all() (deduct stock)
    TransactionModel-->>BillingPage: Return invoice_id & totals

    BillingPage->>CustomerModel: add_or_update() (save/update profile)
    BillingPage->>PDFGenerator: generate() (create PDF receipt)
    PDFGenerator-->>BillingPage: Return PDF file path

    BillingPage->>CartModel: Clear active cart session
    BillingPage-->>Cashier: Show "Open PDF?" dialog
```

---

## CSV Database Schema

```mermaid
erDiagram
    CATEGORIES {
        string category_name PK
        int total_items
    }

    INVENTORY {
        string item_id PK
        string name
        string category FK
        float price
        int quantity
        date date_added
        date mfg_date
        date expiry_date
    }

    CUSTOMERS {
        string phone PK
        string name
        string address
    }

    TRANSACTIONS {
        string invoice_id PK
        datetime timestamp
        string customer_phone FK
        float subtotal
        float discount_percent
        float grand_total
    }

    TRANSACTION_ITEMS {
        string invoice_id FK
        string item_id FK
        int quantity
        float price_at_sale
    }

    CARTS {
        string cart_index PK
        string invoice_id
        datetime timestamp
        string customer_phone
        string customer_name
        string customer_address
        float discount
    }

    CART_ITEMS {
        string cart_index FK
        string item_id FK
        int quantity
    }

    CATEGORIES ||--o{ INVENTORY : "contains"
    CUSTOMERS ||--o{ TRANSACTIONS : "places"
    TRANSACTIONS ||--|{ TRANSACTION_ITEMS : "has line items"
    INVENTORY ||--o{ TRANSACTION_ITEMS : "sold in"
    CARTS ||--o{ CART_ITEMS : "holds"
    INVENTORY ||--o{ CART_ITEMS : "added to"
```
