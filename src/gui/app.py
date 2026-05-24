# src/gui/app.py
"""
Main application controller for the OpenCart Billing System.

Defines the MainApplication window which acts as the central coordinator:
initialises all database models, builds the sidebar navigation,
manages page frame switching, handles theme toggling, and exposes
shared helper utilities (toast notifications, striped table tags, etc.).
"""
import os
import json
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import ToastNotification

from src.database import InventoryModel, CategoryModel, CustomerModel, TransactionModel, CartModel, CartItemModel
from src.utils import logger, PDFInvoiceGenerator

# Import page views
from src.gui.home import HomePage
from src.gui.inventory import InventoryPage
from src.gui.billing import BillingPage
from src.gui.customers import CustomersPage
from src.gui.history import HistoryPage
from src.gui.analytics import AnalyticsPage
from src.gui.logs import show_logs_dialog

class MainApplication(tb.Window):
    """Root application window and central controller for all GUI pages."""

    def __init__(self):
        # Load persisted settings from ROOT folder
        self.config_file = "settings.json"
        self.config = self.load_settings()
        initial_theme = self.config.get("theme", "cosmo")
        if initial_theme not in ["cosmo", "superhero"]:
            initial_theme = "cosmo"
            
        super().__init__(
            title="OpenCart - Python Billing System",
            themename=initial_theme,
            size=(1300, 850),
            position=(50, 50)
        )
        self.state("zoomed") # Maximize by default
        
        # Instantiate CSV models
        self.inventory_model = InventoryModel()
        self.category_model = CategoryModel()
        self.customer_model = CustomerModel()
        self.transaction_model = TransactionModel()
        self.cart_model = CartModel()
        self.cart_item_model = CartItemModel()
        
        # Instantiate PDF receipt generator utility
        self.pdf_generator = PDFInvoiceGenerator
        
        # Configure global treeview style rules (boost font size to 12, row height to 35)
        self.apply_treeview_styles()
        
        # Build core layout container - adapt background to theme
        self.sidebar = tb.Frame(self, width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        self.content_area = tb.Frame(self)
        self.content_area.pack(side="right", expand=True, fill="both")
        
        # Initialize page dictionaries
        self.pages = {}
        self.current_page = None
        
        # Initialize frames
        for PageClass in (HomePage, InventoryPage, BillingPage, CustomersPage, HistoryPage, AnalyticsPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=self.content_area, controller=self)
            self.pages[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        self.build_sidebar()
        self.show_frame("HomePage")
        
        # Setup Menu Bar
        self.menu_bar = tk.Menu(self)
        
        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Exit Application", command=self.destroy)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Navigate Menu
        nav_menu = tk.Menu(self.menu_bar, tearoff=0)
        nav_menu.add_command(label="Home Dashboard", command=lambda: self.show_frame("HomePage"))
        nav_menu.add_command(label="Inventory Manager", command=lambda: self.show_frame("InventoryPage"))
        nav_menu.add_command(label="Billing Terminal", command=lambda: self.show_frame("BillingPage"))
        nav_menu.add_command(label="Customer Details", command=lambda: self.show_frame("CustomersPage"))
        nav_menu.add_command(label="Transaction History", command=lambda: self.show_frame("HistoryPage"))
        nav_menu.add_command(label="Business Analytics", command=lambda: self.show_frame("AnalyticsPage"))
        self.menu_bar.add_cascade(label="Navigate", menu=nav_menu)
        
        # Diagnostics Logs Menu Action
        diagnostics_menu = tk.Menu(self.menu_bar, tearoff=0)
        diagnostics_menu.add_command(label="View Diagnostic Logs", command=self.show_logs_dialog)
        self.menu_bar.add_cascade(label="Diagnostics", menu=diagnostics_menu)
        
        # Theme Menu
        theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        theme_menu.add_command(label="Light Mode (Cosmo)", command=lambda: self.change_theme("cosmo"))
        theme_menu.add_command(label="Dark Mode (Superhero)", command=lambda: self.change_theme("superhero"))
        self.menu_bar.add_cascade(label="Theme", menu=theme_menu)
        
        # Help Menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.configure(menu=self.menu_bar)
        
        logger.info("Main Application layout loaded successfully.")

    def show_about_dialog(self):
        """Displays a simple informational About dialog box."""
        Messagebox.show_info(
            title="About Application",
            message="OpenCart - Python Billing System\nVersion 1.0\n\nMade with ♥ by Biswajit"
        )

    def load_settings(self):
        """Reads and returns persisted settings from settings.json. Falls back to defaults on failure."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read settings: {e}")
        # Default fallback
        default_config = {"theme": "cosmo"}
        self.save_settings(default_config)
        return default_config

    def save_settings(self, config):
        """Serialises the given config dict to settings.json."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def apply_treeview_styles(self):
        """Applies consistent font size and row height to all ttkbootstrap Treeview style variants."""
        bootstyles = ["", "primary", "secondary", "success", "info", "warning", "danger", "light", "dark"]
        for bs in bootstyles:
            style_name = f"{bs}.Treeview" if bs else "Treeview"
            heading_style = f"{bs}.Treeview.Heading" if bs else "Treeview.Heading"
            self.style.configure(style_name, font=("Helvetica", 12), rowheight=35)
            self.style.configure(heading_style, font=("Helvetica", 12, "bold"), padding=(5, 5))

    def apply_striped_tags(self, tree):
        """Configures alternating row background colours on a Treeview based on the active theme."""
        theme = self.config.get("theme", "cosmo")
        is_dark = (theme == "superhero")
        odd_bg = "#2b3e50" if is_dark else "#ffffff"
        even_bg = "#20374C" if is_dark else "#F8F9FA"
        fg = "#ffffff" if is_dark else "#373a3c"
        tree.tag_configure("oddrow", background=odd_bg, foreground=fg)
        tree.tag_configure("evenrow", background=even_bg, foreground=fg)

    def build_sidebar(self):
        """Constructs the left sidebar with brand label, navigation buttons, and footer."""
        brand = tb.Label(
            self.sidebar, 
            text="OpenCart Billing", 
            bootstyle="primary", 
            font=("Helvetica", 16, "bold"), 
            justify="center",
            padding=(0, 25)
        )
        brand.pack(fill="x")
        
        div = tb.Separator(self.sidebar)
        div.pack(fill="x", padx=10, pady=5)
        
        nav_items = [
            ("Home Dashboard", "HomePage"),
            ("Inventory Manager", "InventoryPage"),
            ("Billing / Cart", "BillingPage"),
            ("Customer Details", "CustomersPage"),
            ("Invoice History", "HistoryPage"),
            ("Business Analytics", "AnalyticsPage")
        ]
        
        self.nav_buttons = {}
        for text, frame_name in nav_items:
            btn = tb.Button(
                self.sidebar, 
                text=text, 
                bootstyle="primary-outline", 
                command=lambda f=frame_name: self.show_frame(f)
            )
            btn.pack(fill="x", padx=15, pady=8)
            self.nav_buttons[frame_name] = btn

        # Sidebar Footer
        self.footer_frame = tb.Frame(self.sidebar)
        self.footer_frame.pack(side="bottom", fill="x", pady=20)
        
        inner_footer = tb.Frame(self.footer_frame)
        inner_footer.pack(anchor="center")
        
        lbl1 = tb.Label(inner_footer, text="Made with ", font=("Helvetica", 10, "italic"))
        lbl1.pack(side="left")
        
        lbl_heart = tb.Label(inner_footer, text="♥", font=("Helvetica", 10), foreground="red")
        lbl_heart.pack(side="left")
        
        lbl2 = tb.Label(inner_footer, text=" by Biswajit", font=("Helvetica", 10, "italic"))
        lbl2.pack(side="left")

    def show_frame(self, page_name):
        """Raises the specified page frame to the front and highlights its sidebar button, then calls on_show()."""
        frame = self.pages[page_name]
        frame.tkraise()
        self.current_page = page_name
        
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(bootstyle="primary")
            else:
                btn.configure(bootstyle="primary-outline")
                
        if hasattr(frame, "on_show"):
            frame.on_show()

    def change_theme(self, new_theme):
        """Switches the application theme, persists the choice, and refreshes all visible page styles."""
        self.style.theme_use(new_theme)
        
        # Save config
        self.config["theme"] = new_theme
        self.save_settings(self.config)
        
        # Re-apply Treeview style rules because changing theme resets them
        self.apply_treeview_styles()
        
        logger.info(f"Theme successfully updated to {new_theme}")
        
        # Re-apply stripes/colors for widgets on the active/instantiated pages
        for page_name, frame in self.pages.items():
            if self.current_page == page_name:
                # Force refresh of currently showing page first
                if hasattr(frame, "on_show"):
                    frame.on_show()
            else:
                # Refresh off-screen tables when shown later
                if hasattr(frame, "reload_table"):
                    frame.reload_table()
                elif hasattr(frame, "reload_tree"):
                    frame.reload_tree()
                elif hasattr(frame, "reload_history_table"):
                    frame.reload_history_table()
                    
        self.show_toast("Theme Changed", f"Successfully loaded '{new_theme}' theme.", "success")

    def show_logs_dialog(self):
        """Opens the system diagnostics log viewer modal window."""
        show_logs_dialog(self)

    def show_toast(self, title, message, level="info"):
        """Displays a brief toast notification at the bottom-right corner of the screen."""
        bootstyle = SUCCESS if level == "success" else (DANGER if level == "error" else INFO)
        toast = ToastNotification(
            title=title,
            message=message,
            duration=3000,
            bootstyle=bootstyle,
            position='se'
        )
        toast.show_toast()
