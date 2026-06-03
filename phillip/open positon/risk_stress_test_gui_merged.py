# -*- coding: utf-8 -*-
"""
压力测试工具 - GUI 版本
用于期货/信用风险压力测试的图形界面程序
支持中英双语切换
（合并版本：包含持仓与财务文件的自动检测，优化了财务摘要页面布局）
"""

import csv
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path


@dataclass
class Position:
    """持仓数据结构"""
    client_id: str
    product: str
    contract: str
    quantity: float
    price: float
    currency: str = "USD"
    category: str = "Other"
    tick_value: float = 1.0
    com_type: str = "F"
    exch_cd: str = ""
    com_cd: str = ""
    contract_month: str = ""
    notional_usd: float = 0.0
    equity_usd: float = 0.0
    
    @property
    def is_long(self) -> bool:
        """判断是否为多头持仓"""
        return self.quantity > 0


@dataclass
class FinancialSummary:
    """各币种财务摘要数据结构"""
    client_id: str
    currency: str
    ledger_cf: float
    unrealised_pnl: float
    equity_balance: float
    net_equity: float
    im_amt: float
    mm_amt: float
    margin_excess: float
    allowable_withdrawal: float
    net_options_value: float
    exch_rate: float
    ledger_cf_usd: float = 0.0
    equity_balance_usd: float = 0.0
    net_equity_usd: float = 0.0
    im_amt_usd: float = 0.0
    mm_amt_usd: float = 0.0
    margin_excess_usd: float = 0.0


