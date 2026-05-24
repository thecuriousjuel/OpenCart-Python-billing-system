# src/gui/logs.py
"""
System Diagnostics Log Viewer for the OpenCart Billing System.

Provides a standalone modal dialog (SystemLogsDialog) that reads and
displays the last 150 lines of the current day's log file in a
syntax-highlighted scrollable console widget.
"""
import os
import tkinter as tk
import ttkbootstrap as tb
from datetime import datetime

class SystemLogsDialog(tb.Toplevel):
    """Standalone popup window displaying real-time system diagnostics logs."""
    def __init__(self, parent):
        super().__init__(title="System Diagnostics Logs", size=(850, 600))
        self.resizable(True, True)
        self.grab_set() # Modal dialog
        
        # Header
        header_frame = tb.Frame(self, padding=15)
        header_frame.pack(fill="x")
        
        tb.Label(
            header_frame, 
            text="Diagnostics Log Console Operations", 
            font=("Helvetica", 14, "bold"), 
            bootstyle="primary"
        ).pack(side="left")
        
        tb.Button(
            header_frame, 
            text="Refresh Console Logs", 
            bootstyle="info-outline", 
            command=self.reload_logs
        ).pack(side="right")
        
        # Text Frame with Scrollbar
        txt_frame = tb.Frame(self, padding=(15, 0, 15, 15))
        txt_frame.pack(fill="both", expand=True)
        
        self.text_logs = tk.Text(
            txt_frame, 
            bg="#11111b", 
            fg="#a6e3a1", # Console green
            insertbackground="white", 
            font=("Consolas", 10), 
            state="disabled", 
            wrap="word"
        )
        self.text_logs.pack(side="left", fill="both", expand=True)
        
        scroll = tb.Scrollbar(txt_frame, orient="vertical", command=self.text_logs.yview)
        scroll.pack(side="right", fill="y")
        self.text_logs.configure(yscrollcommand=scroll.set)
        
        self.reload_logs()

    def reload_logs(self):
        """Reads the current day's log file and populates the console text widget with the last 150 lines."""
        self.text_logs.configure(state="normal")
        self.text_logs.delete("1.0", tk.END)
        
        log_file = os.path.join("logs", f"{datetime.now().strftime('%Y-%m-%d')}.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    tail_lines = lines[-150:] # show last 150 lines
                    self.text_logs.insert(tk.END, "".join(tail_lines))
                    self.text_logs.see(tk.END)
            except Exception as e:
                self.text_logs.insert(tk.END, f"Error reading logs: {e}")
        else:
            self.text_logs.insert(tk.END, "No log entries found for today.")
            
        self.text_logs.configure(state="disabled")

def show_logs_dialog(parent):
    """Convenience function that instantiates and shows the SystemLogsDialog modal window."""
    SystemLogsDialog(parent)
