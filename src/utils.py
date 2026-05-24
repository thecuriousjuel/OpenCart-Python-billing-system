# utils.py
import os
import re
import logging
from datetime import datetime
from fpdf import FPDF

# --- DAILY APP LOGGER ---
def setup_logger():
    """Sets up a daily rotating logger."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
    
    logger = logging.getLogger("OpenCartBilling")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Also print logs to stdout for development debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

logger = setup_logger()

# --- FILENAME SANITIZER ---
def sanitize_filename(name):
    """Sanitizes string to be a safe file name across all operating systems."""
    # Replace colons, spaces, and slashes with underscores or dashes
    name = re.sub(r'[\s:/\\?*<>|"]', '_', name)
    return name

# --- PDF INVOICE GENERATOR ---
class PDFInvoiceGenerator:
    @staticmethod
    def generate(invoice_data, items_list, customer_details, filename):
        """
        Generates a professional retail invoice PDF.
        :param invoice_data: dict containing invoice_id, timestamp, subtotal, discount_percent, grand_total
        :param items_list: list of dicts containing item_id, name, price_at_sale, quantity, subtotal
        :param customer_details: dict containing phone, name, address
        :param filename: output filename string
        """
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Color Palette Definition (Modern Flat Navy)
            primary_color = (30, 41, 59) # Slate Grey
            text_dark = (15, 23, 42)
            bg_light = (248, 250, 252)
            
            # Header Block
            pdf.set_fill_color(*primary_color)
            pdf.rect(0, 0, 210, 40, "F")
            
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("helvetica", "B", 20)
            pdf.set_y(10)
            pdf.cell(0, 10, "OpenCart - Python Billing System", align="C")
            pdf.ln(8)
            pdf.set_font("helvetica", "I", 10)
            pdf.cell(0, 10, "Shopping Mall Transaction Invoice", align="C")
            
            # Spacer
            pdf.set_text_color(*text_dark)
            pdf.set_y(50)
            
            # Customer & Invoice Detail Panels
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(95, 6, "INVOICE DETAILS")
            pdf.cell(95, 6, "CUSTOMER DETAILS")
            pdf.ln(7)
            
            # Draw partition line
            pdf.set_draw_color(226, 232, 240)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            
            pdf.set_font("helvetica", "", 10)
            # Detail columns
            details_y = pdf.get_y()
            
            # Left Panel: Invoice metadata
            pdf.set_xy(10, details_y)
            pdf.write(5, f"Invoice ID: ")
            pdf.set_font("helvetica", "B", 10)
            pdf.write(5, f"{invoice_data['invoice_id']}\n")
            pdf.set_font("helvetica", "", 10)
            pdf.write(5, f"Date/Time: {invoice_data['timestamp']}\n")
            
            # Right Panel: Customer metadata
            pdf.set_xy(110, details_y)
            pdf.write(5, f"Name: {customer_details.get('name', 'Walk-in Customer')}\n")
            pdf.set_xy(110, details_y + 5)
            pdf.write(5, f"Phone: {customer_details.get('phone', 'N/A')}\n")
            if customer_details.get("address"):
                pdf.set_xy(110, details_y + 10)
                pdf.write(5, f"Address: {customer_details.get('address')}\n")
                
            pdf.ln(12)
            pdf.set_y(pdf.get_y() + 10)
            
            # Table Header
            pdf.set_fill_color(*primary_color)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("helvetica", "B", 10)
            
            pdf.cell(35, 8, "Item ID", border=1, fill=True, align="C")
            pdf.cell(75, 8, "Item Name", border=1, fill=True)
            pdf.cell(25, 8, "Price", border=1, fill=True, align="R")
            pdf.cell(20, 8, "Qty", border=1, fill=True, align="C")
            pdf.cell(35, 8, "Subtotal", border=1, fill=True, align="R")
            pdf.ln(8)
            
            # Table Rows
            pdf.set_text_color(*text_dark)
            pdf.set_font("helvetica", "", 10)
            
            row_fill = False
            for item in items_list:
                pdf.set_fill_color(*bg_light)
                
                pdf.cell(35, 7, item["item_id"], border=1, fill=row_fill, align="C")
                pdf.cell(75, 7, f" {item['name']}", border=1, fill=row_fill)
                pdf.cell(25, 7, f"Rs. {float(item['price_at_sale']):.2f} ", border=1, fill=row_fill, align="R")
                pdf.cell(20, 7, str(item["quantity"]), border=1, fill=row_fill, align="C")
                pdf.cell(35, 7, f"Rs. {float(item['subtotal']):.2f} ", border=1, fill=row_fill, align="R")
                pdf.ln(7)
                row_fill = not row_fill # Alternate row coloring
                
            pdf.ln(5)
            
            # Divider Line
            pdf.set_draw_color(148, 163, 184)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
            
            # Summary Totals Block
            pdf.set_font("helvetica", "", 10)
            pdf.cell(120, 6, "")
            pdf.cell(35, 6, "Subtotal:", align="R")
            pdf.cell(35, 6, f"Rs. {float(invoice_data['subtotal']):.2f} ", align="R")
            pdf.ln(6)
            
            discount_amount = float(invoice_data['subtotal']) * float(invoice_data['discount_percent']) / 100.0
            pdf.cell(120, 6, "")
            pdf.cell(35, 6, f"Discount ({float(invoice_data['discount_percent'])}%):", align="R")
            pdf.cell(35, 6, f"-Rs. {discount_amount:.2f} ", align="R")
            pdf.ln(6)
            
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(220, 38, 38) # Highlight grand total in red
            pdf.cell(120, 7, "")
            pdf.cell(35, 7, "Grand Total:", align="R")
            pdf.cell(35, 7, f"Rs. {float(invoice_data['grand_total']):.2f} ", align="R")
            pdf.ln(12)
            
            # Terms and Footer Note
            pdf.set_text_color(100, 116, 139)
            pdf.set_font("helvetica", "I", 9)
            pdf.cell(0, 5, "Thank you for shopping with us!", align="C")
            pdf.ln(5)
            pdf.cell(0, 5, "Please retain this invoice for return or exchange claims within 7 days.", align="C")
            pdf.ln(5)
            pdf.cell(0, 5, "Made with <3 by Biswajit", align="C")
            
            # Save Output
            bills_dir = "bills"
            os.makedirs(bills_dir, exist_ok=True)
            sanitized_name = sanitize_filename(filename)
            full_path = os.path.join(bills_dir, sanitized_name)
            
            pdf.output(full_path)
            logger.info(f"PDF Invoice successfully generated at: {full_path}")
            return full_path
            
        except Exception as e:
            logger.error(f"Failed to generate invoice PDF: {e}", exc_info=True)
            raise e
