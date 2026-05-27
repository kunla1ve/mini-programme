#!/usr/bin/env python3
"""
Risk Stress Test Tool - GUI Version
A GUI application for futures/credit risk stress testing
"""

import csv
import json
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class Position:
    """Position data structure"""
    client_id: str
    product: str
    contract: str
    quantity: float
    price: float
    currency: str = "USD"
    category: str = "Other"
    tick_value: float = 1.0
    
    @property
    def notional(self) -> float:
        return abs(self.quantity) * self.price * self.tick_value
    
    @property
    def is_long(self) -> bool:
        return self.quantity > 0


# Product to category mapping
CATEGORY_MAP = {
    'JY': 'FX', 'EU': 'FX', 'AD': 'FX', 'BP': 'FX', 'CD': 'FX', 'NZD': 'FX', 
    'DX': 'FX', 'MJY': 'FX', 'MSF': 'FX', 'MBP': 'FX', 'MAD': 'FX',
    'GD': 'Metals', 'SV': 'Metals', 'PL': 'Metals', 'PA': 'Metals', 
    'GC': 'Metals', 'SI': 'Metals', 'HG': 'Metals', 'SIL': 'Metals', 
    'MGC': 'Metals', 'MHG': 'Metals', 'QO': 'Metals', 'QI': 'Metals',
    'UC': 'Metals', 'MINIGOLD': 'Metals', 'MICROGOLD': 'Metals',
    'CL': 'Energy', 'RB': 'Energy', 'HO': 'Energy', 'NG': 'Energy', 
    'MCL': 'Energy', 'MINICRUDE': 'Energy',
    'ES': 'Indices', 'NQ': 'Indices', 'YM': 'Indices', 'RTY': 'Indices',
    'MES': 'Indices', 'MNQ': 'Indices', 'MYM': 'Indices', 'M2K': 'Indices',
    'NK': 'Indices', 'TWN': 'Indices', 'SGP': 'Indices', 'CN': 'Indices',
    'GIN': 'Indices', 'FESX': 'Indices', 'TOPIXM': 'Indices', 'VIX': 'Indices',
    'TY': 'Bonds', 'US': 'Bonds', 'FV': 'Bonds', 'TU': 'Bonds',
    'UBE': 'Bonds', 'EUROJY': 'Bonds',
    'C': 'Grains', 'S': 'Grains', 'W': 'Grains', 'O': 'Grains', 
    'BO': 'Grains', 'SM': 'Grains',
    'CT': 'Softs', 'CC': 'Softs', 'SB': 'Softs', 'OJ': 'Softs',
    'LC': 'Livestock', 'FC': 'Livestock',
    'FEF': 'Iron Ore',
}


