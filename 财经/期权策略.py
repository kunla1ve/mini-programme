# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 22:30:26 2026

@author: kunlave
"""
# -*- coding: utf-8 -*-
"""
期权策略盈亏分析（卖Put + 卖Call）
- 计算盈亏平衡点
- 计算当前点位（62833）的盈亏
- 计算上涨100、200、1000点后的亏损
- 绘制PnL曲线并标注零线交点
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 数据（依据您提供的表格）
data = [
    ("Put", 45000, -2, 5),
    ("Put", 53000, -4, 3),
    ("Put", 53125, -5, 3),
    ("Put", 53250, -4, 3),
    ("Put", 53375, -1, 3),
    ("Put", 53500, -3, 3),
    ("Put", 53625, -4, 3),
    ("Put", 53750, -3, 3),
    ("Put", 53875, -1, 3),
    ("Put", 54000, -3, 2.66666),
    ("Put", 55375, -1, 3),
    ("Put", 55500, -2, 3),
    ("Put", 55625, -1, 3),
    ("Put", 55750, -2, 3),
    ("Put", 55875, -6, 3),
    ("Put", 56000, -6, 3.5),
    ("Put", 56125, -8, 3),
    ("Put", 56250, -7, 3.28571),
    ("Put", 56375, -3, 3.33333),
    ("Put", 56750, -3, 4),
    ("Put", 56875, -2, 5),
    ("Put", 57250, -2, 3),
    ("Put", 57500, -5, 3),
    ("Put", 58000, -6, 5),
    ("Put", 60000, -1, 33),
    ("Call", 63375, -1, 4),
    ("Call", 63500, -3, 3),
    ("Call", 63750, -5, 22.8),
    ("Call", 64000, -3, 13),
    ("Call", 64250, -2, 7),
    ("Call", 64500, -3, 6),
    ("Call", 64750, -9, 6.33333),
    ("Call", 65000, -8, 4.5),
    ("Call", 65500, -1, 4),
    ("Call", 68000, -1, 3),
]

df = pd.DataFrame(data, columns=["Type", "Strike", "Net", "Price"])

# 期权盈亏函数
def option_pnl(S, type_, K, net, prem):
    if type_ == "Call":
        return net * (np.maximum(S - K, 0) - prem)
    else:  # Put
        return net * (np.maximum(K - S, 0) - prem)

# 价格范围
S_range = np.linspace(55000, 66000, 10)  # 扩宽范围以捕捉所有拐点
total_pnl = np.zeros_like(S_range)

for _, row in df.iterrows():
    total_pnl += option_pnl(S_range, row["Type"], row["Strike"], row["Net"], row["Price"])

# 寻找盈亏平衡点（与零线交点）
# 方法：找符号变化的位置，然后线性插值精确交点
zero_crossings = []
for i in range(len(S_range) - 1):
    if total_pnl[i] * total_pnl[i+1] < 0:
        # 线性插值
        x1, y1 = S_range[i], total_pnl[i]
        x2, y2 = S_range[i+1], total_pnl[i+1]
        x_zero = x1 - y1 * (x2 - x1) / (y2 - y1)
        zero_crossings.append(x_zero)

# 当前日经指数点位
current_nk = 62654.01

# 计算当前盈亏
def get_pnl_at(point):
    return option_pnl(point, "Call", 0, 1, 0)  # 占位，实际需要重构
# 直接用公式计算当前点位的总盈亏
current_pnl = 0.0
for _, row in df.iterrows():
    if row["Type"] == "Call":
        current_pnl += row["Net"] * (max(current_nk - row["Strike"], 0) - row["Price"])
    else:
        current_pnl += row["Net"] * (max(row["Strike"] - current_nk, 0) - row["Price"])

# 上涨100, 200, 1000点的盈亏
up_points = [1000, 2000, 3000]
pnl_changes = {}
for up in up_points:
    new_price = current_nk + up
    new_pnl = 0.0
    for _, row in df.iterrows():
        if row["Type"] == "Call":
            new_pnl += row["Net"] * (max(new_price - row["Strike"], 0) - row["Price"])
        else:
            new_pnl += row["Net"] * (max(row["Strike"] - new_price, 0) - row["Price"])
    pnl_changes[up] = new_pnl - current_pnl   #计不计算prem！！！！
# 输出结果
print("=" * 60)
print("期权策略盈亏分析")
print("=" * 60)
print(f"当前日经指数: {current_nk} 点")
print(f"当前策略总盈亏: {current_pnl:.2f} 点（每个期权单位对应1点指数变动）")
print("\n盈亏平衡区间（PnL > 0 的区间）:")
if len(zero_crossings) >= 2:
    # 通常这类空宽跨式有两个平衡点
    lower = min(zero_crossings)
    upper = max(zero_crossings)
    print(f"  盈利区间: {lower:.2f} ~ {upper:.2f}")
    print(f"  当前指数{'在' if lower <= current_nk <= upper else '不在'}盈利区间内")
else:
    print(f"  盈利区间边界: {zero_crossings}")

print("\n从当前点上涨后的盈亏变化:")
for up, loss in pnl_changes.items():
    # loss为亏损
    if loss < 0:
        print(f"  上涨 {up:4d} 点 → 亏损 {-loss:.2f} 点")
    else:
        print(f"  上涨 {up:4d} 点 → 盈利 {loss:.2f} 点")

# 绘制图表
plt.figure(figsize=(14, 7))
plt.plot(S_range, total_pnl, label="Total PnL", color="blue", linewidth=2)
plt.axhline(0, color="black", linestyle="--", linewidth=1)
plt.axvline(x=current_nk, color="red", linestyle="-.", alpha=0.7, label=f"Current NK={current_nk}")
# 标注平衡点
for i, zc in enumerate(zero_crossings):
    plt.plot(zc, 0, 'ro', markersize=6)
    plt.text(zc, -50, f"{zc:.0f}", ha='center', fontsize=9)

# 填充盈利区域
if len(zero_crossings) >= 2:
    mask = (S_range >= zero_crossings[0]) & (S_range <= zero_crossings[-1])
    plt.fill_between(S_range, 0, total_pnl, where=mask, color='green', alpha=0.2, label="Profit zone")
else:
    plt.fill_between(S_range, 0, total_pnl, where=(total_pnl>0), color='green', alpha=0.2, label="Profit zone")

plt.title("Option Strategy PnL (Short Put + Short Call / Short Strangle)")
plt.xlabel("Nikkei Index at Expiration")
plt.ylabel("Profit / Loss (points per unit)")
plt.grid(True, alpha=0.3)
plt.legend(loc="best")
plt.tight_layout()
plt.show()