# 产品代码到产品大类的映射字典
CATEGORY_MAP = {
    'JY': 'FX', 'EU': 'FX', 'AD': 'FX', 'BP': 'FX', 'CD': 'FX', 'NZD': 'FX', 
    'DX': 'FX', 'MJY': 'FX', 'MSF': 'FX', 'MBP': 'FX', 'MAD': 'FX',
    'GD': 'Metals', 'SV': 'Metals', 'PL': 'Metals', 'PA': 'Metals', 
    'GC': 'Metals', 'SI': 'Metals', 'HG': 'Metals', 'SIL': 'Metals', 
    'MGC': 'Metals', 'MHG': 'Metals', 'QO': 'Metals', 'QI': 'Metals',
    'UC': 'FX', 'MINIGOLD': 'Metals', 'MICROGOLD': 'Metals',
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

# ========== 添加汇率字典 ==========
# 从提供的汇率表创建字典，使用Buy价（中间价）
exchange_rates = {
    'AUD': 0.7205,
    'CAD': 1/1.3718,
    'CHF': 1/0.7837,
    'CNH': 1/6.8377,
    'DKK': 1/6.4216,
    'EUR': 1.1671,
    'GBP': 1.3516,
    'HKD': 1/7.842,
    'IDR': 1/17705.16,
    'INR': 1/95.4304,
    'JPY': 1/157.4394,
    'KRW': 1/1465.3989,
    'MYR': 1/3.9603,
    'NOK': 1/9.3939,
    'NZD': 0.5925,
    'PHP': 1/61.1367,
    'SEK': 1/9.3281,
    'SGD': 1/1.2738,
    'THB': 1/32.6356,
    'TRY': 1/45.6068,
    'TWD': 1/31.572,
    'USD': 1.0000,
}

# 额外添加交叉汇率
cross_rates = {
    'AUD/HKD': 5.643,
    'EUR/HKD': 9.141,
    'GBP/HKD': 10.5858,
    'NZD/HKD': 4.6407,
}

def convert_to_usd(amount, from_currency):
    """
    将金额从 from_currency 转换为 USD
    """
    if not isinstance(from_currency, str) or from_currency.strip() == '' or from_currency.lower() == 'nan':
        return amount
        
    if from_currency in exchange_rates:
        return amount * exchange_rates[from_currency]
        
    if '/' in from_currency:
        if from_currency in cross_rates:
            hkd_amount = amount * cross_rates[from_currency]
            return hkd_amount * exchange_rates.get('HKD', 1/7.842)
        else:
            base, quote = from_currency.split('/')
            if base in exchange_rates and quote in exchange_rates:
                return amount * exchange_rates[base] / exchange_rates[quote]
    
    return amount

# ============================================================
# 中英双语翻译字典
# ============================================================
TEXTS = {
    'en': {
        'window_title': 'Risk Stress Test Tool v2.0',
        'title': 'Risk Stress Test Tool',
        'subtitle': 'Futures Stress Testing (PHL9000, Excludes Options)',
        'position_file': 'Position File:',
        'financial_summary': 'Financial Summary:',
        'browse': 'Browse...',
        'select_pos_csv': 'Select Position CSV File',
        'select_fin_csv': 'Select Financial Summary CSV File',
        'csv_files': 'CSV files',
        'all_files': 'All files',
        'run_test': 'Run Stress Test',
        'export_reports': 'Export CSV Reports',
        'language_btn': '中文',
        
        'ready': 'Ready',
        'loading': 'Loading data...',
        'no_positions': 'No valid futures positions found',
        'no_valid': 'No valid data found',
        'loaded': 'Loaded {} positions',
        'run_failed': 'Run failed',
        'select_csv': 'Please select a valid CSV file',
        
        'error': 'Error',
        'warning': 'Warning',
        'complete': 'Complete',
        'completed_msg': 'Stress test completed!\nProcessed {} positions',
        'no_data_export': 'No data to export',
        'select_export_dir': 'Select Export Directory',
        'export_success': 'Export Successful',
        'export_msg': 'Reports exported:\n\n{}\n{}',
        'export_failed': 'Export Failed',
        
        'tab_overview': 'Overview',
        'tab_product': 'Product Details',
        'tab_category': 'Category Summary',
        'tab_financial': 'Financial Summary',
        
        'col_category': 'Category',
        'col_product': 'Product',
        'col_currency': 'Currency',
        'col_long': 'Long',
        'col_short': 'Short',
        'col_net': 'Net',
        'col_notional': 'Notional',
        'col_stress_10': 'Stress_10%',
        'col_stress_15': 'Stress_15%',
        'col_stress_20': 'Stress_20%',
        'col_ledger_cf': 'Ledger_CF',
        'col_unrealised_pnl': 'Unrealised_PnL',
        'col_equity_balance': 'Equity_Balance',
        'col_net_equity': 'Net_Equity',
        'col_im_amt': 'IM_Amt',
        'col_mm_amt': 'MM_Amt',
        'col_margin_excess': 'Margin_Excess',
        'col_exch_rate': 'Exch_Rate',
        'col_usd_equiv': 'USD Equiv',
        
        'footer': 'Supported format: Client_No, Com_Type, Com_cd, Contract_Month, Buy_Sell, Traded_Qty, Settlement_Price',
        
        'report_header': 'Risk Stress Test Report - PHL9000',
        'portfolio_overview': 'Portfolio Overview:',
        'total_positions': 'Total Positions:',
        'long_notional': 'Long Notional:',
        'short_notional': 'Short Notional:',
        'net_exposure': 'Net Exposure:',
        'gross_exposure': 'Gross Exposure:',
        'stress_results': 'Stress Test Results (by Notional):',
        'shock_10': '10% Shock:',
        'shock_15': '15% Shock:',
        'shock_20': '20% Shock:',
        
        'fin_summary_title': 'Financial Summary - PHL9000',
        'equity_balance_label': 'Total Equity Balance (USD):',
        'net_equity_label': 'Total Net Equity (USD):',
        'unrealised_pnl_label': 'Total Unrealised PnL (USD):',
        'im_label': 'Total Initial Margin (USD):',
        'mm_label': 'Total Maint. Margin (USD):',
        'margin_excess_label': 'Total Margin Excess (USD):',
        'margin_util': 'Margin Usage Ratio:',
        'fin_detail_header': 'Currency Breakdown:',
        'fin_not_loaded': '(Financial summary not loaded)',
        'fin_loaded': 'Financial summary loaded',
        'total_usd': 'TOTAL (USD)',
    },
    'zh': {
        'window_title': '风险压力测试工具 v2.0',
        'title': '风险压力测试工具',
        'subtitle': '期货压力测试 (PHL9000，不包含期权)',
        'position_file': '持仓文件：',
        'financial_summary': '财务摘要：',
        'browse': '浏览...',
        'select_pos_csv': '选择持仓 CSV 文件',
        'select_fin_csv': '选择财务摘要 CSV 文件',
        'csv_files': 'CSV 文件',
        'all_files': '所有文件',
        'run_test': '执行压力测试',
        'export_reports': '导出CSV报告',
        'language_btn': 'English',
        
        'ready': '就绪',
        'loading': '正在加载数据...',
        'no_positions': '未找到有效的期货持仓',
        'no_valid': '未找到有效数据',
        'loaded': '已加载 {} 条持仓',
        'run_failed': '执行失败',
        'select_csv': '请选择一个有效的 CSV 文件',
        
        'error': '错误',
        'warning': '警告',
        'complete': '完成',
        'completed_msg': '压力测试完成！\n已处理 {} 条持仓',
        'no_data_export': '没有数据可导出',
        'select_export_dir': '选择导出目录',
        'export_success': '导出成功',
        'export_msg': '报告已导出：\n\n{}\n{}',
        'export_failed': '导出失败',
        
        'tab_overview': '总览',
        'tab_product': '产品明细',
        'tab_category': '分类汇总',
        'tab_financial': '财务摘要',
        
        'col_category': '类别',
        'col_product': '产品',
        'col_currency': '币种',
        'col_long': '多头',
        'col_short': '空头',
        'col_net': '净头寸',
        'col_notional': '名义价值',
        'col_stress_10': '压力_10%',
        'col_stress_15': '压力_15%',
        'col_stress_20': '压力_20%',
        'col_ledger_cf': '账本现金',
        'col_unrealised_pnl': '未实现盈亏',
        'col_equity_balance': '权益余额',
        'col_net_equity': '净权益',
        'col_im_amt': '初始保证金',
        'col_mm_amt': '维持保证金',
        'col_margin_excess': '保证金盈余',
        'col_exch_rate': '汇率',
        'col_usd_equiv': 'USD等值',
        
        'footer': '支持格式: Client_No, Com_Type, Com_cd, Contract_Month, Buy_Sell, Traded_Qty, Settlement_Price',
        
        'report_header': '风险压力测试报告 - PHL9000',
        'portfolio_overview': '投资组合概览：',
        'total_positions': '总持仓数：',
        'long_notional': '多头名义价值：',
        'short_notional': '空头名义价值：',
        'net_exposure': '净敞口：',
        'gross_exposure': '总敞口：',
        'stress_results': '压力测试结果（基于名义价值）：',
        'shock_10': '10% 冲击：',
        'shock_15': '15% 冲击：',
        'shock_20': '20% 冲击：',
        
        'fin_summary_title': '财务摘要 - PHL9000',
        'equity_balance_label': '权益余额合计 (USD)：',
        'net_equity_label': '净权益合计 (USD)：',
        'unrealised_pnl_label': '未实现盈亏合计 (USD)：',
        'im_label': '初始保证金合计 (USD)：',
        'mm_label': '维持保证金合计 (USD)：',
        'margin_excess_label': '保证金盈余合计 (USD)：',
        'margin_util': '保证金使用率：',
        'fin_detail_header': '分币种明细：',
        'fin_not_loaded': '（未加载财务摘要）',
        'fin_loaded': '财务摘要已加载',
        'total_usd': '合计 (USD)',
    }
}


class RiskStressTest:
    """风险压力测试引擎核心计算类"""
    
    def __init__(self):
        self.positions: List[Position] = []
        self.financial_summary: List[FinancialSummary] = []
    
    def load_positions_csv(self, filepath: str) -> bool:
        """从 CSV 文件加载持仓数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    client = row.get('Client_No', row.get('Client', 'UNKNOWN'))
                    
                    # 只处理 PHL9000 账户
                    if client != 'PHL9000':
                        continue
                    
                    com_type = row.get('Com_Type', '').upper()
                    # 保同期权过滤（暂时不处理 O 期权）
                    if com_type not in ('F', 'X'):
                        continue
                    
                    exch_cd = row.get('Exch_Cd', '')
                    com_cd = row.get('Com_cd', '')
                    contract_month = row.get('Contract_Month', '').strip()
                    contract = f"{com_cd} {contract_month}" if contract_month else com_cd
                    
                    buy_sell = row.get('Buy_Sell', 'B')
                    qty = float(row.get('Traded_Qty', 0))
                    if buy_sell == 'S':
                        qty = -qty
                    
                    tick_value = float(row.get('Tick_Value', 1))
                    currency = row.get('Settle_Curr_Cd', 'USD')
                    category = CATEGORY_MAP.get(com_cd, 'Other')
                    
                    # 差异化计算 Equity 和 Notional
                    if com_type == 'X':
                        # 远期合约如果存在 Cumulative_Swap 则优先使用
                        if 'Cumulative_Swap' in row and row['Cumulative_Swap'].strip():
                            calc_price = float(row['Cumulative_Swap'])
                        else:
                            calc_price = float(row.get('Settlement_Price', row.get('Traded_Price', 0)))
                    else:
                        calc_price = float(row.get('Settlement_Price', row.get('Traded_Price', 0)))
                        
                    price = float(row.get('Settlement_Price', row.get('Traded_Price', 0)))
                    
                    # 取绝对值名义价值和原始权益
                    notional = abs(qty) * price * tick_value
                    equity = qty * calc_price * tick_value
                    
                    # 通过转换逻辑统一挂算到 USD
                    notional_usd = convert_to_usd(notional, currency)
                    equity_usd = convert_to_usd(equity, currency)
                    
                    self.positions.append(Position(
                        client_id=client,
                        product='Futures' if com_type == 'F' else 'Forwards',
                        contract=contract,
                        quantity=qty,
                        price=price,
                        currency=currency,
                        category=category,
                        tick_value=tick_value,
                        com_type=com_type,
                        exch_cd=exch_cd,
                        com_cd=com_cd,
                        contract_month=contract_month,
                        notional_usd=notional_usd,
                        equity_usd=equity_usd
                    ))
            return True
        except Exception as e:
            raise Exception(f"Load failed: {e}")
    
    def load_financial_summary_csv(self, filepath: str) -> bool:
        """从 CSV 文件加载财务摘要数据 (提取所有账户信息)"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    client = row.get('Client_No', '')
                    
                    # 只处理 PHL9000 账户
                    if client != 'PHL9000':
                        continue
                    
                    currency = row.get('Curr_Cd', 'USD')
                    self.financial_summary.append(FinancialSummary(
                        client_id=client,
                        currency=currency,
                        ledger_cf=float(row.get('Ledger_Cf', 0)),
                        unrealised_pnl=float(row.get('Unrealised_Profit_Loss', 0)),
                        equity_balance=float(row.get('Equity_Balance', 0)),
                        net_equity=float(row.get('NetEquity', 0)),
                        im_amt=float(row.get('Im_Amt', 0)),
                        mm_amt=float(row.get('MM_Amt', 0)),
                        margin_excess=float(row.get('Margin_Excess', 0)),
                        allowable_withdrawal=float(row.get('AllowableWithdrawal', 0)),
                        net_options_value=float(row.get('Net_Options_Value', 0)),
                        exch_rate=float(row.get('Exch_Rate', 1)),
                        ledger_cf_usd=float(row.get('Ledger_Cf(BASE_USD)', 0)),
                        equity_balance_usd=float(row.get('Equity_Balance(BASE_USD)', 0)),
                        net_equity_usd=float(row.get('NetEquity(BASE_USD)', 0)),
                        im_amt_usd=float(row.get('Im_Amt(BASE_USD)', 0)),
                        mm_amt_usd=float(row.get('MM_Amt(BASE_USD)', 0)),
                        margin_excess_usd=float(row.get('Margin_Excess(BASE_USD)', 0)),
                    ))
            return True
        except Exception as e:
            raise Exception(f"Load financial summary failed: {e}")

    def aggregate_by_product(self) -> Dict:
        """按合约精准聚合持仓 (分组逻辑：Exch_Cd + Com_cd + Contract_Month)"""
        products = {}
        for p in self.positions:
            # 使用组合键来进行更准确的产品聚合
            group_key = f"{p.exch_cd}_{p.com_cd}_{p.contract_month}"
            
            if group_key not in products:
                products[group_key] = {
                    'category': p.category,
                    'product_code': p.contract,  # 保存展示用的合约名称
                    'currency': p.currency,
                    'price': p.price,
                    'tick_value': p.tick_value,
                    'long': 0,
                    'short': 0,
                    'net': 0,
                    'notional': 0,      # 保留键，但在代码后面直接指向 notional_usd
                    'notional_usd': 0
                }
            
            products[group_key]['long'] += p.quantity if p.quantity > 0 else 0
            products[group_key]['short'] += abs(p.quantity) if p.quantity < 0 else 0
            products[group_key]['net'] += p.quantity
            products[group_key]['notional_usd'] += p.notional_usd
            products[group_key]['notional'] += p.notional_usd # 为了向后兼容其他引用的变量名
        
        return products
    
    def aggregate_by_category(self) -> Dict:
        """按类别粗粒度聚合持仓 (统一使用已换算的 USD 名义价值进行累加)"""
        categories = {}
        for p in self.positions:
            cat = p.category
            if cat not in categories:
                categories[cat] = {'long': 0, 'short': 0, 'net': 0, 'notional': 0, 'notional_usd': 0}
            
            categories[cat]['long'] += p.quantity if p.quantity > 0 else 0
            categories[cat]['short'] += abs(p.quantity) if p.quantity < 0 else 0
            categories[cat]['net'] += p.quantity
            categories[cat]['notional_usd'] += p.notional_usd
            categories[cat]['notional'] += p.notional_usd
        
        return categories
    
    def export_product_csv(self, filepath: str):
        """将产品级别聚合结果导出为 CSV 文件"""
        products = self.aggregate_by_product()
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Product', 'Curr', 'Settle_Px', 'Tick_Val', 
                           'Long', 'Short', 'Net', 'Net_Notional_USD', 
                           'Stress_10pct_USD', 'Stress_15pct_USD', 'Stress_20pct_USD'])
            for group_key, data in sorted(products.items(), key=lambda x: x[1]['product_code']):
                notional = data['notional_usd']
                writer.writerow([
                    data['category'], data['product_code'], data['currency'], data['price'],
                    data['tick_value'], int(data['long']), int(data['short']),
                    int(data['net']), round(notional, 2),
                    round(notional * 0.10, 2), round(notional * 0.15, 2), round(notional * 0.20, 2)
                ])
    
    def export_category_csv(self, filepath: str):
        """将大类级别聚合结果导出为 CSV 文件"""
        categories = self.aggregate_by_category()
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Long', 'Short', 'Net', 'Net_Notional_USD',
                           'Stress_10pct_USD', 'Stress_15pct_USD', 'Stress_20pct_USD'])
            for cat, data in sorted(categories.items()):
                notional = data['notional_usd']
                writer.writerow([
                    cat, int(data['long']), int(data['short']), int(data['net']),
                    round(notional, 2), round(notional * 0.10, 2),
                    round(notional * 0.15, 2), round(notional * 0.20, 2)
                ])


