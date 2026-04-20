# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 16:18:43 2026

@author: hongl
"""

import numpy as np
import matplotlib.pyplot as plt

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def bond_cashflow_analysis(coupon_rate, ytm, years, face=100, freq=1):
    """
    计算债券的现金流现值分布和麦考利久期
    """
    periods = years * freq
    coupon_payment = face * coupon_rate / 100 / freq  # 每期票息
    ytm_period = ytm / 100 / freq  # 每期收益率
    
    cashflows = []  # 每期现金流金额
    times = []      # 每期对应的时间（年）
    pv_cashflows = []  # 每期现金流的现值
    
    for t in range(1, periods + 1):
        if t < periods:
            cf = coupon_payment
        else:
            cf = coupon_payment + face  # 最后一期加本金
        
        pv = cf / (1 + ytm_period) ** t
        cashflows.append(cf)
        times.append(t / freq)
        pv_cashflows.append(pv)
    
    bond_price = sum(pv_cashflows)
    weights = [pv / bond_price for pv in pv_cashflows]  # 现值权重
    
    # 麦考利久期 = 加权平均时间
    mac_duration = sum(weights[t] * times[t] for t in range(len(times)))
    
    return times, cashflows, pv_cashflows, weights, mac_duration, bond_price


# 参数设置
ytm = 5  # 到期收益率 5%
years = 10  # 期限 10年
coupon_rates = [2, 5, 8]  # 票面利率: 2%, 5%, 8%

# 创建图表
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for idx, coupon in enumerate(coupon_rates):
    times, cashflows, pv_cashflows, weights, mac_dur, price = bond_cashflow_analysis(coupon, ytm, years)
    
    ax = axes[idx]
    
    # 绘制双柱图：左轴为现金流现值，右轴为累计权重
    x_pos = np.arange(len(times))
    width = 0.6
    
    # 主柱状图：现金流现值
    bars = ax.bar(x_pos, pv_cashflows, width, color='steelblue', alpha=0.7, label='现金流现值')
    
    ax.set_xlabel('期数 (年)', fontsize=11)
    ax.set_ylabel('现金流现值', fontsize=11, color='steelblue')
    ax.tick_params(axis='y', labelcolor='steelblue')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f'{t:.0f}' for t in times])
    
    # 添加累计权重曲线（右轴）
    ax2 = ax.twinx()
    cumulative_weights = np.cumsum(weights)
    ax2.plot(x_pos, cumulative_weights, 'r-o', linewidth=2, markersize=6, label='累计权重')
    ax2.set_ylabel('累计现值权重', fontsize=11, color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.axhline(y=0.5, color='gray', linestyle=':', alpha=0.7, label='50% 权重线')
    
    # 标记久期位置（累计权重达到50%的点）
    # 找到累计权重刚超过50%的位置
    for i, cum_w in enumerate(cumulative_weights):
        if cum_w >= 0.5:
            # 线性插值更精确的久期位置
            if i > 0:
                prev_cum = cumulative_weights[i-1]
                exact_idx = (i-1) + (0.5 - prev_cum) / (cum_w - prev_cum)
                exact_time = times[int(exact_idx)] + (times[i] - times[int(exact_idx)]) * (exact_idx - int(exact_idx))
            else:
                exact_time = times[i]
            break
    
    # 在累计权重曲线上标记久期点
    ax2.scatter([exact_time], [0.5], color='green', s=100, zorder=5, 
                edgecolors='black', linewidths=1.5, label=f'久期 = {mac_dur:.2f}年')
    
    # 从久期点画垂直线
    ax.axvline(x=exact_time, color='green', linestyle='--', linewidth=2, alpha=0.7)
    
    # 添加标题和说明
    ax.set_title(f'票面利率 {coupon}% | 久期 = {mac_dur:.2f}年', fontsize=12, fontweight='bold')
    
    # 图例合并
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)

plt.suptitle('麦考利久期图解：现金流现值权重累计到50%的时间点', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()


# 额外补充一张图：展示不同票面利率下现金流权重分布的对比
fig2, ax = plt.subplots(figsize=(12, 6))

colors = ['blue', 'green', 'red']
for idx, coupon in enumerate(coupon_rates):
    times, cashflows, pv_cashflows, weights, mac_dur, price = bond_cashflow_analysis(coupon, ytm, years)
    
    # 绘制权重分布（面积图或折线）
    ax.plot(times, weights, 'o-', color=colors[idx], linewidth=2, markersize=6, 
            label=f'票面利率 {coupon}% (久期={mac_dur:.2f}年)')
    
    # 标记久期位置
    ax.axvline(x=mac_dur, color=colors[idx], linestyle='--', alpha=0.5)

ax.set_xlabel('时间 (年)', fontsize=12)
ax.set_ylabel('现金流现值权重', fontsize=12)
ax.set_title('不同票面利率债券的现金流权重分布对比\n(权重越高代表该时点收回的资金占比越大)', fontsize=13, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)

# 添加说明文字
ax.text(0.98, 0.98, 
        '注：久期是现金流回笼的加权平均时间\n票面利率越低 → 前期利息少 → 久期越长', 
        transform=ax.transAxes, ha='right', va='top', fontsize=10,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.show()


# 打印详细的数值对比
print("=" * 70)
print("麦考利久期详细计算结果")
print("=" * 70)
print(f"{'票面利率':<8} {'久期(年)':<10} {'债券价格':<10} {'说明'}")
print("-" * 70)

for coupon in coupon_rates:
    times, cashflows, pv_cashflows, weights, mac_dur, price = bond_cashflow_analysis(coupon, ytm, years)
    
    # 计算各期权重的描述
    weight_dist = "前期权重" + ("小" if coupon <= 5 else "大")
    note = f"票息{coupon}%: {weight_dist}"
    
    print(f"{coupon}%{'':<5} {mac_dur:<10.2f} {price:<10.2f} {note}")

print("-" * 70)
print("关键结论：")
print("1. 票面利率越低 → 前期现金流现值越小 → 加权平均时间越长 → 久期越大")
print("2. 久期本质是'现金流回笼的平均时间'，累计权重达到50%的点就是久期位置")
