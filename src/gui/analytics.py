# src/gui/analytics.py
"""
Business Analytics Page for the OpenCart Billing System.

Displays aggregated KPI cards (sales count, customer count, revenue,
total items in stock, inventory value), a daily revenue trend line chart,
and a category stock distribution pie chart. All charts support
interactive mouse-hover tooltips with boundary-aware positioning.
"""
import tkinter as tk
import ttkbootstrap as tb
import math
from datetime import datetime

class AnalyticsPage(tb.Frame):
    """Business performance analytics page with live KPI cards and interactive canvas charts."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Main Header
        header = tb.Label(
            self, 
            text="Business Analytics & Metrics Dashboard", 
            font=("Helvetica", 20, "bold"), 
            bootstyle="primary",
            padding=(20, 20)
        )
        header.pack(anchor="w")
        
        # Top KPI bar container
        self.kpi_frame = tb.Frame(self, padding=(20, 0, 20, 10))
        self.kpi_frame.pack(fill="x")
        self.kpi_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        # Metrics Cards
        self.lbl_sales_done = self.create_kpi_card("Sales Invoices (All Time)", "0", 0)
        self.lbl_cust_db = self.create_kpi_card("Registered Customers", "0", 1)
        self.lbl_revenue_all = self.create_kpi_card("Revenue (All Time)", "₹0.00", 2)
        self.lbl_total_items = self.create_kpi_card("Total Items in Stock", "0", 3)
        self.lbl_inventory_val = self.create_kpi_card("Inventory Value", "₹0.00", 4)
        
        # Graphs container
        self.graphs_frame = tb.Frame(self, padding=20)
        self.graphs_frame.pack(fill="both", expand=True)
        self.graphs_frame.grid_columnconfigure((0, 1), weight=1)
        self.graphs_frame.grid_rowconfigure((0, 1), weight=1)
        
        # Canvas 1: Daily Revenue Trend (Line Chart) - spans full width
        self.canvas_rev = tk.Canvas(self.graphs_frame, height=180, highlightthickness=0)
        self.canvas_rev.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Canvas 3: Category Share (Pie Chart) - spans full width
        self.canvas_pie = tk.Canvas(self.graphs_frame, height=240, highlightthickness=0)
        self.canvas_pie.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Bind resize configuration to redraw graphs dynamically
        self.graphs_frame.bind("<Configure>", lambda event: self.draw_graphs())
        
        # Bind motion events for hover tooltips
        self.canvas_rev.bind("<Motion>", self.hover_line_chart)
        self.canvas_rev.bind("<Leave>", lambda e: self.hide_tooltip(self.canvas_rev))
        
        self.canvas_pie.bind("<Motion>", self.hover_pie_chart)
        self.canvas_pie.bind("<Leave>", lambda e: self.hide_tooltip(self.canvas_pie))
        
        # Hover state caches
        self.line_points_cache = []
        self.pie_slices_cache = []
        self.pie_center = (0, 0, 0) # cx, cy, radius
        
        # Tooltip overlays cache
        self.tooltips = {} # canvas -> (rect_id, text_id)

    def create_kpi_card(self, title, initial_val, column):
        """Creates a KPI labelframe card widget in the top metrics bar at the given column index."""
        card = tb.Labelframe(self.kpi_frame, text=title, padding=15)
        card.grid(row=0, column=column, padx=10, sticky="nsew")
        
        lbl_val = tb.Label(card, text=initial_val, font=("Helvetica", 16, "bold"), bootstyle="primary")
        lbl_val.pack(anchor="center")
        return lbl_val

    def on_show(self):
        # Update metrics values
        invoices = self.controller.transaction_model.read_all()
        customers = self.controller.customer_model.read_all()
        active_items = self.controller.inventory_model.get_all()
        
        total_sales = len(invoices)
        total_customers = len(customers)
        total_revenue = sum(float(tx["grand_total"]) for tx in invoices)
        
        total_items = 0
        inventory_value = 0.0
        for item in active_items:
            try:
                qty = int(item.get("quantity", 0))
                price = float(item.get("price", 0.0))
                total_items += qty
                inventory_value += price * qty
            except (ValueError, TypeError):
                pass
        
        self.lbl_sales_done.configure(text=str(total_sales))
        self.lbl_cust_db.configure(text=str(total_customers))
        self.lbl_revenue_all.configure(text=f"₹{total_revenue:.2f}")
        self.lbl_total_items.configure(text=str(total_items))
        self.lbl_inventory_val.configure(text=f"₹{inventory_value:.2f}")
        
        self.draw_graphs()

    def draw_graphs(self):
        """Redraws all canvas charts (line and pie) based on current transaction and inventory data."""
        w_rev = self.canvas_rev.winfo_width()
        h_rev = self.canvas_rev.winfo_height()
        w_pie = self.canvas_pie.winfo_width()
        h_pie = self.canvas_pie.winfo_height()
        
        if w_rev < 10 or h_rev < 10 or w_pie < 10 or h_pie < 10:
            return
            
        # Get theme colors
        style = self.controller.style
        bg_color = style.colors.get("bg") or "#ffffff"
        fg_color = style.colors.get("fg") or "#000000"
        
        is_dark = (self.controller.config.get("theme", "cosmo") == "superhero")
        grid_color = "#343a40" if is_dark else "#e9ecef"
        text_color = fg_color
        line_color = "#37b24d" # Success Green
        
        # Clear canvases
        self.canvas_rev.delete("all")
        self.canvas_pie.delete("all")
        self.tooltips.clear()
        
        # Set backgrounds
        self.canvas_rev.configure(bg=bg_color)
        self.canvas_pie.configure(bg=bg_color)
        
        # Load transaction data
        history = self.controller.transaction_model.get_history()
        
        # Group revenue by date
        revenue_by_date = {}
        for tx in history:
            date_str = tx["timestamp"][:10]
            revenue_by_date[date_str] = revenue_by_date.get(date_str, 0.0) + float(tx["grand_total"])
            
        all_dates = sorted(list(revenue_by_date.keys()))
        last_7_dates = all_dates[-7:] if len(all_dates) >= 7 else all_dates
        
        # 1. DRAW REVENUE TREND (LINE CHART)
        pad_left, pad_right, pad_top, pad_bottom = 45, 15, 20, 45
        self.canvas_rev.create_text(w_rev/2, h_rev - 5, text="Daily Revenue Trend", fill=text_color, font=("Helvetica", 10, "bold"), anchor="s")
        
        self.line_points_cache = []
        if not last_7_dates:
            self.canvas_rev.create_text(w_rev/2, h_rev/2, text="No Sales Data Available", fill=text_color, font=("Helvetica", 9, "italic"))
        else:
            max_rev = max(revenue_by_date.get(d, 0.0) for d in last_7_dates)
            if max_rev <= 0.0:
                max_rev = 1.0
            
            # Axes
            self.canvas_rev.create_line(pad_left, h_rev - pad_bottom, w_rev - pad_right, h_rev - pad_bottom, fill=text_color, width=1)
            self.canvas_rev.create_line(pad_left, pad_top, pad_left, h_rev - pad_bottom, fill=text_color, width=1)
            
            # Y ticks & Grid Lines
            for tick in [0.0, max_rev/2.0, max_rev]:
                y_pos = h_rev - pad_bottom - (tick / max_rev) * (h_rev - pad_top - pad_bottom)
                self.canvas_rev.create_line(pad_left, y_pos, w_rev - pad_right, y_pos, fill=grid_color, dash=(2, 2))
                self.canvas_rev.create_text(pad_left - 5, y_pos, text=f"₹{tick:.0f}", fill=text_color, font=("Helvetica", 8), anchor="e")
                
            # Plot Points & Lines
            points_coords = []
            x_step = (w_rev - pad_left - pad_right) / max(1, len(last_7_dates) - 1) if len(last_7_dates) > 1 else (w_rev - pad_left - pad_right)
            
            for i, date_str in enumerate(last_7_dates):
                x = pad_left + i * x_step if len(last_7_dates) > 1 else pad_left + (w_rev - pad_left - pad_right)/2
                val = revenue_by_date.get(date_str, 0.0)
                y = h_rev - pad_bottom - (val / max_rev) * (h_rev - pad_top - pad_bottom)
                points_coords.append((x, y))
                
                # Cache for hover motion lookup
                self.line_points_cache.append((x, y, date_str, val))
                
                # X Labels
                self.canvas_rev.create_text(x, h_rev - pad_bottom + 12, text=date_str[5:], fill=text_color, font=("Helvetica", 8), anchor="center")
                self.canvas_rev.create_line(x, pad_top, x, h_rev - pad_bottom, fill=grid_color, dash=(2, 2))
                
            if len(points_coords) > 1:
                flat_points = [coord for pt in points_coords for coord in pt]
                self.canvas_rev.create_line(flat_points, fill=line_color, width=2)
            for x, y in points_coords:
                self.canvas_rev.create_oval(x-4, y-4, x+4, y+4, fill=line_color, outline=text_color, tags="marker")

        # 3. DRAW CATEGORY SHARE (PIE CHART)
        self.canvas_pie.create_text(w_pie/2, 10, text="Category Share (Stock Distribution)", fill=text_color, font=("Helvetica", 11, "bold"), anchor="n")
        
        active_items = self.controller.inventory_model.get_all()
        cat_counts = {}
        for item in active_items:
            cat = item["category"]
            cat_counts[cat] = cat_counts.get(cat, 0) + int(item["quantity"])
            
        total_items = sum(cat_counts.values())
        self.pie_slices_cache = []
        
        if total_items <= 0:
            self.canvas_pie.create_text(w_pie/2, h_pie/2, text="No Inventory Items Available", fill=text_color, font=("Helvetica", 10, "italic"))
        else:
            sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
            
            diameter = min(h_pie - 50, w_pie / 2.2)
            cx = diameter / 2 + 30
            cy = h_pie / 2 + 10
            x1, y1 = cx - diameter/2, cy - diameter/2
            x2, y2 = cx + diameter/2, cy + diameter/2
            
            # Cache center and radius for polar lookup
            self.pie_center = (cx, cy, diameter / 2)
            
            pie_colors = ["#4dabf7", "#37b24d", "#f783ac", "#f59f00", "#748ffc", "#f06595", "#3bc9db", "#ae3ec9"]
            
            start_angle = 0.0
            lx = diameter + 70
            
            for i, (cat, qty) in enumerate(sorted_cats):
                percentage = (qty / total_items) * 100.0
                angle = (qty / total_items) * 360.0
                color = pie_colors[i % len(pie_colors)]
                
                # Draw wedge
                self.canvas_pie.create_arc(x1, y1, x2, y2, start=start_angle, extent=angle, fill=color, outline=text_color)
                
                # Cache start & end angles for wedge detection
                self.pie_slices_cache.append((start_angle, start_angle + angle, cat, qty, percentage))
                start_angle += angle
                
                # Draw legend list
                if i < 7:
                    ly = 35 + i * 22
                    self.canvas_pie.create_rectangle(lx, ly, lx + 12, ly + 12, fill=color, outline=text_color)
                    legend_text = f"{cat}: {qty} units ({percentage:.1f}%)"
                    self.canvas_pie.create_text(lx + 20, ly + 6, text=legend_text, fill=text_color, font=("Helvetica", 9), anchor="w")
                    
            if len(sorted_cats) > 7:
                self.canvas_pie.create_text(lx, 35 + 7 * 22, text="... and more categories", fill=text_color, font=("Helvetica", 8, "italic"), anchor="w")

    # --- CANVAS GRAPH HOVER INTERACTION LOGIC ---
    
    def hover_line_chart(self, event):
        """Handles mouse motion over the revenue trend line chart, showing a tooltip near close data points."""
        mx, my = event.x, event.y
        hover_match = None
        
        # Check proximity to points
        for (x, y, date_str, val) in self.line_points_cache:
            dist = math.sqrt((x - mx)**2 + (y - my)**2)
            if dist < 8.0:
                hover_match = f"Date: {date_str}\nRevenue: ₹{val:.2f}"
                break
                
        if hover_match:
            self.show_tooltip(self.canvas_rev, hover_match, mx, my)
        else:
            self.hide_tooltip(self.canvas_rev)

    def hover_pie_chart(self, event):
        """Handles mouse motion over the pie chart, detecting wedge hit using polar coordinate math."""
        mx, my = event.x, event.y
        cx, cy, r = self.pie_center
        if r <= 0:
            return
            
        dx = mx - cx
        dy = cy - my # invert Y Cartesian
        dist = math.sqrt(dx*dx + dy*dy)
        
        hover_match = None
        if dist <= r:
            # Polar coordinates angle conversion
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            if angle_deg < 0:
                angle_deg += 360.0
                
            # Lookup wedge match
            for (start_ang, end_ang, cat, qty, pct) in self.pie_slices_cache:
                # Handle angle wrap-around
                if start_ang <= angle_deg < end_ang or start_ang <= angle_deg + 360.0 < end_ang:
                    hover_match = f"Category: {cat}\nStock: {qty} units\nShare: {pct:.1f}%"
                    break
                    
        if hover_match:
            self.show_tooltip(self.canvas_pie, hover_match, mx, my)
        else:
            self.hide_tooltip(self.canvas_pie)

    # --- TOOLTIP DRAWING MANAGER ---
    
    def show_tooltip(self, canvas, text, x, y):
        """Draws a floating tooltip box on the canvas at the given coordinates.

        Automatically flips left or upward if the tooltip would overflow the canvas boundary.
        """
        # Hide any stale tooltip
        self.hide_tooltip(canvas)
        
        # Determine theme-aware tooltip style
        style = self.controller.style
        bg = style.colors.get("dark") or "#20374C"
        fg = "#ffffff"
        
        canvas_w = canvas.winfo_width()
        canvas_h = canvas.winfo_height()
        
        # Estimate tooltip dimensions (approx chars * px per char)
        lines = text.split("\n")
        max_chars = max(len(l) for l in lines) if lines else 10
        est_w = max_chars * 6 + 30   # rough pixel estimate
        est_h = len(lines) * 14 + 20
        
        # Determine anchor position: flip left if near right edge, flip up if near bottom
        near_right = (x + est_w + 20) > canvas_w
        near_bottom = (y + est_h + 20) > canvas_h
        
        if near_right and near_bottom:
            tx, ty, anchor = x - 15, y - 15, "se"
        elif near_right:
            tx, ty, anchor = x - 15, y + 15, "ne"
        elif near_bottom:
            tx, ty, anchor = x + 15, y - 15, "sw"
        else:
            tx, ty, anchor = x + 15, y + 15, "nw"
        
        # Create text tag to compute height & width
        text_id = canvas.create_text(
            tx, ty,
            text=text,
            fill=fg,
            font=("Helvetica", 9),
            anchor=anchor,
            justify="left"
        )
        
        # Bounding box
        bbox = canvas.bbox(text_id)
        if bbox:
            bx1, by1, bx2, by2 = bbox
            # Draw background rectangle behind text
            rect_id = canvas.create_rectangle(
                bx1 - 5, by1 - 5,
                bx2 + 5, by2 + 5,
                fill=bg,
                outline=fg,
                width=1
            )
            # Reorder canvas items so text sits on top of rectangle
            canvas.tag_raise(text_id, rect_id)
            self.tooltips[canvas] = (rect_id, text_id)

    def hide_tooltip(self, canvas):
        """Removes the active tooltip rectangle and text items from the given canvas."""
        if canvas in self.tooltips:
            rect_id, text_id = self.tooltips[canvas]
            canvas.delete(rect_id)
            canvas.delete(text_id)
            del self.tooltips[canvas]