class RiskStressTestGUI:
    """带有自动检测文件功能的图形界面主类 (支持中英双语切换)"""
    
    def __init__(self, root):
        self.root = root
        self.lang = 'zh'  # 默认中文
        self.root.title(TEXTS[self.lang]['window_title'])
        self.root.geometry("1100x800")
        self.root.minsize(900, 650)
        
        self.tester = RiskStressTest()
        
        self.create_widgets()
        self._auto_detect_files()
        
    def _auto_detect_files(self):
        """自动侦测当前目录下存在的持仓文件和财务汇总文件，并尽量保证日期相同"""
        import sys
        if getattr(sys, 'frozen', False):
            # 运行的是打包后的 exe 文件
            script_dir = Path(sys.executable).parent
        else:
            # 运行的是未打包的 .py 脚本
            script_dir = Path(__file__).parent
        
        # 获取所有持仓文件并按名称降序排列（最新的在前）
        pos_candidates = list(script_dir.glob("PHILLIP_Open_Position_*.csv"))
        pos_candidates.sort(reverse=True)
        
        if pos_candidates:
            # 填入最新持仓文件
            latest_pos_file = pos_candidates[0]
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, str(latest_pos_file))
            
            # 尝试从文件名中提取日期并寻找匹配的财务文件
            date_str = latest_pos_file.stem.split('_')[-1]
            matching_fin_file = script_dir / f"PHILLIP_Financial_Summary_{date_str}.csv"
            
            if matching_fin_file.exists():
                # 找到日期相同的财务文件
                self.fin_entry.delete(0, tk.END)
                self.fin_entry.insert(0, str(matching_fin_file))
            else:
                # 如果没有相同日期的，则回退到寻找最新的财务文件
                fin_candidates = list(script_dir.glob("PHILLIP_Financial_Summary_*.csv"))
                if fin_candidates:
                    fin_candidates.sort(reverse=True)
                    self.fin_entry.delete(0, tk.END)
                    self.fin_entry.insert(0, str(fin_candidates[0]))
        else:
            # 如果没有持仓文件，仍尝试找最新的财务文件
            fin_candidates = list(script_dir.glob("PHILLIP_Financial_Summary_*.csv"))
            if fin_candidates:
                fin_candidates.sort(reverse=True)
                self.fin_entry.delete(0, tk.END)
                self.fin_entry.insert(0, str(fin_candidates[0]))
            
    def t(self, key: str) -> str:
        """获取当前语言对应的翻译文本"""
        return TEXTS.get(self.lang, TEXTS['en']).get(key, key)
    
    def _update_all_texts(self):
        """语言切换时刷新所有的 UI 文本显示"""
        self.root.title(self.t('window_title'))
        self.title_label.config(text=self.t('title'))
        self.subtitle_label.config(text=self.t('subtitle'))
        self.file_label.config(text=self.t('position_file'))
        self.fin_label.config(text=self.t('financial_summary'))
        self.browse_btn.config(text=self.t('browse'))
        self.fin_browse_btn.config(text=self.t('browse'))
        self.run_btn.config(text=self.t('run_test'))
        self.export_btn.config(text=self.t('export_reports'))
        self.lang_btn.config(text=self.t('language_btn'))
        self.footer_label.config(text=self.t('footer'))
        
        # 更新标签页名称
        self.notebook.tab(0, text=self.t('tab_overview'))
        self.notebook.tab(1, text=self.t('tab_financial'))
        self.notebook.tab(2, text=self.t('tab_product'))
        self.notebook.tab(3, text=self.t('tab_category'))
        
        # 更新产品明细表格表头
        prod_cols = {
            'Category': self.t('col_category'),
            'Product': self.t('col_product'),
            'Currency': self.t('col_currency'),
            'Long': self.t('col_long'),
            'Short': self.t('col_short'),
            'Net': self.t('col_net'),
            'Notional': self.t('col_notional'),
            'Stress_10%': self.t('col_stress_10'),
            'Stress_15%': self.t('col_stress_15'),
            'Stress_20%': self.t('col_stress_20'),
        }
        for old, new in prod_cols.items():
            self.product_tree.heading(old, text=new)
        
        # 更新分类汇总表格表头
        cat_cols = {
            'Category': self.t('col_category'),
            'Long': self.t('col_long'),
            'Short': self.t('col_short'),
            'Net': self.t('col_net'),
            'Notional': self.t('col_notional'),
            'Stress_10%': self.t('col_stress_10'),
            'Stress_15%': self.t('col_stress_15'),
            'Stress_20%': self.t('col_stress_20'),
        }
        for old, new in cat_cols.items():
            self.category_tree.heading(old, text=new)
        
        # 更新财务摘要表格表头
        fin_cols = {
            'Currency': self.t('col_currency'),
            'Ledger_CF': self.t('col_ledger_cf'),
            'Unrealised_PnL': self.t('col_unrealised_pnl'),
            'Equity_Balance': self.t('col_equity_balance'),
            'Net_Equity': self.t('col_net_equity'),
            'IM_Amt': self.t('col_im_amt'),
            'MM_Amt': self.t('col_mm_amt'),
            'Margin_Excess': self.t('col_margin_excess'),
            'Exch_Rate': self.t('col_exch_rate'),
            'USD_Equiv': self.t('col_usd_equiv'),
        }
        for old, new in fin_cols.items():
            self.fin_tree.heading(old, text=new)
        
        # 如果已经加载过数据，顺便刷新数据展示
        if self.tester.positions:
            self.show_overview()
            self.show_financial_summary()
            self.show_products()
            self.show_categories()
            
        current_status = self.status_label.cget("text")
        if current_status in [TEXTS['en']['ready'], TEXTS['zh']['ready'],
                              TEXTS['en']['run_failed'], TEXTS['zh']['run_failed']]:
            self.status_label.config(text=self.t('ready' if 'ready' in current_status.lower() or '就绪' in current_status else 'run_failed'))
        else:
            self.status_label.config(text=self.t('ready'))
    
    def toggle_language(self):
        """切换界面使用的显示语言（中/英）"""
        self.lang = 'zh' if self.lang == 'en' else 'en'
        self._update_all_texts()
    
    def create_widgets(self):
        """构建并初始化 GUI 视窗内的所有组件控件"""
        # ---- 顶部栏（语言切换 + 标题） ----
        top_bar = tk.Frame(self.root)
        top_bar.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        self.lang_btn = tk.Button(top_bar, text=self.t('language_btn'),
                                  command=self.toggle_language,
                                  font=("Arial", 10), bg="#607D8B", fg="white",
                                  width=8)
        self.lang_btn.pack(side=tk.RIGHT)
        
        self.title_label = tk.Label(self.root, text=self.t('title'),
                                    font=("Arial", 20, "bold"))
        self.title_label.pack(pady=(5, 0))
        
        self.subtitle_label = tk.Label(self.root, text=self.t('subtitle'),
                                       font=("Arial", 12), fg="#555")
        self.subtitle_label.pack()
        
        # ---- 文件选择区 ----
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.file_label = tk.Label(file_frame, text=self.t('position_file'),
                                   font=("Arial", 11), width=16, anchor='w')
        self.file_label.pack(side=tk.LEFT)
        
        self.file_entry = tk.Entry(file_frame, width=60, font=("Arial", 10))
        self.file_entry.pack(side=tk.LEFT, padx=10)
        
        self.browse_btn = tk.Button(file_frame, text=self.t('browse'),
                                    command=lambda: self.browse_file(self.file_entry, 'select_pos_csv'),
                                    font=("Arial", 10), bg="#4CAF50", fg="white")
        self.browse_btn.pack(side=tk.LEFT)
        
        # ---- 财务摘要文件选择区 ----
        fin_frame = tk.Frame(self.root)
        fin_frame.pack(pady=5, padx=20, fill=tk.X)
        
        self.fin_label = tk.Label(fin_frame, text=self.t('financial_summary'),
                                  font=("Arial", 11), width=16, anchor='w')
        self.fin_label.pack(side=tk.LEFT)
        
        self.fin_entry = tk.Entry(fin_frame, width=60, font=("Arial", 10))
        self.fin_entry.pack(side=tk.LEFT, padx=10)
        
        self.fin_browse_btn = tk.Button(fin_frame, text=self.t('browse'),
                                        command=lambda: self.browse_file(self.fin_entry, 'select_fin_csv'),
                                        font=("Arial", 10), bg="#4CAF50", fg="white")
        self.fin_browse_btn.pack(side=tk.LEFT)
        
        # ---- 按钮区 ----
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.run_btn = tk.Button(btn_frame, text=self.t('run_test'),
                                 command=self.run_test,
                                 font=("Arial", 12, "bold"), bg="#2196F3", fg="white",
                                 width=20, height=2)
        self.run_btn.pack(side=tk.LEFT, padx=10)
        
        self.export_btn = tk.Button(btn_frame, text=self.t('export_reports'),
                                    command=self.export_reports,
                                    font=("Arial", 12), bg="#FF9800", fg="white",
                                    width=20, height=2, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=10)
        
        # ---- 状态显示 ----
        self.status_label = tk.Label(self.root, text=self.t('ready'),
                                     font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=3)
        
        # ---- Tab 页（结果显示） ----
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
        
        # 1. 总览标签页
        self.overview_frame = tk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text=self.t('tab_overview'))
        
        self.overview_text = scrolledtext.ScrolledText(self.overview_frame, wrap=tk.WORD,
                                                       font=("Consolas", 11))
        self.overview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 2. 财务摘要标签页（inhance2.py 风格）
        self.financial_frame = tk.Frame(self.notebook)
        self.notebook.add(self.financial_frame, text=self.t('tab_financial'))
        
        self.fin_text = scrolledtext.ScrolledText(self.financial_frame, wrap=tk.WORD,
                                                   font=("Consolas", 11), height=10)
        self.fin_text.pack(fill=tk.X, padx=5, pady=5)
        
        fin_columns = ('Currency', 'Ledger_CF', 'Unrealised_PnL', 'Equity_Balance',
                       'Net_Equity', 'IM_Amt', 'MM_Amt', 'Margin_Excess', 'Exch_Rate', 'USD_Equiv')
        self.fin_tree = ttk.Treeview(self.financial_frame, columns=fin_columns, show='headings', height=10)
        
        fin_col_texts = [
            self.t('col_currency'), self.t('col_ledger_cf'), self.t('col_unrealised_pnl'),
            self.t('col_equity_balance'), self.t('col_net_equity'), self.t('col_im_amt'),
            self.t('col_mm_amt'), self.t('col_margin_excess'), self.t('col_exch_rate'),
            self.t('col_usd_equiv')
        ]
        
        # 计算大致适合 1100px 视窗宽度的列宽
        col_widths = [80, 100, 110, 100, 100, 100, 100, 100, 80, 100]
        for col, text, w in zip(fin_columns, fin_col_texts, col_widths):
            self.fin_tree.heading(col, text=text)
            if col == 'Currency':
                self.fin_tree.column(col, width=w, anchor='center')
            else:
                self.fin_tree.column(col, width=w, anchor='e')
        
        fin_scrollbar = ttk.Scrollbar(self.financial_frame, orient=tk.VERTICAL,
                                      command=self.fin_tree.yview)
        self.fin_tree.configure(yscrollcommand=fin_scrollbar.set)
        
        self.fin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        fin_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 3. 产品明细标签页
        self.product_frame = tk.Frame(self.notebook)
        self.notebook.add(self.product_frame, text=self.t('tab_product'))
        
        columns = ('Category', 'Product', 'Currency', 'Long', 'Short', 'Net', 'Notional',
                   'Stress_10%', 'Stress_15%', 'Stress_20%')
        self.product_tree = ttk.Treeview(self.product_frame, columns=columns, show='headings')
        
        prod_col_texts = [
            self.t('col_category'), self.t('col_product'), self.t('col_currency'),
            self.t('col_long'), self.t('col_short'), self.t('col_net'),
            self.t('col_notional'), self.t('col_stress_10'),
            self.t('col_stress_15'), self.t('col_stress_20')
        ]
        for col, text in zip(columns, prod_col_texts):
            self.product_tree.heading(col, text=text)
            self.product_tree.column(col, width=80)
        
        self.product_tree.column('Product', width=100)
        self.product_tree.column('Notional', width=120)
        
        scrollbar = ttk.Scrollbar(self.product_frame, orient=tk.VERTICAL, 
                                  command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 4. 分类汇总标签页
        self.category_frame = tk.Frame(self.notebook)
        self.notebook.add(self.category_frame, text=self.t('tab_category'))
        
        columns2 = ('Category', 'Long', 'Short', 'Net', 'Notional',
                    'Stress_10%', 'Stress_15%', 'Stress_20%')
        self.category_tree = ttk.Treeview(self.category_frame, columns=columns2, show='headings')
        
        cat_col_texts = [
            self.t('col_category'), self.t('col_long'), self.t('col_short'),
            self.t('col_net'), self.t('col_notional'), self.t('col_stress_10'),
            self.t('col_stress_15'), self.t('col_stress_20')
        ]
        for col, text in zip(columns2, cat_col_texts):
            self.category_tree.heading(col, text=text)
            self.category_tree.column(col, width=100)
        
        scrollbar2 = ttk.Scrollbar(self.category_frame, orient=tk.VERTICAL,
                                   command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=scrollbar2.set)
        
        self.category_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ---- 页脚 ----
        self.footer_label = tk.Label(self.root, text=self.t('footer'),
                                     font=("Arial", 9), fg="gray")
        self.footer_label.pack(pady=3)
    
    def browse_file(self, target_entry, text_key):
        """打开文件选择对话框并将选中路径填入目标输入框"""
        file_path = filedialog.askopenfilename(
            title=self.t(text_key),
            filetypes=[(self.t('csv_files'), "*.csv"), (self.t('all_files'), "*.*")]
        )
        if file_path:
            target_entry.delete(0, tk.END)
            target_entry.insert(0, file_path)
    
    def run_test(self):
        """执行压力测试计算：读取指定的 CSV 文件并重新渲染报表数据"""
        file_path = self.file_entry.get()
        if not file_path or not Path(file_path).exists():
            messagebox.showerror(self.t('error'), self.t('select_csv'))
            return
        
        try:
            self.status_label.config(text=self.t('loading'), fg="blue")
            self.root.update()
            
            self.tester = RiskStressTest()
            self.tester.load_positions_csv(file_path)
            
            fin_path = self.fin_entry.get()
            if fin_path and Path(fin_path).exists():
                self.tester.load_financial_summary_csv(fin_path)
            
            if not self.tester.positions:
                messagebox.showwarning(self.t('warning'), self.t('no_positions'))
                self.status_label.config(text=self.t('no_valid'), fg="red")
                return
            
            self.status_label.config(
                text=self.t('loaded').format(len(self.tester.positions)),
                fg="green"
            )
            
            self.show_overview()
            self.show_financial_summary()
            self.show_products()
            self.show_categories()
            
            self.export_btn.config(state=tk.NORMAL)
            
            messagebox.showinfo(
                self.t('complete'),
                self.t('completed_msg').format(len(self.tester.positions))
            )
            
        except Exception as e:
            messagebox.showerror(self.t('error'), str(e))
            self.status_label.config(text=self.t('run_failed'), fg="red")
    
    def show_overview(self):
        """展示总览报表文本（包括投资组合情况与压力测试汇总）"""
        t = self.t
        
        total_long = sum(p.notional_usd for p in self.tester.positions if p.is_long)
        total_short = sum(p.notional_usd for p in self.tester.positions if not p.is_long)
        net = total_long - total_short
        gross = total_long + total_short
        
        report = f"""
{'='*65}
         {t('report_header')}
{'='*65}

{t('portfolio_overview')}
  {t('total_positions'):<20s} {len(self.tester.positions)}
  {t('long_notional'):<20s} ${total_long:,.2f}
  {t('short_notional'):<20s} ${total_short:,.2f}
  {t('net_exposure'):<20s} ${net:,.2f}
  {t('gross_exposure'):<20s} ${gross:,.2f}

{t('stress_results')}
  {t('shock_10'):<20s} ${gross * 0.10:,.2f}
  {t('shock_15'):<20s} ${gross * 0.15:,.2f}
  {t('shock_20'):<20s} ${gross * 0.20:,.2f}
"""

        # 仅在存在财务摘要时将财务汇总附加到概览尾部，以保持一致的排版风格
        if self.tester.financial_summary:
            total_equity_usd = sum(fs.equity_balance_usd for fs in self.tester.financial_summary)
            total_net_equity_usd = sum(fs.net_equity_usd for fs in self.tester.financial_summary)
            total_im_usd = sum(fs.im_amt_usd for fs in self.tester.financial_summary)
            total_mm_usd = sum(fs.mm_amt_usd for fs in self.tester.financial_summary)
            total_excess_usd = sum(fs.margin_excess_usd for fs in self.tester.financial_summary)
            
            margin_ratio = (total_im_usd / total_net_equity_usd * 100) if total_net_equity_usd else 0
            
            report += f"""
{'-'*65}
{t('equity_balance_label'):<30s} ${total_equity_usd:>16,.2f}
{t('net_equity_label'):<30s} ${total_net_equity_usd:>16,.2f}
{t('im_label'):<30s} ${total_im_usd:>16,.2f}
{t('margin_excess_label'):<30s} ${total_excess_usd:>16,.2f}

{t('margin_util'):<30s} {margin_ratio:>.1f}%
"""
        
        report += f"\n{'='*65}\n"
        
        self.overview_text.delete(1.0, tk.END)
        self.overview_text.insert(1.0, report)
    
    def show_financial_summary(self):
        """展示财务摘要报表，并填充数据至表格中"""
        t = self.t
        self.fin_text.delete(1.0, tk.END)
        for item in self.fin_tree.get_children():
            self.fin_tree.delete(item)
            
        if not self.tester.financial_summary:
            self.fin_text.insert(1.0, t('fin_not_loaded'))
            return
            
        total_equity_usd = sum(fs.equity_balance_usd for fs in self.tester.financial_summary)
        total_net_equity_usd = sum(fs.net_equity_usd for fs in self.tester.financial_summary)
        total_im_usd = sum(fs.im_amt_usd for fs in self.tester.financial_summary)
        total_mm_usd = sum(fs.mm_amt_usd for fs in self.tester.financial_summary)
        total_excess_usd = sum(fs.margin_excess_usd for fs in self.tester.financial_summary)
        total_unrealised_usd = sum(f.equity_balance_usd - f.ledger_cf_usd for f in self.tester.financial_summary)
        
        margin_ratio = (total_im_usd / total_net_equity_usd * 100) if total_net_equity_usd else 0
        
        summary_text = f"""
{'='*65}
  {t('fin_summary_title')}
{'='*65}

  {t('equity_balance_label'):<35s} ${total_equity_usd:>16,.2f}
  {t('net_equity_label'):<35s} ${total_net_equity_usd:>16,.2f}
  {t('im_label'):<35s} ${total_im_usd:>16,.2f}
  {t('mm_label'):<35s} ${total_mm_usd:>16,.2f}
  {t('margin_excess_label'):<35s} ${total_excess_usd:>16,.2f}
  {t('unrealised_pnl_label'):<35s} ${total_unrealised_usd:>16,.2f}

  {t('margin_util'):<35s} {margin_ratio:>16.1f}%

{'='*65}
  {t('fin_detail_header')}
"""
        self.fin_text.insert(1.0, summary_text)
        
        # 填充表格内容
        for fs in sorted(self.tester.financial_summary, key=lambda x: abs(x.net_equity_usd), reverse=True):
            if abs(fs.ledger_cf) < 0.01 and abs(fs.equity_balance) < 0.01:
                continue
            self.fin_tree.insert('', tk.END, values=(
                fs.currency,
                f"{fs.ledger_cf:,.2f}",
                f"{fs.unrealised_pnl:,.2f}",
                f"{fs.equity_balance:,.2f}",
                f"{fs.net_equity:,.2f}",
                f"{fs.im_amt:,.2f}",
                f"{fs.mm_amt:,.2f}",
                f"{fs.margin_excess:,.2f}",
                f"{fs.exch_rate:.6f}",
                f"${fs.net_equity_usd:,.2f}"
            ))
            
        self.fin_tree.insert('', tk.END, values=(
            t('total_usd'),
            "",
            f"${total_unrealised_usd:,.2f}",
            f"${total_equity_usd:,.2f}",
            f"${total_net_equity_usd:,.2f}",
            f"${total_im_usd:,.2f}",
            f"${total_mm_usd:,.2f}",
            f"${total_excess_usd:,.2f}",
            "",
            f"${total_net_equity_usd:,.2f}"
        ), tags=('total',))
        self.fin_tree.tag_configure('total', background='#E3F2FD', font=("Arial", 9, "bold"))
        
    def show_products(self):
        """清洗并填充产品明细标签页中的数据"""
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
        """清洗并填充分组类别标签页中的数据"""
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
            
        categories = self.tester.aggregate_by_category()
        total_notional = 0
        for cat, data in sorted(categories.items()):
            notional = data['notional']
            total_notional += notional
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
            
        # 添加全部分类的合计行
        self.category_tree.insert('', tk.END, values=(
            "TOTAL" if self.lang == 'en' else "合计", "", "", "",
            f"${total_notional:,.0f}",
            f"${total_notional * 0.10:,.0f}",
            f"${total_notional * 0.15:,.0f}",
            f"${total_notional * 0.20:,.0f}"
        ), tags=('total',))
        self.category_tree.tag_configure('total', background='#E3F2FD', font=("Arial", 9, "bold"))
        
    def export_reports(self):
        """处理一键导出产品汇总与分类汇总报告"""
        t = self.t
        if not self.tester.positions:
            messagebox.showerror(t('error'), t('no_data_export'))
            return
            
        export_dir = filedialog.askdirectory(title=t('select_export_dir'))
        if not export_dir:
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d")
            product_file = Path(export_dir) / f"AllAccounts_{timestamp}_Product_StressTest.csv"
            category_file = Path(export_dir) / f"AllAccounts_{timestamp}_Category_StressTest.csv"
            
            self.tester.export_product_csv(str(product_file))
            self.tester.export_category_csv(str(category_file))
            
            messagebox.showinfo(
                t('export_success'),
                t('export_msg').format(product_file.name, category_file.name)
            )
        except Exception as e:
            messagebox.showerror(t('export_failed'), str(e))


def main():
    """主程序入口，启动 GUI 应用进程"""
    root = tk.Tk()
    app = RiskStressTestGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()