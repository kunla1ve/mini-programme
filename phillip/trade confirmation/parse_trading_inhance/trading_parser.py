#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交易記錄處理工具 - 最終版
從第9行開始寫入數據，保留圖片，日期粗體
"""

import re
import os
from datetime import datetime
from pathlib import Path
import xlwings as xw
import copy


# ============================================================================
# 交易記錄文本解析
# ============================================================================

def parse_trading_data(text):
    """解析交易记录文本"""
    
    # 清理文本
    text = re.sub(r' -\s*\n\s*\n\s*(POEMSHK|MCSGXPHL\w*|PHLX\w*)', r' - \1', text)
    text = re.sub(r'(@\s*[\d.]+\s*)\n\s*\n\s*(POEMSHK|MCSGXPHL\w*|PHLX\w*)', 
                  r'\1- \1', text)
    
    lines = text.split('\n')
    
    patterns = [
        r'(買入|賣出|BUY|SELL)\s+(\d+)\s*(?:\[(\d+)\])?\s*([A-Za-z0-9.$]+?)\s*@\s*([\d.]+)\s*-',
        r'(買入|賣出|BUY|SELL)\s+(\d+)\s+([A-Za-z0-9.$]+?)\s*@\s*([\d.]+)',
    ]
    
    transactions = []
    current_symbol = None
    current_action = None
    current_details = []  # 只存放實際成交明細（帶 " -" 的行）
    
    def flush_group():
        """將當前累積的成交明細輸出為一筆交易"""
        nonlocal current_symbol, current_action, current_details
        if current_details:
            total_qty = sum(q for q, _ in current_details)
            total_value = sum(q * p for q, p in current_details)
            avg_price = total_value / total_qty if total_qty > 0 else 0
            transactions.append({
                'action': current_action,
                'product': current_symbol,
                'quantity': total_qty,
                'avg_price': avg_price
            })
        current_symbol = None
        current_action = None
        current_details = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if (line.startswith('––––––') or line.startswith('---') or
            re.search(r'^[A-Za-z]+:\s*(January|February|March|April|May|June|July|August|September|October|November|December|Call|Put|Option)', line) or
            re.search(r'^(POEMSHK|MCSGXPHL|PHLX)\s*\(', line) or
            re.match(r'^\d{2}/\d{2}/\d{4}$', line) or
            re.search(r'^[A-Za-z\s/()-]+:\s*(January|February|March|April|May|June|July|August|September|October|November|December|20\d{2})', line)):
            continue
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                is_dash = (pattern == patterns[0])  # pattern[0] 匹配帶 " -" 的行
                
                action_text = match.group(1).upper()
                qty = int(match.group(3)) if match.group(3) and pattern == patterns[0] else int(match.group(2))
                symbol = match.group(4).strip() if pattern == patterns[0] else match.group(3).strip()
                price = float(match.group(5)) if pattern == patterns[0] else float(match.group(4))
                
                action = '沽出' if action_text in ['賣出', 'SELL'] else '買入'
                
                if is_dash:
                    # 部分成交明細：累積到當前組
                    if current_symbol and (symbol != current_symbol or action != current_action):
                        flush_group()
                    current_symbol = symbol
                    current_action = action
                    current_details.append((qty, price))
                else:
                    # 總訂單摘要：先輸出上一組，然後開始新的一組（只記錄產品/方向，不加入明細）
                    flush_group()
                    current_symbol = symbol
                    current_action = action
                    # 不將總訂單的 qty/price 加入 details，等後續的 dash 行來填充
                break
    
    flush_group()
    
    # 合併相同產品和方向的交易
    merged = {}
    for trans in transactions:
        key = (trans['action'], trans['product'])
        if key in merged:
            old_qty = merged[key]['quantity']
            old_value = merged[key]['avg_price'] * old_qty
            new_qty = old_qty + trans['quantity']
            new_value = old_value + (trans['avg_price'] * trans['quantity'])
            merged[key]['quantity'] = new_qty
            merged[key]['avg_price'] = new_value / new_qty if new_qty > 0 else 0
        else:
            merged[key] = trans.copy()
    
    return list(merged.values())


# ============================================================================
# XLSX模板填充
# ============================================================================

def fill_xlsx_template(template_path, output_path, transaction_date, transactions):
    """填充數據，保留圖片，日期粗體 (使用 xlwings)"""
    
    sell_trans = [t for t in transactions if t['action'] == '沽出']
    buy_trans = [t for t in transactions if t['action'] == '買入']
    
    print(f"\n📊 交易統計:")
    print(f"  沽出: {len(sell_trans)} 筆")
    for t in sell_trans:
        print(f"    - {t['product']}: {t['quantity']}張 @ {t['avg_price']:.4f}")
    print(f"  買入: {len(buy_trans)} 筆")
    for t in buy_trans:
        print(f"    - {t['product']}: {t['quantity']}張 @ {t['avg_price']:.4f}")
    
    # 啟動不可見的 Excel 進程
    app = xw.App(visible=False)
    
    try:
        # 打開模板 (100% 保留圖片、圖表和宏)
        wb = app.books.open(template_path)
        ws = wb.sheets[0]
        
        print(f"\n📋 模板加載完成")
        
        # 1. 更新交易日期 - 在模板前8行中搜索並更新
        date_updated = False
        for i in range(1, 9):
            for j in range(1, 5):
                cell = ws.range((i, j))
                if cell.value is not None:
                    cell_str = str(cell.value)
                    # 查找包含日期格式的內容
                    if re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', cell_str):
                        # 替換日期時間
                        new_value = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s+\d{2}:\d{2})?', 
                                          transaction_date, cell_str)
                        cell.value = new_value
                        cell.api.Font.Name = 'Times New Roman'
                        cell.api.Font.Size = 11
                        cell.api.Font.Bold = True
                        date_updated = True
                        print(f"✅ 日期已更新: {transaction_date} (行{i}, 列{j})")
                        break
            if date_updated:
                break
        
        if not date_updated:
            print("⚠️ 未找到日期單元格，請檢查模板格式")
        
        # 2. 清除第9行及以後的內容
        try:
            # 獲取最後一行
            last_row = ws.api.Cells.SpecialCells(11).Row  # 11 = xlCellTypeLastCell
            max_row_to_clear = max(last_row, 50)
            if max_row_to_clear >= 9:
                clear_range = ws.range(f'A9:D{max_row_to_clear}')
                clear_range.api.UnMerge()
                clear_range.clear() # 清除內容和格式，但不影響圖片
        except:
            pass
        
        # 定義輔助函數：設置邊框
        def set_border(rng):
            for border_id in [7, 8, 9, 10]: # xlEdgeLeft, xlTop, xlBottom, xlRight
                rng.api.Borders(border_id).Weight = 2 # xlThin
                
        # 3. 從第9行開始寫入數據
        current_row = 9
        headers = ['產品', '數量', '價格', '類型']
        
        def write_section(ws, start_row, title_text, title_color, transactions):
            """寫入一個交易區塊（標題 + 表頭 + 數據），返回下一行行號"""
            row = start_row
            # 標題行
            rng = ws.range(f'A{row}:D{row}')
            rng.api.Merge()
            rng.value = title_text
            rng.api.Font.Name = 'Times New Roman'
            rng.api.Font.Size = 12
            rng.api.Font.Bold = True
            rng.api.HorizontalAlignment = -4108
            rng.api.VerticalAlignment = -4108
            rng.color = title_color
            set_border(rng)
            row += 1
            
            # 表頭行
            rng = ws.range(f'A{row}:D{row}')
            rng.value = headers
            rng.api.Font.Name = 'Times New Roman'
            rng.api.Font.Size = 11
            rng.api.Font.Bold = True
            rng.color = (217, 225, 242)
            rng.api.HorizontalAlignment = -4108
            rng.api.VerticalAlignment = -4108
            set_border(rng)
            row += 1
            
            # 數據行
            for trans in transactions:
                rng = ws.range(f'A{row}:D{row}')
                rng.value = [
                    trans['product'],
                    trans['quantity'],
                    round(trans['avg_price'], 4),
                    '平均價'
                ]
                rng.api.Font.Name = 'Times New Roman'
                rng.api.Font.Size = 11
                rng.api.HorizontalAlignment = -4108
                rng.api.VerticalAlignment = -4108
                set_border(rng)
                row += 1
            
            return row
        
        # 沽出區塊
        if sell_trans:
            current_row = write_section(ws, current_row, '沽出', (255, 192, 0), sell_trans)
            current_row += 1  # 空一行
        
        # 買入區塊
        if buy_trans:
            current_row = write_section(ws, current_row, '買入', (146, 208, 80), buy_trans)
        
        # 調整列寬
        ws.range('A:A').column_width = 25
        ws.range('B:B').column_width = 10
        ws.range('C:C').column_width = 15
        ws.range('D:D').column_width = 10
        
        # 保存文件
        wb.save(output_path)
        
    finally:
        # 無論發生甚麼，確保關閉工作簿和 Excel 進程
        try:
            wb.close()
        except:
            pass
        app.quit()
    
    print(f"\n✅ 文件已保存: {output_path}")
    
    return True


# ============================================================================
# 主程序
# ============================================================================

def get_resource_path(relative_path):
    """獲取資源的絕對路徑，適配 PyInstaller 打包環境"""
    import sys
    try:
        # PyInstaller 創建的臨時文件夾
        base_path = sys._MEIPASS
    except Exception:
        # 否則使用當前腳本目錄
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def main():
    """主程序"""
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
    
    transactions = parse_trading_data(text)
    
    if not transactions:
        print("❌ 未找到有效的交易記錄")
        input("\n按回車鍵退出...")
        return
    
    print(f"\n✅ 解析到 {len(transactions)} 筆交易:")
    for i, trans in enumerate(transactions, 1):
        print(f"  {i:2d}. {trans['action']}: {trans['product']:25s} "
              f"{trans['quantity']:4d}張 @ {trans['avg_price']:12.4f}")
    
    transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    template_path = get_resource_path("format.xlsx")
    
    if not os.path.exists(template_path):
        print(f"\n❌ 模板文件不存在: {template_path}")
        input("\n按回車鍵退出...")
        return
    
    try:
        desktop = Path.home() / "Desktop"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        xlsx_filename = f"交易单_{timestamp}.xlsx"
        xlsx_path = os.path.join(str(desktop), xlsx_filename)
        
        fill_xlsx_template(template_path, xlsx_path, transaction_date, transactions)
        
        print(f"\n✨ 完成！")
        print(f"📁 {xlsx_filename}")
        
        open_file = input("\n是否打開文件？(y/n): ").strip().lower()
        if open_file == 'y':
            os.startfile(xlsx_path)
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回車鍵退出...")


if __name__ == "__main__":
    main()