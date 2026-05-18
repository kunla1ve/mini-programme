import re
import pandas as pd
from pathlib import Path

def parse_trading_data(text):
    """解析交易记录文本"""
    product_map = {
        'SIEN26': ('2026年 7月', 'CME白銀'),
        'GCEQ26': ('2026年 8月', 'CME黃金'),
        'EPM26': ('2026年 6月', 'CME標指'),
        'ENQM26': ('2026年 6月', 'CME納指'),
        'YMM26': ('2026年 6月', 'CBOT杜指'),
        'ZNAM26': ('2026年 6月', 'SIMEX日經'),
    }
    
    # 清理文本：把断行的 POEMSHK 合并回上一行
    text = re.sub(r' -\n\s*\n\s*POEMSHK', ' - POEMSHK', text)
    
    blocks = text.split('––––––––––––––––––––––––––––––––––')
    if len(blocks) == 1:
        blocks = split_by_product(text)
    
    transactions = []
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        lines = block.split('\n')
        
        # 兼容中英文：买入/卖出 或 BUY/SELL
        detail_pattern = r'(买入|卖出|BUY|SELL)\s+(\d+)\s*(?:\[(\d+)\])?\s*(\w+)\s*@\s*([\d.]+)\s*-\s*POEMSHK'
        details = []
        action = None
        symbol = None
        
        for line in lines:
            match = re.search(detail_pattern, line, re.IGNORECASE)
            if match:
                action_text = match.group(1).upper()
                if action_text in ['卖出', 'SELL']:
                    action = '沽出'
                else:
                    action = '買入'
                
                actual_qty = match.group(3)
                if actual_qty:
                    qty = int(actual_qty)
                else:
                    qty = int(match.group(2))
                
                symbol = match.group(4)
                price = float(match.group(5))
                details.append((qty, price))
        
        if symbol and symbol in product_map and details:
            total_qty = sum(q for q, _ in details)
            total_value = sum(q * p for q, p in details)
            avg_price = total_value / total_qty
            period, product_name = product_map[symbol]
            
            transactions.append({
                'action': action,
                'period': period,
                'product': product_name,
                'quantity': total_qty,
                'avg_price': avg_price
            })
    
    return transactions

def split_by_product(text):
    """按产品总览行分割文本"""
    lines = text.strip().split('\n')
    blocks = []
    current_block = []
    
    for line in lines:
        if re.search(r'(Silver|Gold|E-Mini|E-mini|Nikkei)', line):
            if current_block:
                blocks.append('\n'.join(current_block))
            current_block = []
        if line.strip():
            current_block.append(line)
    
    if current_block:
        blocks.append('\n'.join(current_block))
    
    return blocks

def create_excel(transactions, output_file):
    """创建Excel文件"""
    output_data = [['總成交確認'], []]
    
    for trans in transactions:
        output_data.extend([
            [],
            [trans['action']],
            [trans['period'], f"「{trans['product']}」", trans['quantity'], 
             f"{trans['avg_price']:.4f}", '平均價']
        ])
    
    df = pd.DataFrame(output_data)
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, header=False, sheet_name='交易記錄')
        worksheet = writer.sheets['交易記錄']
        for col, width in zip(['A', 'B', 'C', 'D', 'E'], [20, 20, 10, 15, 10]):
            worksheet.column_dimensions[col].width = width

def main():
    print("=" * 60)
    print("交易記錄轉換工具")
    print("=" * 60)
    print("\n請粘貼交易數據（輸入空行結束）：")
    
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    
    text = '\n'.join(lines)
    
    if not text.strip():
        print("❌ 未輸入任何數據")
        return
    
    desktop = Path.home() / "Desktop"
    output_file = desktop / "交易記錄_summary.xlsx"
    
    try:
        transactions = parse_trading_data(text)
        
        if not transactions:
            print("❌ 未找到有效的交易記錄")
            return
        
        create_excel(transactions, output_file)
        
        print(f"\n✅ Excel文件已生成: {output_file}")
        print("\n📊 交易摘要:")
        print("-" * 60)
        for trans in transactions:
            print(f"{trans['action']}: {trans['period']} {trans['product']} "
                  f"{trans['quantity']}張 @ {trans['avg_price']:.4f}")
        
    except Exception as e:
        print(f"❌ 處理出錯: {e}")

if __name__ == "__main__":
    main()