class RiskStressTest:
    """Risk stress test engine"""
    
    def __init__(self):
        self.positions: List[Position] = []
        self.results: Dict = {}
    
    def load_positions_csv(self, filepath: str) -> bool:
        """Load positions from CSV file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    client = row.get('Client_No', row.get('Client', 'UNKNOWN'))
                    if 'PHL9000' not in str(client):
                        continue
                    
                    com_type = row.get('Com_Type', '').upper()
                    if com_type != 'F':
                        continue
                    
                    com_cd = row.get('Com_cd', '')
                    contract_month = row.get('Contract_Month', '').strip()
                    contract = f"{com_cd} {contract_month}" if contract_month else com_cd
                    
                    buy_sell = row.get('Buy_Sell', 'B')
                    qty = float(row.get('Traded_Qty', 0))
                    if buy_sell == 'S':
                        qty = -qty
                    
                    price = float(row.get('Settlement_Price', row.get('Traded_Price', 0)))
                    currency = row.get('Settle_Curr_Cd', 'USD')
                    tick_value = float(row.get('Tick_Value', 1))
                    category = CATEGORY_MAP.get(com_cd, 'Other')
                    
                    self.positions.append(Position(
                        client_id=client,
                        product='Futures',
                        contract=contract,
                        quantity=qty,
                        price=price,
                        currency=currency,
                        category=category,
                        tick_value=tick_value
                    ))
            return True
        except Exception as e:
            raise Exception(f"Load failed: {e}")
    
    def aggregate_by_product(self) -> Dict:
        """Aggregate positions by product"""
        products = {}
        for p in self.positions:
            product_code = p.contract.split()[0] if ' ' in p.contract else p.contract
            
            if product_code not in products:
                products[product_code] = {
                    'category': p.category,
                    'currency': p.currency,
                    'price': p.price,
                    'tick_value': p.tick_value,
                    'long': 0,
                    'short': 0,
                    'net': 0,
                    'notional': 0
                }
            
            products[product_code]['long'] += p.quantity if p.quantity > 0 else 0
            products[product_code]['short'] += abs(p.quantity) if p.quantity < 0 else 0
            products[product_code]['net'] += p.quantity
            products[product_code]['notional'] += p.notional
        
        return products
    
    def aggregate_by_category(self) -> Dict:
        """Aggregate positions by category"""
        categories = {}
        for p in self.positions:
            cat = p.category
            if cat not in categories:
                categories[cat] = {'long': 0, 'short': 0, 'net': 0, 'notional': 0}
            
            categories[cat]['long'] += p.quantity if p.quantity > 0 else 0
            categories[cat]['short'] += abs(p.quantity) if p.quantity < 0 else 0
            categories[cat]['net'] += p.quantity
            categories[cat]['notional'] += p.notional
        
        return categories
    
    def export_product_csv(self, filepath: str):
        """Export product-level stress test CSV"""
        products = self.aggregate_by_product()
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Product', 'Curr', 'Settle_Px', 'Tick_Val', 
                           'Long', 'Short', 'Net', 'Net_Notional_USD', 
                           'Stress_10pct', 'Stress_15pct', 'Stress_20pct'])
            
            for product_code, data in sorted(products.items()):
                notional = data['notional']
                writer.writerow([
                    data['category'], product_code, data['currency'], data['price'],
                    data['tick_value'], int(data['long']), int(data['short']),
                    int(data['net']), round(notional, 2),
                    round(notional * 0.10, 2), round(notional * 0.15, 2), round(notional * 0.20, 2)
                ])
    
    def export_category_csv(self, filepath: str):
        """Export category-level stress test CSV"""
        categories = self.aggregate_by_category()
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Long', 'Short', 'Net', 'Net_Notional_USD',
                           'Stress_10pct', 'Stress_15pct', 'Stress_20pct'])
            
            for cat, data in sorted(categories.items()):
                notional = data['notional']
                writer.writerow([
                    cat, int(data['long']), int(data['short']), int(data['net']),
                    round(notional, 2), round(notional * 0.10, 2),
                    round(notional * 0.15, 2), round(notional * 0.20, 2)
                ])


class RiskStressTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Risk Stress Test Tool v1.0")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        self.tester = RiskStressTest()
        self.file_path = ""
        
        self.create_widgets()
    
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="Risk Stress Test Tool", font=("Arial", 20, "bold"))
        title.pack(pady=10)
        
        subtitle = tk.Label(self.root, text="PHL9000 Futures Stress Testing", font=("Arial", 12))
        subtitle.pack()
        
        # File selection area
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=20, padx=20, fill=tk.X)
        
        self.file_label = tk.Label(file_frame, text="Select Position File:", font=("Arial", 11))
        self.file_label.pack(side=tk.LEFT)
        
        self.file_entry = tk.Entry(file_frame, width=50, font=("Arial", 10))
        self.file_entry.pack(side=tk.LEFT, padx=10)
        
        browse_btn = tk.Button(file_frame, text="Browse...", command=self.browse_file, 
                              font=("Arial", 10), bg="#4CAF50", fg="white")
        browse_btn.pack(side=tk.LEFT)
        
        # Buttons area
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.run_btn = tk.Button(btn_frame, text="Run Stress Test", command=self.run_test,
                                font=("Arial", 12, "bold"), bg="#2196F3", fg="white",
                                width=20, height=2)
        self.run_btn.pack(side=tk.LEFT, padx=10)
        
        self.export_btn = tk.Button(btn_frame, text="Export CSV Reports", command=self.export_reports,
                                   font=("Arial", 12), bg="#FF9800", fg="white",
                                   width=20, height=2, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=10)
        
        # Status display
        self.status_label = tk.Label(self.root, text="Ready", font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=5)
        
        # Results display - Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Overview Tab
        self.overview_frame = tk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="Overview")
        
        self.overview_text = scrolledtext.ScrolledText(self.overview_frame, wrap=tk.WORD,
                                                       font=("Consolas", 11))
        self.overview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Product Details Tab
        self.product_frame = tk.Frame(self.notebook)
        self.notebook.add(self.product_frame, text="Product Details")
        
        # Product table
        columns = ('Category', 'Product', 'Currency', 'Long', 'Short', 'Net', 'Notional',
                   'Stress_10%', 'Stress_15%', 'Stress_20%')
        self.product_tree = ttk.Treeview(self.product_frame, columns=columns, show='headings')
        
        for col in columns:
            self.product_tree.heading(col, text=col)
            self.product_tree.column(col, width=80)
        
        self.product_tree.column('Product', width=100)
        self.product_tree.column('Notional', width=120)
        
        scrollbar = ttk.Scrollbar(self.product_frame, orient=tk.VERTICAL, 
                                  command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Category Summary Tab
        self.category_frame = tk.Frame(self.notebook)
        self.notebook.add(self.category_frame, text="Category Summary")
        
        columns2 = ('Category', 'Long', 'Short', 'Net', 'Notional',
                    'Stress_10%', 'Stress_15%', 'Stress_20%')
        self.category_tree = ttk.Treeview(self.category_frame, columns=columns2, show='headings')
        
        for col in columns2:
            self.category_tree.heading(col, text=col)
            self.category_tree.column(col, width=100)
        
        scrollbar2 = ttk.Scrollbar(self.category_frame, orient=tk.VERTICAL,
                                   command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=scrollbar2.set)
        
        self.category_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Footer info
        footer = tk.Label(self.root, text="Supported format: Client_No, Com_Type, Com_cd, Contract_Month, Buy_Sell, Traded_Qty, Settlement_Price",
                         font=("Arial", 9), fg="gray")
        footer.pack(pady=5)
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Position CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path = file_path
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
    
    def run_test(self):
        file_path = self.file_entry.get()
        if not file_path or not Path(file_path).exists():
            messagebox.showerror("Error", "Please select a valid CSV file")
            return
        
        try:
            self.status_label.config(text="Loading data...", fg="blue")
            self.root.update()
            
            self.tester = RiskStressTest()
            self.tester.load_positions_csv(file_path)
            
            if not self.tester.positions:
                messagebox.showwarning("Warning", "No PHL9000 futures positions found")
                self.status_label.config(text="No valid data found", fg="red")
                return
            
            self.status_label.config(text=f"Loaded {len(self.tester.positions)} positions", fg="green")
            
            # Show overview
            self.show_overview()
            
            # Show product details
            self.show_products()
            
            # Show category summary
            self.show_categories()
            
            # Enable export button
            self.export_btn.config(state=tk.NORMAL)
            
            messagebox.showinfo("Complete", f"Stress test completed!\nProcessed {len(self.tester.positions)} positions")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_label.config(text="Run failed", fg="red")
    
    def show_overview(self):
        total_long = sum(p.notional for p in self.tester.positions if p.is_long)
        total_short = sum(p.notional for p in self.tester.positions if not p.is_long)
        net = total_long - total_short
        gross = total_long + total_short
        
        report = f"""
{'='*60}
         Risk Stress Test Report - PHL9000
{'='*60}

