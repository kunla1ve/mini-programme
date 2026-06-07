import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re

# 设置中文字体（Windows用SimHei，Mac用PingFang SC，Linux用WenQuanYi）
plt.rcParams['font.sans-serif'] = ['SimHei', 'PingFang SC', 'WenQuanYi Micro Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 甲组数据
data_a = {
    '申请股份数目': [100,200,300,400,500,600,700,800,900,1000,1500,2000,2500,3000,3500,4000,4500,5000,
                   6000,7000,8000,9000,10000,20000,30000,40000,50000,100000,150000,200000],
    '有效申请人数': [51358,9702,24962,5399,5126,3367,2582,2874,1879,10233,13957,3817,1722,2186,3457,2363,1421,2970,
                   2300,2119,2222,1804,7625,4790,3578,2798,8523,4322,1922,2212],
    '配发基准': [
        '2568名中获100股','494名中获100股','1285名中获100股','281名中获100股','268名中获100股',
        '177名中获100股','136名中获100股','152名中获100股','100名中获100股','550名中获100股',
        '755名中获100股','207名中获100股','94名中获100股','130名中获100股','220名中获100股',
        '155名中获100股','95名中获100股','205名中获100股','180名中获100股','175名中获100股',
        '189名中获100股','160名中获100股','708名中获100股','735名中获100股','720名中获100股',
        '728名中获100股','2772名中获100股','2820名中获100股','全部100股','100股+121名额外100股'
    ]
}

# 乙组数据
data_b = {
    '申请股份数目': [250000,300000,350000,400000,450000,500000,600000,700000,800000,900000,1000000,1500000,2131300],
    '有效申请人数': [3990,1236,860,787,545,777,560,370,355,218,565,311,775],
    '配发基准': [
        '100股+1391名额外100股','100股+532名额外100股','100股+441名额外100股','100股+470名额外100股',
        '100股+377名额外100股','200股','200股+10名额外100股','200股+42名额外100股','200股+100名额外100股',
        '200股+99名额外100股','300股','300股+145名额外100股','400股'
    ]
}

df_a = pd.DataFrame(data_a)
df_b = pd.DataFrame(data_b)

# 计算甲组期望获得股数
def expected_shares_a(row):
    if '全部100股' in row['配发基准']:
        return 100
    elif '名中获' in row['配发基准']:
        nums = re.findall(r'\d+', row['配发基准'])
        if len(nums) >= 2:
            winners = int(nums[0])
            shares = int(nums[1])
            return winners / row['有效申请人数'] * shares
    elif '额外' in row['配发基准']:
        nums = re.findall(r'\d+', row['配发基准'])
        if len(nums) >= 2:
            base = int(nums[0])
            extra_winners = int(nums[1])
            return base + (extra_winners / row['有效申请人数']) * 100
    return np.nan

df_a['期望获配股数'] = df_a.apply(expected_shares_a, axis=1)
df_a['每股中签率'] = df_a['期望获配股数'] / df_a['申请股份数目']

# 计算乙组期望获得股数
def expected_shares_b(row):
    if '股' in row['配发基准'] and '+' not in row['配发基准']:
        nums = re.findall(r'\d+', row['配发基准'])
        return int(nums[0])
    elif '+' in row['配发基准']:
        nums = re.findall(r'\d+', row['配发基准'])
        if len(nums) >= 2:
            base = int(nums[0])
            extra_winners = int(nums[1])
            return base + (extra_winners / row['有效申请人数']) * 100
    return np.nan

df_b['期望获配股数'] = df_b.apply(expected_shares_b, axis=1)
df_b['每股中签率'] = df_b['期望获配股数'] / df_b['申请股份数目']

# 合并两组用于整体分布图
df_all = pd.concat([df_a, df_b], ignore_index=True)

# 创建三个子图
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 图1：申请股份数目和有效申请人数的分布
axes[0].bar(df_all['申请股份数目'].astype(str), df_all['有效申请人数'], color='skyblue', alpha=0.7)
axes[0].set_xlabel('申请股份数目')
axes[0].set_ylabel('有效申请人数')
axes[0].set_title('申请股份数目 vs 有效申请人数')
axes[0].tick_params(axis='x', rotation=90, labelsize=7)

# 图2：申请股份数目和期望获得股数的关系
axes[1].plot(df_a['申请股份数目'], df_a['期望获配股数'], 'o-', label='甲组', markersize=4, linewidth=1)
axes[1].plot(df_b['申请股份数目'], df_b['期望获配股数'], 's-', label='乙组', markersize=4, linewidth=1)
axes[1].set_xscale('log')      #对数坐标
axes[1].set_xlabel('申请股份数目 (对数坐标)')
axes[1].set_ylabel('期望获配股数')
axes[1].set_title('申请股份数目 vs 期望获配股数')
axes[1].legend()
axes[1].grid(True, linestyle='--', alpha=0.6)

# 图3：申请股份数目和每股中签率的关系
axes[2].plot(df_a['申请股份数目'], df_a['每股中签率'] * 100, 'o-', label='甲组', markersize=4, linewidth=1, color='green')
axes[2].plot(df_b['申请股份数目'], df_b['每股中签率'] * 100, 's-', label='乙组', markersize=4, linewidth=1, color='red')
axes[2].set_xscale('log')           #对数坐标
axes[2].set_xlabel('申请股份数目 (对数坐标)')
axes[2].set_ylabel('每股中签率 (%)')
axes[2].set_title('申请股份数目 vs 每股中签率')
axes[2].legend()
axes[2].grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.show()
