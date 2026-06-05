# -*- coding: utf-8 -*-
"""
月度批量风险分析报告生成器
读取文件夹中整月的持仓和财务数据，生成交互式 HTML 报告
包含：Overview 汇总、Category Summary 饼图、每日趋势图、产品明细等
"""

import csv
import os
import glob
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


# ========== 汇率与分类定义（复用 merged 逻辑） ==========
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

exchange_rates = {
    'AUD': 0.7205, 'CAD': 1/1.3718, 'CHF': 1/0.7837, 'CNH': 1/6.8377,
    'DKK': 1/6.4216, 'EUR': 1.1671, 'GBP': 1.3516, 'HKD': 1/7.842,
    'IDR': 1/17705.16, 'INR': 1/95.4304, 'JPY': 1/157.4394,
    'KRW': 1/1465.3989, 'MYR': 1/3.9603, 'NOK': 1/9.3939,
    'NZD': 0.5925, 'PHP': 1/61.1367, 'SEK': 1/9.3281,
    'SGD': 1/1.2738, 'THB': 1/32.6356, 'TRY': 1/45.6068,
    'TWD': 1/31.572, 'USD': 1.0000,
}

cross_rates = {
    'AUD/HKD': 5.643, 'EUR/HKD': 9.141,
    'GBP/HKD': 10.5858, 'NZD/HKD': 4.6407,
}


def convert_to_usd(amount, from_currency):
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


# ========== 数据加载 ==========
def load_positions(filepath, client_filter='PHL9000'):
    """加载持仓文件，返回列表"""
    positions = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                client = row.get('Client_No', row.get('Client', ''))
                if client != client_filter:
                    continue
                com_type = row.get('Com_Type', '').upper()
                if com_type not in ('F', 'X'):
                    continue

                com_cd = row.get('Com_cd', '')
                exch_cd = row.get('Exch_Cd', '')
                contract_month = row.get('Contract_Month', '').strip()
                buy_sell = row.get('Buy_Sell', 'B')
                qty = float(row.get('Traded_Qty', 0))
                if buy_sell == 'S':
                    qty = -qty

                tick_value = float(row.get('Tick_Value', 1))
                currency = row.get('Settle_Curr_Cd', 'USD')
                category = CATEGORY_MAP.get(com_cd, 'Other')

                if com_type == 'X':
                    if 'Cumulative_Swap' in row and row['Cumulative_Swap'].strip():
                        calc_price = float(row['Cumulative_Swap'])
                    else:
                        calc_price = float(row.get('Settlement_Price', row.get('Traded_Price', 0)))
                else:
                    calc_price = float(row.get('Settlement_Price', row.get('Traded_Price', 0)))

                price = float(row.get('Settlement_Price', row.get('Traded_Price', 0)))
                notional = abs(qty) * price * tick_value
                equity = qty * calc_price * tick_value

                positions.append({
                    'client_id': client,
                    'com_cd': com_cd,
                    'exch_cd': exch_cd,
                    'contract_month': contract_month,
                    'contract': f"{com_cd} {contract_month}" if contract_month else com_cd,
                    'quantity': qty,
                    'price': price,
                    'currency': currency,
                    'category': category,
                    'tick_value': tick_value,
                    'com_type': com_type,
                    'notional_usd': convert_to_usd(notional, currency),
                    'equity_usd': convert_to_usd(equity, currency),
                    'is_long': qty > 0,
                })
    except Exception as e:
        print(f"  [WARN] Failed to load {filepath}: {e}")
    return positions


def load_financial_summary(filepath, client_filter='PHL9000'):
    """加载财务摘要文件"""
    summaries = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                client = row.get('Client_No', '')
                if client != client_filter:
                    continue
                currency = row.get('Curr_Cd', 'USD')
                summaries.append({
                    'client_id': client,
                    'currency': currency,
                    'ledger_cf': float(row.get('Ledger_Cf', 0)),
                    'unrealised_pnl': float(row.get('Unrealised_Profit_Loss', 0)),
                    'equity_balance': float(row.get('Equity_Balance', 0)),
                    'net_equity': float(row.get('NetEquity', 0)),
                    'im_amt': float(row.get('Im_Amt', 0)),
                    'mm_amt': float(row.get('MM_Amt', 0)),
                    'margin_excess': float(row.get('Margin_Excess', 0)),
                    'exch_rate': float(row.get('Exch_Rate', 1)),
                    'equity_balance_usd': float(row.get('Equity_Balance(BASE_USD)', 0)),
                    'net_equity_usd': float(row.get('NetEquity(BASE_USD)', 0)),
                    'im_amt_usd': float(row.get('Im_Amt(BASE_USD)', 0)),
                    'mm_amt_usd': float(row.get('MM_Amt(BASE_USD)', 0)),
                    'margin_excess_usd': float(row.get('Margin_Excess(BASE_USD)', 0)),
                    'ledger_cf_usd': float(row.get('Ledger_Cf(BASE_USD)', 0)),
                })
    except Exception as e:
        print(f"  [WARN] Failed to load {filepath}: {e}")
    return summaries


