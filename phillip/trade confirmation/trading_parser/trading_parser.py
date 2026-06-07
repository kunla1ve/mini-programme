import re
import pandas as pd
from pathlib import Path

def parse_trading_data(text):
    """解析交易记录文本"""
    
    # 清理文本：把断行的 POEMSHK/MCSGXPHL 等合并回上一行
    text = re.sub(r' -\s*\n\s*\n\s*(POEMSHK|MCSGXPHL\w*|PHLX\w*)', r' - \1', text)
    
    # 也处理没有 - 的情况（如 BUY 1 P.DAEU267100 @ 0.01370\n\nPOEMSHK...）
    text = re.sub(r'(@\s*[\d.]+\s*)\n\s*\n\s*(POEMSHK|MCSGXPHL\w*|PHLX\w*)', 
                  r'\1- \2', text)
    
    lines = text.split('\n')
    
    # 交易正则表达式：支持期权合约格式（含点号、数字、字母）
    detail_pattern = r'(买入|卖出|BUY|SELL)\s+(\d+)\s*(?:\[(\d+)\])?\s*([A-Za-z0-9.$]+?)\s*@\s*([\d.]+)\s*-'
    
    transactions = []
    current_symbol = None
    current_action = None
    current_details = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 跳过分隔符
        if line.startswith('––––––'):
            continue
        
        # 跳过产品描述行
        if re.search(r'^[A-Za-z]+:\s*(September|October|November|December|January|February|March|April|May|June|July|August|Call|Put|Option)', line):
            continue
        
        # 跳过交易所标识行
        if re.search(r'^(POEMSHK|MCSGXPHL|PHLX)\s*\(', line):
            continue
        
        # 跳过纯数字日期行
        if re.match(r'^\d{2}/\d{2}/\d{4}$', line):
            continue
        
        # 跳过产品总览行（如 "Nikkei 225 (Yen): June 2026"）
        if re.search(r'^[A-Za-z\s/()-]+:\s*(January|February|March|April|May|June|July|August|September|October|November|December|20\d{2})', line):
            continue
        
        # 匹配交易行
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
            
            symbol = match.group(4).strip()
            price = float(match.group(5))
            
            # 如果是新合约或方向改变，保存之前的交易
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
    
    # 处理最后一个交易
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

def create_excel(transactions, output_file):
    """创建Excel文件"""
    output_data = [['總成交確認'], []]
    
    for trans in transactions:
        output_data.extend([
            [],
            [trans['action']],
            ['', trans['product'], trans['quantity'], 
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
        try:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        except EOFError:
            break
    
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
            print(f"{trans['action']}: {trans['product']} "
                  f"{trans['quantity']}張 @ {trans['avg_price']:.4f}")
        
    except Exception as e:
        print(f"❌ 處理出錯: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
