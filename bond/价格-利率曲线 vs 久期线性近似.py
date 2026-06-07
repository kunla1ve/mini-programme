# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 16:25:04 2026

@author: hongl
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib


def bond_price(coupon_rate, ytm, years, face=100, freq=1):
    """计算债券价格"""
    periods = years * freq
    coupon_payment = face * coupon_rate / freq
    ytm_period = ytm / freq
    
    # 现值计算
    pv_coupons = coupon_payment * (1 - (1 + ytm_period) ** -periods) / ytm_period
    pv_face = face / (1 + ytm_period) ** periods
    
    return pv_coupons + pv_face

def modified_duration(coupon_rate, ytm, years, freq=1):
    """计算修正久期"""
    mac_dur, _, _ = macaulay_duration(coupon_rate, ytm, years, freq)
    return mac_dur / (1 + ytm / freq)

def convexity(coupon_rate, ytm, years, face=100, freq=1):
    """计算凸性"""
    periods = years * freq
    coupon_payment = face * coupon_rate / freq
    ytm_period = ytm / freq
    
    price = bond_price(coupon_rate, ytm, years, face, freq)
    
    convexity_sum = 0
    for t in range(1, periods + 1):
        cf = coupon_payment if t < periods else coupon_payment + face
        convexity_sum += cf * t * (t + 1) / ((1 + ytm_period) ** (t + 2))
    
    return convexity_sum / price / freq ** 2

# 参数设置
coupon = 5  # 票面利率5%
years = 10  # 10年期
current_ytm = 5  # 当前收益率5%

# 利率变动范围
ytm_range = np.linspace(1, 9, 100)
prices_real = [bond_price(coupon, ytm, years) for ytm in ytm_range]

# 计算当前价格、久期和凸性
current_price = bond_price(coupon, current_ytm, years)
mod_dur = modified_duration(coupon, current_ytm, years)
conv = convexity(coupon, current_ytm, years)

# 久期线性近似
price_duration_only = current_price * (1 - mod_dur * (ytm_range - current_ytm))

# 久期 + 凸性近似
price_duration_convexity = current_price * (1 - mod_dur * (ytm_range - current_ytm) 
                                              + 0.5 * conv * (ytm_range - current_ytm) ** 2)

# 绘图
fig, ax = plt.subplots(figsize=(12, 7))

ax.plot(ytm_range, prices_real, 'b-', linewidth=2.5, label='真实价格曲线 (凸性)')
ax.plot(ytm_range, price_duration_only, 'r--', linewidth=1.8, label='久期线性近似 (直线)')
ax.plot(ytm_range, price_duration_convexity, 'g:', linewidth=2, label='久期 + 凸性修正')

# 标记当前点
ax.plot(current_ytm, current_price, 'ko', markersize=8, label=f'当前点 (收益率={current_ytm}%)')

# 添加阴影区域说明误差
ax.fill_between(ytm_range, price_duration_only, prices_real, 
                where=(ytm_range > current_ytm), alpha=0.2, color='red', label='久期低估下跌幅度')
ax.fill_between(ytm_range, price_duration_only, prices_real, 
                where=(ytm_range < current_ytm), alpha=0.2, color='green', label='久期低估上涨幅度')

ax.set_xlabel('到期收益率 (%)', fontsize=12)
ax.set_ylabel('债券价格', fontsize=12)
ax.set_title(f'债券价格-收益率曲线：凸性修正效果\n(票面利率 {coupon}%, {years}年期)', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)

# 添加文本框解释
info_text = f'修正久期: {mod_dur:.2f}\n凸性: {conv:.2f}'
ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
        verticalalignment='top', fontsize=10,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.show()