# ========== 聚合计算 ==========
def aggregate_by_product(positions):
    """按合约精准聚合持仓 (分组逻辑：Exch_Cd + Com_cd + Contract_Month)"""
    products = {}
    for p in positions:
        group_key = f"{p['exch_cd']}_{p['com_cd']}_{p['contract_month']}"
        if group_key not in products:
            products[group_key] = {
                'category': p['category'],
                'product_code': p['contract'],
                'currency': p['currency'],
                'long': 0, 'short': 0, 'net': 0,
                'notional_usd': 0, 'net_notional_usd': 0
            }
        products[group_key]['long'] += p['quantity'] if p['quantity'] > 0 else 0
        products[group_key]['short'] += abs(p['quantity']) if p['quantity'] < 0 else 0
        products[group_key]['net'] += p['quantity']
        products[group_key]['notional_usd'] += p['notional_usd']
        net_value = p['quantity'] * p['price'] * p['tick_value']
        products[group_key]['net_notional_usd'] += convert_to_usd(net_value, p['currency'])
    return products


def aggregate_by_product_category(positions):
    """按产品分类聚合持仓 (分组逻辑：Exch_Cd + Com_cd + Currency，忽略合约月份)
    同一产品不同月份可对冲，Net 使用代数和
    """
    products = {}
    for p in positions:
        group_key = f"{p['exch_cd']}_{p['com_cd']}_{p['currency']}"
        if group_key not in products:
            products[group_key] = {
                'category': p['category'],
                'product_code': p['com_cd'],
                'exch_cd': p['exch_cd'],
                'currency': p['currency'],
                'long': 0, 'short': 0, 'net': 0,
                'notional_usd': 0, 'net_notional_usd': 0
            }
        products[group_key]['long'] += p['quantity'] if p['quantity'] > 0 else 0
        products[group_key]['short'] += abs(p['quantity']) if p['quantity'] < 0 else 0
        products[group_key]['net'] += p['quantity']
        products[group_key]['notional_usd'] += p['notional_usd']
        net_value = p['quantity'] * p['price'] * p['tick_value']
        products[group_key]['net_notional_usd'] += convert_to_usd(net_value, p['currency'])
    return products


def aggregate_by_category(positions):
    """按类别聚合持仓"""
    categories = {}
    for p in positions:
        cat = p['category']
        if cat not in categories:
            categories[cat] = {'long': 0, 'short': 0, 'net': 0,
                               'notional_usd': 0, 'net_notional_usd': 0}
        categories[cat]['long'] += p['quantity'] if p['quantity'] > 0 else 0
        categories[cat]['short'] += abs(p['quantity']) if p['quantity'] < 0 else 0
        categories[cat]['net'] += p['quantity']
        categories[cat]['notional_usd'] += p['notional_usd']
        net_value = p['quantity'] * p['price'] * p['tick_value']
        categories[cat]['net_notional_usd'] += convert_to_usd(net_value, p['currency'])
    return categories


