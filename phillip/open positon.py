# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 22:30:26 2026

@author: kunlave
"""

import pandas as pd
import numpy as np

# 读取CSV文件
file_path = r"C:\Users\hongl\Desktop\PHILLIP_Open_Position_PHL9000_20260504.csv"
df = pd.read_csv(file_path)

# ========== 添加汇率字典 ==========
# 从提供的汇率表创建字典，使用Buy价（中间价）
exchange_rates = {
    'AUD': 0.7205,  # AUD/USD Buy
    'CAD': 1/1.3718,  # USD/CAD Sell -> USD/CAD = 1/1.3718
    'CHF': 1/0.7837,  # USD/CHF Sell
    'CNH': 1/6.8377,  # USD/CNH Sell
    'DKK': 1/6.4216,  # USD/DKK Sell
    'EUR': 1.1671,  # EUR/USD Buy
    'GBP': 1.3516,  # GBP/USD Buy
    'HKD': 1/7.842,  # USD/HKD Sell
    'IDR': 1/17705.16,  # USD/IDR Sell (per 10000调整为per unit)
    'INR': 1/95.4304,  # USD/INR Sell
    'JPY': 1/157.4394,  # USD/JPY Sell
    'KRW': 1/1465.3989,  # USD/KRW Sell
    'MYR': 1/3.9603,  # USD/MYR Sell
    'NOK': 1/9.3939,  # USD/NOK Sell
    'NZD': 0.5925,  # NZD/USD Buy
    'PHP': 1/61.1367,  # USD/PHP Sell
    'SEK': 1/9.3281,  # USD/SEK Sell
    'SGD': 1/1.2738,  # USD/SGD Sell
    'THB': 1/32.6356,  # USD/THB Sell
    'TRY': 1/45.6068,  # USD/TRY Sell
    'TWD': 1/31.572,  # USD/TWD Sell
    'USD': 1.0000,  # USD基准
}

# 额外添加一些交叉汇率（如果Settle_Curr_Cd是交叉货币对）
cross_rates = {
    'AUD/HKD': 5.643,  # AUD/HKD Buy
    'EUR/HKD': 9.141,  # EUR/HKD Buy
    'GBP/HKD': 10.5858,  # GBP/HKD Buy
    'NZD/HKD': 4.6407,  # NZD/HKD Buy
}

def convert_to_usd(amount, from_currency):
    """
    将金额从from_currency转换为USD
    """
    if pd.isna(from_currency) or from_currency == '':
        return amount  # 如果没有货币信息报错
    
    # 单一货币
    if from_currency in exchange_rates:
        return amount * exchange_rates[from_currency]
    
    # 处理交叉汇率对（如 'AUD/HKD'）
    if '/' in from_currency:
        if from_currency in cross_rates:
            # 先转换为HKD，再转换为USD
            hkd_amount = amount * cross_rates[from_currency]
            usd_amount = hkd_amount * exchange_rates.get('HKD', 1/7.842)
            return usd_amount
        else:
            # 如果交叉汇率不在字典中，分割处理
            base, quote = from_currency.split('/')
            if base in exchange_rates and quote in exchange_rates:
                # 通过USD中转
                usd_amount = amount * exchange_rates[base] / exchange_rates[quote]
                return usd_amount
    
    else:
        # 如果货币不在汇率表中，打印警告并保持原值
        print(f"警告: 未找到货币 {from_currency} 的汇率，保持原值")
        return amount

print("原始数据形状:", df.shape)
print("\n各类型数量:")
print(df['Com_Type'].value_counts())

# 对于期货和远期合约，使用3列分组（不包括Strike_Price和Call_Put）
futures_contract_cols = ['Exch_Cd', 'Com_cd', 'Contract_Month']
# 对于期权，使用5列分组
options_contract_cols = ['Exch_Cd', 'Com_cd', 'Contract_Month', 'Strike_Price', 'Call_Put']

all_results = []

# 处理期货 (Com_Type = 'F')
futures_df = df[df['Com_Type'] == 'F']
print(f"\n处理期货，数量: {len(futures_df)}")

for name, group in futures_df.groupby(futures_contract_cols):
    # 计算买入总数和卖出总数
    buy_mask = group['Buy_Sell'] == 'B'
    sell_mask = group['Buy_Sell'] == 'S'
    
    buy_qty = group.loc[buy_mask, 'Traded_Qty'].sum()
    sell_qty = group.loc[sell_mask, 'Traded_Qty'].sum()
    
    # 获取结算价格和tick value
    settlement_price = group['Settlement_Price'].iloc[0]
    tick_value = group['Tick_Value'].iloc[0]
    settle_currency = group['Settle_Curr_Cd'].iloc[0]
    
    # 计算权益（考虑Tick_Value）
    buy_equity = buy_qty * settlement_price * tick_value
    sell_equity = -sell_qty * settlement_price * tick_value
    net_equity = buy_equity + sell_equity
    net_qty = buy_qty - sell_qty
    
    # 转换净权益为USD
    net_equity_usd = convert_to_usd(net_equity, settle_currency)
    
    result_row = {
        'Report_Date': group['Report_Date'].iloc[0],
        'Client_No': group['Client_No'].iloc[0],
        'Com_Type': 'F',
        'Exch_Cd': name[0],
        'Com_cd': name[1],
        'Contract_Month': name[2],
        'Strike_Price': '',  # 期货没有行权价
        'Call_Put': '',       # 期货没有看涨看跌
        'Settle_Curr_Cd': settle_currency,
        'Tick_Value': tick_value,
        'total_buy_qty': buy_qty,
        'total_sell_qty': sell_qty,
        'net_qty': net_qty,
        'buy_equity': buy_equity,
        'sell_equity': sell_equity,
        'net_equity': net_equity,
        'net_equity_usd': net_equity_usd  # 新增USD列
    }
    all_results.append(result_row)

print(f"期货处理后合约数量: {len([r for r in all_results if r['Com_Type'] == 'F'])}")

# 处理期权 (Com_Type = 'O')
options_df = df[df['Com_Type'] == 'O']
print(f"\n处理期权，数量: {len(options_df)}")

for name, group in options_df.groupby(options_contract_cols):
    # 计算买入总数和卖出总数
    buy_mask = group['Buy_Sell'] == 'B'
    sell_mask = group['Buy_Sell'] == 'S'
    
    buy_qty = group.loc[buy_mask, 'Traded_Qty'].sum()
    sell_qty = group.loc[sell_mask, 'Traded_Qty'].sum()
    
    # Nett_Option_Value 已经是处理好的权益（买入为正，卖出为负）
    buy_equity = group.loc[buy_mask, 'Nett_Option_Value'].sum()
    sell_equity = group.loc[sell_mask, 'Nett_Option_Value'].sum()
    
    # 总权益是所有Nett_Option_Value的和
    net_equity = group['Nett_Option_Value'].sum()
    net_qty = buy_qty - sell_qty
    
    # 获取结算价格
    settlement_price = group['Settlement_Price'].iloc[0]
    tick_value = group['Tick_Value'].iloc[0]
    settle_currency = group['Settle_Curr_Cd'].iloc[0]
    
    # 转换净权益为USD
    net_equity_usd = convert_to_usd(net_equity, settle_currency)
    
    result_row = {
        'Report_Date': group['Report_Date'].iloc[0],
        'Client_No': group['Client_No'].iloc[0],
        'Com_Type': 'O',
        'Exch_Cd': name[0],
        'Com_cd': name[1],
        'Contract_Month': name[2],
        'Strike_Price': name[3],
        'Call_Put': name[4],
        'Settlement_Price': settlement_price,
        'Settle_Curr_Cd': settle_currency,
        'Tick_Value': tick_value,
        'total_buy_qty': buy_qty,
        'total_sell_qty': sell_qty,
        'net_qty': net_qty,
        'buy_equity': buy_equity,
        'sell_equity': sell_equity,
        'net_equity': net_equity,
        'net_equity_usd': net_equity_usd  # 新增USD列
    }
    all_results.append(result_row)

print(f"期权处理后合约数量: {len([r for r in all_results if r['Com_Type'] == 'O'])}")

# 处理远期合约 (Com_Type = 'X')
forwards_df = df[df['Com_Type'] == 'X']
print(f"\n处理远期合约，数量: {len(forwards_df)}")

for name, group in forwards_df.groupby(futures_contract_cols):
    # 计算买入总数和卖出总数
    buy_mask = group['Buy_Sell'] == 'B'
    sell_mask = group['Buy_Sell'] == 'S'
    
    buy_qty = group.loc[buy_mask, 'Traded_Qty'].sum()
    sell_qty = group.loc[sell_mask, 'Traded_Qty'].sum()
    
    # 获取结算价格和tick value
    tick_value = group['Tick_Value'].iloc[0]
    
    # 远期合约使用Cumulative_Swap作为实际价值
    if 'Cumulative_Swap' in group.columns and not pd.isna(group['Cumulative_Swap'].iloc[0]):
        settlement_value = group['Cumulative_Swap'].iloc[0]
    else:
        settlement_value = group['Settlement_Price'].iloc[0]
    
    # 计算权益
    buy_equity = buy_qty * settlement_value * tick_value
    sell_equity = -sell_qty * settlement_value * tick_value
    
    net_qty = buy_qty - sell_qty
    net_equity = buy_equity + sell_equity
    
    # 设置结算货币（根据合约代码推断或使用默认）
    settle_currency = 'USD'  # 默认USD
    
    # 转换净权益为USD
    net_equity_usd = convert_to_usd(net_equity, settle_currency)
    
    result_row = {
        'Report_Date': group['Report_Date'].iloc[0],
        'Client_No': group['Client_No'].iloc[0],
        'Com_Type': 'X',
        'Exch_Cd': name[0],
        'Com_cd': name[1],
        'Contract_Month': name[2],
        'Strike_Price': '',  # 远期合约没有行权价
        'Call_Put': '',       # 远期合约没有看涨看跌
        'Settlement_Price': settlement_value,
        'Settle_Curr_Cd': settle_currency,
        'Tick_Value': tick_value,
        'total_buy_qty': buy_qty,
        'total_sell_qty': sell_qty,
        'net_qty': net_qty,
        'buy_equity': buy_equity,
        'sell_equity': sell_equity,
        'net_equity': net_equity,
        'net_equity_usd': net_equity_usd  # 新增USD列
    }
    all_results.append(result_row)

print(f"远期合约处理后合约数量: {len([r for r in all_results if r['Com_Type'] == 'X'])}")

# 转换为DataFrame
final_result = pd.DataFrame(all_results)

# 定义输出列的顺序
output_columns = ['Report_Date', 'Client_No', 'Com_Type', 'Exch_Cd', 'Com_cd', 
                  'Contract_Month', 'Strike_Price', 'Call_Put', 'Settlement_Price',
                  'Settle_Curr_Cd', 'Tick_Value', 'total_buy_qty', 'total_sell_qty',
                  'net_qty', 'buy_equity', 'sell_equity', 'net_equity', 'net_equity_usd']

# 确保所有列都存在
final_result = final_result[output_columns]

print(f"\n最终结果形状: {final_result.shape}")
print(f"\n各类型最终合约数量:")
print(final_result['Com_Type'].value_counts())

# 按Com_Type显示权益汇总
print(f"\n按合约类型的权益汇总（原始货币）:")
for com_type in final_result['Com_Type'].unique():
    type_data = final_result[final_result['Com_Type'] == com_type]
    total_equity = type_data['net_equity'].sum()
    print(f"{com_type} - 合约数: {len(type_data)}, 总权益: {total_equity:,.2f}")

print(f"\n按合约类型的权益汇总（转换为USD）:")
for com_type in final_result['Com_Type'].unique():
    type_data = final_result[final_result['Com_Type'] == com_type]
    total_equity_usd = type_data['net_equity_usd'].sum()
    print(f"{com_type} - 合约数: {len(type_data)}, 总权益USD: {total_equity_usd:,.2f}")

# 总体权益汇总
total_net_equity_usd = final_result['net_equity_usd'].sum()
print(f"\n所有合约总权益（USD）: {total_net_equity_usd:,.2f}")

# 保存到桌面
output_path = r"C:\Users\hongl\Desktop\PHILLIP_Open_Position_PHL9000_20260504_processed.csv"
final_result.to_csv(output_path, index=False)
print(f"\n文件已保存到: {output_path}")

# # 显示货币使用情况统计
# print(f"\n各货币使用情况统计:")
# currency_stats = final_result['Settle_Curr_Cd'].value_counts()
# print(currency_stats)