Portfolio Overview:
  Total Positions: {len(self.tester.positions)}
  Long Notional:   ${total_long:,.2f}
  Short Notional:  ${total_short:,.2f}
  Net Exposure:    ${net:,.2f}
  Gross Exposure:  ${gross:,.2f}

Stress Test Results (by Notional):
  10% Shock:       ${gross * 0.10:,.2f}
  15% Shock:       ${gross * 0.15:,.2f}
  20% Shock:       ${gross * 0.20:,.2f}

{'='*60}
        """
        
        self.overview_text.delete(1.0, tk.END)
        self.overview_text.insert(1.0, report)
    
    def show_products(self):
        # Clear table
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        products = self.tester.aggregate_by_product()
        
        for product_code, data in sorted(products.items()):
            notional = data['notional']
            self.product_tree.insert('', tk.END, values=(
                data['category'],
                product_code,
                data['currency'],
                int(data['long']),
                int(data['short']),
                int(data['net']),
                f"${notional:,.0f}",
                f"${notional * 0.10:,.0f}",
                f"${notional * 0.15:,.0f}",
                f"${notional * 0.20:,.0f}"
            ))
    
    def show_categories(self):
        # Clear table
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
        
        categories = self.tester.aggregate_by_category()
        
        for cat, data in sorted(categories.items()):
            notional = data['notional']
            self.category_tree.insert('', tk.END, values=(
                cat,
                int(data['long']),
                int(data['short']),
                int(data['net']),
                f"${notional:,.0f}",
                f"${notional * 0.10:,.0f}",
                f"${notional * 0.15:,.0f}",
                f"${notional * 0.20:,.0f}"
            ))
    
    def export_reports(self):
        if not self.tester.positions:
            messagebox.showerror("Error", "No data to export")
            return
        
        # Select export directory
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            return
        
        try:
            # Generate filenames
            timestamp = datetime.now().strftime("%Y%m%d")
            
            product_file = Path(export_dir) / f"PHL9000_{timestamp}_Product_StressTest.csv"
            category_file = Path(export_dir) / f"PHL9000_{timestamp}_Category_StressTest.csv"
            
            self.tester.export_product_csv(str(product_file))
            self.tester.export_category_csv(str(category_file))
            
            messagebox.showinfo("Export Successful", 
                              f"Reports exported:\n\n{product_file.name}\n{category_file.name}")
            
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))


def main():
    root = tk.Tk()
    app = RiskStressTestGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