def compute_overview(positions, fin_summary):
    """计算单日 Overview 指标"""
    total_long = sum(p['notional_usd'] for p in positions if p['is_long'])
    total_short = sum(p['notional_usd'] for p in positions if not p['is_long'])
    gross = total_long + total_short
    categories = aggregate_by_category(positions)
    net_exposure = sum(abs(d['net_notional_usd']) for d in categories.values())

    total_equity_usd = sum(f['equity_balance_usd'] for f in fin_summary)
    total_net_equity_usd = sum(f['net_equity_usd'] for f in fin_summary)
    total_im_usd = sum(f['im_amt_usd'] for f in fin_summary)
    total_mm_usd = sum(f['mm_amt_usd'] for f in fin_summary)
    total_excess_usd = sum(f['margin_excess_usd'] for f in fin_summary)
    total_unrealised_usd = sum(f['equity_balance_usd'] - f['ledger_cf_usd'] for f in fin_summary)
    margin_ratio = (total_im_usd / total_equity_usd * 100) if total_equity_usd else 0

    return {
        'total_positions': len(positions),
        'long_notional': total_long,
        'short_notional': total_short,
        'gross_exposure': gross,
        'net_exposure': net_exposure,
        'equity_balance_usd': total_equity_usd,
        'net_equity_usd': total_net_equity_usd,
        'unrealised_pnl_usd': total_unrealised_usd,
        'im_amt_usd': total_im_usd,
        'mm_amt_usd': total_mm_usd,
        'margin_excess_usd': total_excess_usd,
        'margin_ratio': margin_ratio,
    }


# ========== 主逻辑 ==========
def scan_and_process(data_dir, client_filter='PHL9000'):
    """扫描文件夹，逐日处理，返回每日汇总"""
    pos_pattern = os.path.join(data_dir, f"PHILLIP_Open_Position_{client_filter}_*.csv")
    pos_files = sorted(glob.glob(pos_pattern))

    daily_results = []
    for pf in pos_files:
        fname = os.path.basename(pf)
        # 从文件名提取日期
        date_str = fname.replace('.csv', '').split('_')[-1]
        if len(date_str) != 8:
            continue
        date_label = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

        # 对应的财务文件
        fin_file = os.path.join(data_dir, f"PHILLIP_Financial_Summary_{client_filter}_{date_str}.csv")

        print(f"  Processing {date_label} ...")
        positions = load_positions(pf, client_filter)
        fin_summary = load_financial_summary(fin_file, client_filter) if os.path.exists(fin_file) else []

        if not positions:
            print(f"    No positions, skipping.")
            continue

        overview = compute_overview(positions, fin_summary)
        overview['date'] = date_label
        overview['date_str'] = date_str
        overview['categories'] = aggregate_by_category(positions)
        overview['products'] = aggregate_by_product(positions)
        overview['product_categories'] = aggregate_by_product_category(positions)
        overview['positions_count'] = len(positions)

        daily_results.append(overview)

    return daily_results


# ========== HTML 报告生成 ==========
def fmt_money(v):
    """格式化金额（统一使用美元数字格式）"""
    return f"${v:,.0f}"


