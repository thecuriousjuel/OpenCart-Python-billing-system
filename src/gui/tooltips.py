# src/gui/tooltips.py
"""
Treeview Hover Tooltip Helper for the OpenCart Billing System.

Provides the TreeviewTooltip class which binds to a ttk.Treeview and
displays a floating frameless popup window with contextual details
whenever the user hovers over a data row.
"""
import tkinter as tk
import ttkbootstrap as tb

class TreeviewTooltip:
    """Helper to display floating details when hovering over rows of a ttk.Treeview."""
    def __init__(self, tree, controller, query_func):
        self.tree = tree
        self.controller = controller
        self.query_func = query_func # function: takes values_list, returns text string
        self.tip_window = None
        self.hovered_item = None
        
        # Bind motion and leave events
        self.tree.bind("<Motion>", self.on_mouse_move)
        self.tree.bind("<Leave>", self.hide_tip)

    def on_mouse_move(self, event):
        """Detects the row under the cursor and triggers a tooltip if the row has changed."""
        row_id = self.tree.identify_row(event.y)
        if row_id != self.hovered_item:
            self.hovered_item = row_id
            self.hide_tip()
            if row_id:
                # Get details
                row_vals = self.tree.item(row_id, "values")
                tip_text = self.query_func(row_vals)
                if tip_text:
                    # Position tooltip relative to screen
                    x = event.x_root + 15
                    y = event.y_root + 15
                    self.show_tip(tip_text, x, y)

    def show_tip(self, text, x, y):
        """Creates and positions a borderless Toplevel popup window displaying the tooltip text."""
        if self.tip_window:
            return
            
        self.tip_window = tw = tk.Toplevel(self.tree)
        tw.wm_overrideredirect(True) # Remove window borders
        tw.wm_geometry(f"+{x}+{y}")
        
        # Determine theme-aware background/foreground colors
        style = self.controller.style
        bg = style.colors.get("dark") or "#20374C"
        fg = "#ffffff"
        
        frame = tb.Frame(tw, bootstyle="dark", padding=2)
        frame.pack()
        
        # Inner padding and styling
        inner_frame = tk.Frame(frame, bg=bg, bd=0)
        inner_frame.pack(padx=1, pady=1)
        
        lbl = tk.Label(
            inner_frame, 
            text=text, 
            justify=tk.LEFT, 
            bg=bg, 
            fg=fg, 
            font=("Helvetica", 10),
            padx=10,
            pady=8
        )
        lbl.pack()

    def hide_tip(self, event=None):
        """Destroys the tooltip popup window if one is currently visible."""
        tw = self.tip_window
        self.tip_window = None
        if tw:
            try:
                tw.destroy()
            except Exception:
                pass
