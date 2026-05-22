#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交易記錄處理工具 - 純文本替換版
直接修改ODS的XML文本，避免XML解析問題
"""

import re
import os
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


# ============================================================================
# 交易記錄文本解析
# ============================================================================

def parse_trading_data(text):
    """解析交易记录文本"""
    
    text = re.sub(r' -\s*\n\s*\n\s*(POEMSHK|MCSGXPHL\w*|PHLX\w*)', r' - \1', text)
    text = re.sub(r'(@\s*[\d.]+\s*)\n\s*\n\s*(POEMSHK|MCSGXPHL\w*|PHLX\w*)', 
                  r'\1- \2', text)
    
    lines = text.split('\n')
    detail_pattern = r'(买入|卖出|BUY|SELL)\s+(\d+)\s*(?:\[(\d+)\])?\s*([A-Za-z0-9.$]+?)\s*@\s*([\d.]+)\s*-'
    
    transactions = []
    current_symbol = None
    current_action = None
    current_details = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('––––––'):
            continue
        if re.search(r'^[A-Za-z]+:\s*(September|October|November|December|January|February|March|April|May|June|July|August|Call|Put|Option)', line):
            continue
        if re.search(r'^(POEMSHK|MCSGXPHL|PHLX)\s*\(', line):
            continue
        if re.match(r'^\d{2}/\d{2}/\d{4}$', line):
            continue
        if re.search(r'^[A-Za-z\s/()-]+:\s*(January|February|March|April|May|June|July|August|September|October|November|December|20\d{2})', line):
            continue
        
        match = re.search(detail_pattern, line, re.IGNORECASE)
        if match:
            action_text = match.group(1).upper()
            action = '沽出' if action_text in ['卖出', 'SELL'] else '買入'
            
            actual_qty = match.group(3)
            qty = int(actual_qty) if actual_qty else int(match.group(2))
            
            symbol = match.group(4).strip()
            price = float(match.group(5))
            
            if current_symbol and (symbol != current_symbol or action != current_action):
                if current_details:
                    total_qty = sum(q for q, _ in current_details)
                    total_value = sum(q * p for q, p in current_details)
                    avg_price = total_value / total_qty
                    transactions.append({
                        'action': current_action,
                        'product': current_symbol,
                        'quantity': total_qty,
                        'avg_price': avg_price
                    })
                current_details = []
            
            current_symbol = symbol
            current_action = action
            current_details.append((qty, price))
    
    if current_symbol and current_details:
        total_qty = sum(q for q, _ in current_details)
        total_value = sum(q * p for q, p in current_details)
        avg_price = total_value / total_qty
        transactions.append({
            'action': current_action,
            'product': current_symbol,
            'quantity': total_qty,
            'avg_price': avg_price
        })
    
    # 合并相同产品和方向的订单
    merged = {}
    for trans in transactions:
        key = (trans['action'], trans['product'])
        if key in merged:
            old_qty = merged[key]['quantity']
            old_value = merged[key]['avg_price'] * old_qty
            new_qty = old_qty + trans['quantity']
            new_value = old_value + (trans['avg_price'] * trans['quantity'])
            merged[key]['quantity'] = new_qty
            merged[key]['avg_price'] = new_value / new_qty
        else:
            merged[key] = trans.copy()
    
    return list(merged.values())


# ============================================================================
# ODS生成 - 純文本替換
# ============================================================================

def generate_ods(template_path, output_path, transaction_date, transactions):
    """使用純文本替換生成ODS文件"""
    
    # 分離沽出和買入
    sell_trans = [t for t in transactions if t['action'] == '沽出']
    buy_trans = [t for t in transactions if t['action'] == '買入']
    
    # 讀取模板
    with zipfile.ZipFile(template_path, 'r') as z:
        # 讀取content.xml
        content_xml = z.read('content.xml').decode('utf-8')
        
        # 讀取其他文件
        other_files = {}
        for name in z.namelist():
            if name != 'content.xml':
                other_files[name] = z.read(name)
    
    # 1. 更新交易日期
    content_xml = re.sub(
        r'(交易日期.*?)\d{4}-\d{1,2}-\d{1,2}\s+\d{2}:\d{2}',
        f'\\1{transaction_date}',
        content_xml
    )
    
    # 2. 生成新的數據行
    def create_row_xml(product, quantity, price):
        return f'''<table:table-row table:style-name="ro1">
             <table:table-cell office:value-type="string" table:style-name="ce7">
               <text:p>{product}</text:p>
             </table:table-cell>
             <table:table-cell office:value-type="float" office:value="{quantity}" table:style-name="ce8">
               <text:p>{quantity}</text:p>
             </table:table-cell>
             <table:table-cell office:value-type="float" office:value="{price:.4f}" table:style-name="ce9">
               <text:p>{price:.4f}</text:p>
             </table:table-cell>
             <table:table-cell office:value-type="string" table:style-name="ce7">
               <text:p><text:span text:style-name="T7">平均價</text:span></text:p>
             </table:table-cell>
             <table:table-cell table:style-name="ce3"/>
             <table:table-cell table:style-name="ce4"/>
             <table:table-cell table:number-columns-repeated="16378" table:style-name="ce5"/>
           </table:table-row>'''
    
    # 生成所有沽出行
    sell_rows = '\n'.join([create_row_xml(t['product'], t['quantity'], t['avg_price']) for t in sell_trans])
    
    # 生成所有買入行
    buy_rows = '\n'.join([create_row_xml(t['product'], t['quantity'], t['avg_price']) for t in buy_trans])
    
    # 3. 替換沽出數據行
    # 找到沽出標籤行和其後的數據行
    sell_pattern = r'(<text:span text:style-name="T5">沽出</text:span>.*?</table:table-row>)\s*<table:table-row.*?</table:table-row>(\s*<table:table-row table:style-name="ro1">\s*<table:table-cell table:style-name="ce10")'
    
    if sell_rows:
        content_xml = re.sub(sell_pattern, f'\\1\n{sell_rows}\\2', content_xml, flags=re.DOTALL)
    
    # 4. 替換買入數據行
    buy_pattern = r'(<text:span text:style-name="T5">買入</text:span>.*?</table:table-row>)\s*<table:table-row.*?</table:table-row>(\s*<table:table-row table:number-rows-repeated)'
    
    if buy_rows:
        content_xml = re.sub(buy_pattern, f'\\1\n{buy_rows}\\2', content_xml, flags=re.DOTALL)
    
    # 5. 寫入新的ODS文件
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        # 寫入content.xml
        zout.writestr('content.xml', content_xml)
        
        # 寫入其他文件
        for name, data in other_files.items():
            zout.writestr(name, data)


# ============================================================================
# 主程序
# ============================================================================

def main():
    """主函数"""
    print("=" * 60)
    print("📈 交易記錄處理工具")
    print("=" * 60)
    print("\n請粘貼交易數據（連續按兩次回車結束輸入）：")
    
    lines = []
    blank_count = 0
    while True:
        try:
            line = input()
            if line == "":
                blank_count += 1
                if blank_count >= 2:
                    break
            else:
                blank_count = 0
            lines.append(line)
        except EOFError:
            break
    
    text = '\n'.join(lines)
    
    if not text.strip():
        print("❌ 未輸入任何數據")
        input("\n按回車鍵退出...")
        return
    
    try:
        transactions = parse_trading_data(text)
        
        if not transactions:
            print("❌ 未找到有效的交易記錄")
            input("\n按回車鍵退出...")
            return
        
        print("\n📊 解析到的交易:")
        print("-" * 60)
        for trans in transactions:
            print(f"{trans['action']}: {trans['product']} "
                  f"{trans['quantity']}張 @ {trans['avg_price']:.4f}")
        
    except Exception as e:
        print(f"❌ 解析出錯: {e}")
        input("\n按回車鍵退出...")
        return
    
    transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    template_path = r"C:\Users\hongl\Desktop\format.ods"
    
    if not os.path.exists(template_path):
        print(f"❌ 模板文件不存在: {template_path}")
        input("\n按回車鍵退出...")
        return
    
    try:
        desktop = Path.home() / "Desktop"
        output_filename = f"交易单_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ods"
        output_path = os.path.join(str(desktop), output_filename)
        
        generate_ods(template_path, output_path, transaction_date, transactions)
        
        print(f"\n✨ 完成！交易單已保存到桌面: {output_filename}")
        
    except Exception as e:
        print(f"❌ 生成ODS文件時出錯: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回車鍵退出...")


if __name__ == "__main__":
    main()