def generate_html_report(daily_results, output_path):
    """生成交互式 HTML 报告"""
    if not daily_results:
        print("No data to generate report.")
        return

    dates = [r['date'] for r in daily_results]

    # ---- 1. Overview 趋势图 ----
    fig_overview = make_subplots(
        rows=2, cols=2,
        subplot_titles=('敞口趋势 (Exposure Trend, USD)', '财务趋势 (Financial Trend, USD)',
                        '保证金使用率 (Margin Usage, %)', '持仓数量 (Position Count)'),
        vertical_spacing=0.14, horizontal_spacing=0.08
    )

    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['gross_exposure'] for r in daily_results],
        name='总敞口 (Gross)', line=dict(color='#2196F3', width=2),
        hovertemplate='%{x}<br>Gross: $%{y:,.0f}<extra></extra>'
    ), row=1, col=1)
    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['net_exposure'] for r in daily_results],
        name='净敞口 (Net)', line=dict(color='#FF9800', width=2),
        hovertemplate='%{x}<br>Net: $%{y:,.0f}<extra></extra>'
    ), row=1, col=1)
    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['long_notional'] for r in daily_results],
        name='多头 (Long)', line=dict(color='#4CAF50', width=1.5, dash='dot'),
    ), row=1, col=1)
    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['short_notional'] for r in daily_results],
        name='空头 (Short)', line=dict(color='#f44336', width=1.5, dash='dot'),
    ), row=1, col=1)

    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['equity_balance_usd'] for r in daily_results],
        name='权益余额 (Equity)', line=dict(color='#2196F3', width=2),
    ), row=1, col=2)
    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['net_equity_usd'] for r in daily_results],
        name='净权益 (Net Equity)', line=dict(color='#9C27B0', width=2),
    ), row=1, col=2)
    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['unrealised_pnl_usd'] for r in daily_results],
        name='未实现盈亏 (Unrealised PnL)', line=dict(color='#FF5722', width=1.5),
    ), row=1, col=2)
    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['margin_excess_usd'] for r in daily_results],
        name='超额保证金 (Margin Excess)', line=dict(color='#4CAF50', width=1.5),
    ), row=1, col=2)
    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['im_amt_usd'] for r in daily_results],
        name='初始保证金 (IM)', line=dict(color='#E91E63', width=1.5),
        hovertemplate='%{x}<br>IM: $%{y:,.0f}<extra></extra>'
    ), row=1, col=2)
    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['mm_amt_usd'] for r in daily_results],
        name='维持保证金 (MM)', line=dict(color='#795548', width=1.5),
        hovertemplate='%{x}<br>MM: $%{y:,.0f}<extra></extra>'
    ), row=1, col=2)

    fig_overview.add_trace(go.Scatter(
        x=dates, y=[r['margin_ratio'] for r in daily_results],
        name='保证金使用率 (Margin %)', line=dict(color='#f44336', width=2),
        fill='tozeroy', fillcolor='rgba(244,67,54,0.1)',
    ), row=2, col=1)

    fig_overview.add_trace(go.Bar(
        x=dates, y=[r['total_positions'] for r in daily_results],
        name='持仓数量 (Positions)', marker_color='#607D8B',
    ), row=2, col=2)

    # 统一修复 x 轴和 y 轴格式
    fig_overview.update_xaxes(tickangle=-45, tickformat='%m-%d', dtick=86400000, row=1, col=1)
    fig_overview.update_xaxes(tickangle=-45, tickformat='%m-%d', dtick=86400000, row=1, col=2)
    fig_overview.update_xaxes(tickangle=-45, tickformat='%m-%d', dtick=86400000, row=2, col=1)
    fig_overview.update_xaxes(tickangle=-45, tickformat='%m-%d', dtick=86400000, row=2, col=2)
    fig_overview.update_yaxes(tickformat='$,.0f', row=1, col=1)
    fig_overview.update_yaxes(tickformat='$,.0f', row=1, col=2)
    fig_overview.update_yaxes(ticksuffix='%', row=2, col=1)

    fig_overview.update_layout(
        height=750, title_text='每日趋势总览 (Daily Overview)',
        template='plotly_white', showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.22, xanchor='center', x=0.5),
        margin=dict(b=120)
    )

    # ---- 2. Category Summary（取最新一天做饼图）----
    latest = daily_results[-1]
    cats = latest['categories']

    # 总敞口饼图
    fig_gross_pie = go.Figure(data=[go.Pie(
        labels=list(cats.keys()),
        values=[abs(d['notional_usd']) for d in cats.values()],
        hole=0.4,
        textinfo='label+percent',
        hovertemplate='%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>',
        marker=dict(colors=px.colors.qualitative.Set2),
    )])
    fig_gross_pie.update_layout(
        title_text=f'各类别总敞口 (Gross Notional) ({latest["date"]})',
        height=450, template='plotly_white'
    )

    # 净敞口饼图
    fig_net_pie = go.Figure(data=[go.Pie(
        labels=list(cats.keys()),
        values=[abs(d['net_notional_usd']) for d in cats.values()],
        hole=0.4,
        textinfo='label+percent',
        hovertemplate='%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>',
        marker=dict(colors=px.colors.qualitative.Pastel1),
    )])
    fig_net_pie.update_layout(
        title_text=f'各类别净敞口 (Net Notional) ({latest["date"]})',
        height=450, template='plotly_white'
    )

    # 各类别随时间变化 - 总敞口趋势图
    all_cats_set = set()
    for r in daily_results:
        all_cats_set.update(r['categories'].keys())
    all_cats = sorted(all_cats_set)

    colors = px.colors.qualitative.Set3

    fig_gross_trend = go.Figure()
    for i, cat in enumerate(all_cats):
        vals = []
        for r in daily_results:
            c = r['categories'].get(cat, {})
            vals.append(abs(c.get('notional_usd', 0)))
        fig_gross_trend.add_trace(go.Scatter(
            x=dates, y=vals, name=cat, stackgroup='one',
            line=dict(width=0.5, color=colors[i % len(colors)]),
            fillcolor=colors[i % len(colors)],
            hovertemplate=f'{cat}<br>%{{x}}<br>$%{{y:,.0f}}<extra></extra>'
        ))
    fig_gross_trend.update_xaxes(tickangle=-45, tickformat='%m-%d', dtick=86400000)
    fig_gross_trend.update_yaxes(tickformat='$,.0f')
    fig_gross_trend.update_layout(
        title_text='各类别总敞口趋势 (Gross Notional Over Time)',
        height=500, template='plotly_white', yaxis_title='USD',
        legend=dict(orientation='h', yanchor='top', y=-0.28, xanchor='center', x=0.5),
        margin=dict(b=150)
    )

    # 各类别随时间变化 - 净敞口趋势图
    fig_net_trend = go.Figure()
    for i, cat in enumerate(all_cats):
        vals = []
        for r in daily_results:
            c = r['categories'].get(cat, {})
            vals.append(abs(c.get('net_notional_usd', 0)))
        fig_net_trend.add_trace(go.Scatter(
            x=dates, y=vals, name=cat, stackgroup='one',
            line=dict(width=0.5, color=colors[i % len(colors)]),
            fillcolor=colors[i % len(colors)],
            hovertemplate=f'{cat}<br>%{{x}}<br>$%{{y:,.0f}}<extra></extra>'
        ))
    fig_net_trend.update_xaxes(tickangle=-45, tickformat='%m-%d', dtick=86400000)
    fig_net_trend.update_yaxes(tickformat='$,.0f')
    fig_net_trend.update_layout(
        title_text='各类别净敞口趋势 (Net Notional Over Time)',
        height=500, template='plotly_white', yaxis_title='USD',
        legend=dict(orientation='h', yanchor='top', y=-0.28, xanchor='center', x=0.5),
        margin=dict(b=150)
    )

    # ---- 3. Overview 数据表格（交互式） ----
    overview_headers = ['Date', 'Positions', 'Long ($)', 'Short ($)', 'Gross ($)',
                        'Net ($)', 'Equity ($)', 'Unrealised PnL ($)',
                        'IM ($)', 'MM ($)', 'Excess ($)', 'Margin %']
    overview_rows = []
    for r in daily_results:
        overview_rows.append([
            r['date'], r['total_positions'],
            f"${r['long_notional']:,.0f}", f"${r['short_notional']:,.0f}",
            f"${r['gross_exposure']:,.0f}", f"${r['net_exposure']:,.0f}",
            f"${r['equity_balance_usd']:,.0f}", f"${r['unrealised_pnl_usd']:,.0f}",
            f"${r['im_amt_usd']:,.0f}", f"${r['mm_amt_usd']:,.0f}",
            f"${r['margin_excess_usd']:,.0f}", f"{r['margin_ratio']:.1f}%",
        ])

    # ---- 4. Product Details 表格（最新一天）----
    latest_products = latest.get('products', {})
    prod_headers = ['Product', 'Category', 'Currency', 'Long', 'Short', 'Net',
                    'Gross ($)', 'Net ($)', 'Gross_10%', 'Gross_15%', 'Gross_20%',
                    'Net_10%', 'Net_15%', 'Net_20%']
    prod_rows = []
    for key, d in sorted(latest_products.items()):
        g = d['notional_usd']
        n = d['net_notional_usd']
        prod_rows.append([
            d['product_code'], d['category'], d['currency'],
            int(d['long']), int(d['short']), int(d['net']),
            f"${g:,.0f}", f"${n:,.0f}",
            f"${g*0.10:,.0f}", f"${g*0.15:,.0f}", f"${g*0.20:,.0f}",
            f"${abs(n)*0.10:,.0f}", f"${abs(n)*0.15:,.0f}", f"${abs(n)*0.20:,.0f}",
        ])

    # ---- 5. Product Category Summary 表格（最新一天）----
    latest_prod_cats = latest.get('product_categories', {})
    pc_headers = ['Product', 'Category', 'Exch', 'Currency', 'Long', 'Short', 'Net',
                  'Gross ($)', 'Net ($)', 'Gross_10%', 'Gross_15%', 'Gross_20%',
                  'Net_10%', 'Net_15%', 'Net_20%']
    pc_rows = []
    for key, d in sorted(latest_prod_cats.items()):
        g = d['notional_usd']
        n = d['net_notional_usd']
        pc_rows.append([
            d['product_code'], d['category'], d['exch_cd'], d['currency'],
            int(d['long']), int(d['short']), int(d['net']),
            f"${g:,.0f}", f"${n:,.0f}",
            f"${g*0.10:,.0f}", f"${g*0.15:,.0f}", f"${g*0.20:,.0f}",
            f"${abs(n)*0.10:,.0f}", f"${abs(n)*0.15:,.0f}", f"${abs(n)*0.20:,.0f}",
        ])

    # ---- 6. Category Summary 表格 ----
    cat_headers = ['Category', 'Long', 'Short', 'Net', 'Gross ($)', 'Net ($)',
                   'Gross_10%', 'Gross_15%', 'Gross_20%',
                   'Net_10%', 'Net_15%', 'Net_20%']
    cat_rows = []
    total_gross_cat = 0
    total_net_cat = 0
    total_long_cat = 0
    total_short_cat = 0
    total_net_qty_cat = 0
    for cat in sorted(cats.keys()):
        d = cats[cat]
        g = d['notional_usd']
        n = d['net_notional_usd']
        total_gross_cat += g
        total_net_cat += abs(n)
        total_long_cat += d['long']
        total_short_cat += d['short']
        total_net_qty_cat += d['net']
        cat_rows.append([
            cat, int(d['long']), int(d['short']), int(d['net']),
            f"${g:,.0f}", f"${abs(n):,.0f}",
            f"${g*0.10:,.0f}", f"${g*0.15:,.0f}", f"${g*0.20:,.0f}",
            f"${abs(n)*0.10:,.0f}", f"${abs(n)*0.15:,.0f}", f"${abs(n)*0.20:,.0f}",
        ])
    cat_rows.append([
        'TOTAL', int(total_long_cat), int(total_short_cat), int(total_net_qty_cat),
        f"${total_gross_cat:,.0f}", f"${abs(total_net_cat):,.0f}",
        f"${total_gross_cat*0.10:,.0f}", f"${total_gross_cat*0.15:,.0f}", f"${total_gross_cat*0.20:,.0f}",
        f"${total_net_cat*0.10:,.0f}", f"${total_net_cat*0.15:,.0f}", f"${total_net_cat*0.20:,.0f}",
    ])

    # ---- 7. 组装 HTML ----
    overview_chart_html = fig_overview.to_html(full_html=False, include_plotlyjs=False)
    gross_pie_html = fig_gross_pie.to_html(full_html=False, include_plotlyjs=False)
    net_pie_html = fig_net_pie.to_html(full_html=False, include_plotlyjs=False)
    gross_trend_html = fig_gross_trend.to_html(full_html=False, include_plotlyjs=False)
    net_trend_html = fig_net_trend.to_html(full_html=False, include_plotlyjs=False)

    def make_table(headers, rows, table_id):
        th = ''.join(f'<th onclick="sortTable(\'{table_id}\', {i})">{h} <span class="sort-arrow">⇅</span></th>'
                      for i, h in enumerate(headers))
        trs = ''
        for row in rows:
            is_total = row[0] in ('TOTAL', '合计')
            cls = ' class="total-row"' if is_total else ''
            tds = ''.join(f'<td>{cell}</td>' for cell in row)
            trs += f'<tr{cls}>{tds}</tr>\n'
        return f'''<table id="{table_id}">
            <thead><tr>{th}</tr></thead>
            <tbody>{trs}</tbody>
        </table>'''

    overview_table_html = make_table(overview_headers, overview_rows, 'overviewTable')
    prod_table_html = make_table(prod_headers, prod_rows, 'productTable')
    pc_table_html = make_table(pc_headers, pc_rows, 'productCatTable')
    cat_table_html = make_table(cat_headers, cat_rows, 'categoryTable')

    # ---- 最新一天摘要卡片 ----
    latest_r = daily_results[-1]
    first_r = daily_results[0]
    gross_change = latest_r['gross_exposure'] - first_r['gross_exposure']
    equity_change = latest_r['equity_balance_usd'] - first_r['equity_balance_usd']

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>月度风险分析报告</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f5f7fa; color: #333; }}
        .header {{ background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%);
                   color: white; padding: 30px 40px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 5px; }}
        .header p {{ opacity: 0.85; font-size: 14px; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}

        /* 摘要卡片 */
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                  gap: 15px; margin: 20px 0; }}
        .card {{ background: white; border-radius: 10px; padding: 20px;
                 box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                 border-left: 4px solid #2196F3; }}
        .card.green {{ border-left-color: #4CAF50; }}
        .card.orange {{ border-left-color: #FF9800; }}
        .card.red {{ border-left-color: #f44336; }}
        .card.purple {{ border-left-color: #9C27B0; }}
        .card .label {{ font-size: 12px; color: #888; text-transform: uppercase; margin-bottom: 5px; }}
        .card .value {{ font-size: 22px; font-weight: 700; }}
        .card .change {{ font-size: 12px; margin-top: 4px; }}
        .card .change.up {{ color: #4CAF50; }}
        .card .change.down {{ color: #f44336; }}

        /* Section */
        .section {{ background: white; border-radius: 10px; margin: 20px 0;
                    padding: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .section h2 {{ font-size: 18px; margin-bottom: 15px; color: #1a237e;
                       border-bottom: 2px solid #e8eaf6; padding-bottom: 8px; }}
        .section h3 {{ font-size: 15px; margin: 15px 0 10px; color: #37474f; }}

        /* 表格 */
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background: #e8eaf6; color: #1a237e; padding: 10px 8px; text-align: left;
              cursor: pointer; user-select: none; position: sticky; top: 0; }}
        th:hover {{ background: #c5cae9; }}
        .sort-arrow {{ font-size: 10px; opacity: 0.5; }}
        td {{ padding: 8px; border-bottom: 1px solid #eee; text-align: right; }}
        td:first-child {{ text-align: left; font-weight: 500; }}
        tr:hover {{ background: #f5f5f5; }}
        .total-row {{ background: #e3f2fd !important; font-weight: 700; }}
        .table-wrapper {{ max-height: 500px; overflow-y: auto; border: 1px solid #e0e0e0;
                          border-radius: 8px; }}

        /* Tab */
        .tabs {{ display: flex; gap: 5px; margin-bottom: 15px; }}
        .tab-btn {{ padding: 8px 20px; border: none; background: #e8eaf6; color: #1a237e;
                    border-radius: 6px 6px 0 0; cursor: pointer; font-size: 13px; }}
        .tab-btn.active {{ background: #1a237e; color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* 双列布局 */
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}

        /* 图表容器 */
        .chart-container {{ width: 100%; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 月度风险分析报告</h1>
        <p>PHL9000 | {first_r['date']} ~ {latest_r['date']} | {len(daily_results)} 个交易日 (Trading Days)</p>
    </div>

    <div class="container">
        <!-- 摘要卡片 -->
        <div class="cards">
            <div class="card">
                <div class="label">最新交易日 (Latest Date)</div>
                <div class="value">{latest_r['date']}</div>
            </div>
            <div class="card green">
                <div class="label">总敞口 (Gross)</div>
                <div class="value">{fmt_money(latest_r['gross_exposure'])}</div>
                <div class="change {"up" if gross_change > 0 else "down"}">月变动: {fmt_money(gross_change)}</div>
            </div>
            <div class="card orange">
                <div class="label">净敞口 (Net)</div>
                <div class="value">{fmt_money(latest_r['net_exposure'])}</div>
            </div>
            <div class="card purple">
                <div class="label">权益余额 (Equity)</div>
                <div class="value">{fmt_money(latest_r['equity_balance_usd'])}</div>
                <div class="change {"up" if equity_change > 0 else "down"}">月变动: {fmt_money(equity_change)}</div>
            </div>
            <div class="card red">
                <div class="label">保证金使用率 (Margin Usage)</div>
                <div class="value">{latest_r['margin_ratio']:.1f}%</div>
            </div>
            <div class="card">
                <div class="label">持仓数量 (Positions)</div>
                <div class="value">{latest_r['total_positions']}</div>
            </div>
        </div>

        <!-- 总览趋势 -->
        <div class="section">
            <h2>📈 每日趋势 (Daily Overview)</h2>
            <div class="chart-container">{overview_chart_html}</div>
        </div>

        <!-- Overview 数据表 -->
        <div class="section">
            <h2>📋 每日概览数据表 (Overview Data)</h2>
            <div class="table-wrapper">{overview_table_html}</div>
        </div>

        <!-- 产品明细 (Product Details) -->
        <div class="section">
            <h2>📦 产品明细 (Product Details) ({latest_r['date']})</h2>
            <p style="color:#888;font-size:12px;margin-bottom:10px;">分组：Exch + Com_cd + Contract_Month | Gross: 绝对值累加 | Net: 代数和（合约内可对冲）</p>
            <div class="table-wrapper">{prod_table_html}</div>
        </div>

        <!-- 产品分类汇总 (Product Category Summary) -->
        <div class="section">
            <h2>📊 产品分类汇总 (Product Category) ({latest_r['date']})</h2>
            <p style="color:#888;font-size:12px;margin-bottom:10px;">分组：Exch + Com_cd + Currency（忽略合约月份）| Gross: 绝对值累加 | Net: 代数和（同产品不同月份可对冲）</p>
            <div class="table-wrapper">{pc_table_html}</div>
        </div>

        <!-- Category Summary -->
        <div class="section">
            <h2>🏷️ 类别汇总 (Category Summary) ({latest_r['date']})</h2>
            <p style="color:#888;font-size:12px;margin-bottom:10px;">分组：Category (FX/Metals/...) | Gross: 绝对值累加 | Net: 绝对值相加（类别间不可对冲）</p>

            <div class="tabs">
                <button class="tab-btn active" onclick="switchTab(event, 'cat-table')">汇总表格 (Summary)</button>
                <button class="tab-btn" onclick="switchTab(event, 'cat-pie')">饼图 (Pie Chart)</button>
                <button class="tab-btn" onclick="switchTab(event, 'cat-gross-trend')">总敞口趋势 (Gross Trend)</button>
                <button class="tab-btn" onclick="switchTab(event, 'cat-net-trend')">净敞口趋势 (Net Trend)</button>
            </div>

            <div id="cat-table" class="tab-content active">
                <div class="table-wrapper">{cat_table_html}</div>
            </div>

            <div id="cat-pie" class="tab-content">
                <div class="grid-2">
                    <div>{gross_pie_html}</div>
                    <div>{net_pie_html}</div>
                </div>
            </div>

            <div id="cat-gross-trend" class="tab-content">
                <div class="chart-container">{gross_trend_html}</div>
            </div>

            <div id="cat-net-trend" class="tab-content">
                <div class="chart-container">{net_trend_html}</div>
            </div>
        </div>

        <!-- 页脚 -->
        <div style="text-align:center; padding:30px; color:#aaa; font-size:12px;">
            Generated by Monthly Risk Report Tool | {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>

    <script>
        // Tab 切换
        function switchTab(event, tabId) {{
            const section = event.target.closest('.section');
            section.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            section.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        }}

        // 表格排序
        let sortState = {{}};
        function sortTable(tableId, colIdx) {{
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr:not(.total-row)'));
            const totalRow = tbody.querySelector('.total-row');

            const key = tableId + '_' + colIdx;
            sortState[key] = sortState[key] === 'asc' ? 'desc' : 'asc';
            const dir = sortState[key] === 'asc' ? 1 : -1;

            rows.sort((a, b) => {{
                let va = a.cells[colIdx].textContent.replace(/[$,%MK]/g, '').trim();
                let vb = b.cells[colIdx].textContent.replace(/[$,%MK]/g, '').trim();
                let na = parseFloat(va), nb = parseFloat(vb);
                if (!isNaN(na) && !isNaN(nb)) return (na - nb) * dir;
                return va.localeCompare(vb) * dir;
            }});

            rows.forEach(r => tbody.appendChild(r));
            if (totalRow) tbody.appendChild(totalRow);

            // 更新排序箭头
            table.querySelectorAll('th .sort-arrow').forEach((s, i) => {{
                s.textContent = i === colIdx ? (sortState[key] === 'asc' ? '↑' : '↓') : '⇅';
            }});
        }}
    </script>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n✅ Report generated: {output_path}")


# ========== 入口 ==========
def main():
    import sys
    # 默认扫描脚本所在目录下的子文件夹
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        # 自动寻找包含持仓文件的目录
        script_dir = Path(__file__).parent
        candidates = list(script_dir.glob("PHILLIP_Open_Position_*/"))
        if candidates:
            data_dir = str(candidates[0])
        else:
            data_dir = str(script_dir)

    print(f"📂 Data directory: {data_dir}")
    print(f"{'='*60}")

    daily_results = scan_and_process(data_dir, 'PHL9000')

    if not daily_results:
        print("❌ No valid data found!")
        return

    # 输出路径
    output_name = f"Monthly_Risk_Report_{Path(data_dir).name}.html"
    output_path = str(Path(data_dir).parent / output_name)

    print(f"\n{'='*60}")
    print(f"📊 Generating HTML report ...")
    generate_html_report(daily_results, output_path)

    # 自动在浏览器中打开
    import webbrowser
    webbrowser.open('file://' + os.path.realpath(output_path))


if __name__ == '__main__':
    main()
