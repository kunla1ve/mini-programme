# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 20:45:48 2026

@author: kunlave
"""

import numpy as np
import matplotlib.pyplot as plt

# 常量定义
c = 3.0e8  # 光速 (米/秒)，这里作为数值基准
m0 = 1     # 静止质量 (设为1，以便观察能量比例)

# 生成速度数组：从 0 到 0.99c
# 为了避免除零和无穷大，最大值设为略小于c
v = np.linspace(0, 0.99 * c, 1000)

# 计算洛伦兹因子 gamma
beta = v / c
gamma = 1 / np.sqrt(1 - beta**2)

# 计算相对论动能 K
K_rel = (gamma - 1) * m0 * c**2

# 计算牛顿力学动能作为对比 (用于低速区域)
K_newton = 0.5 * m0 * v**2

# 开始绘图
plt.figure(figsize=(10, 6))

# 绘制相对论动能曲线
plt.plot(v / c, K_rel, 'b-', linewidth=2, label='相对论动能 $K = (\gamma - 1) m_0 c^2$')

# 绘制牛顿力学动能曲线 (虚线，用于对比)
plt.plot(v / c, K_newton, 'r--', linewidth=1.5, label='牛顿力学动能 $K = \\frac{1}{2} m_0 v^2$')

# 标记光速位置 (垂直渐近线)
plt.axvline(x=1, color='k', linestyle=':', linewidth=1, label='光速 $c$ (渐近线)')

# 设置横轴范围，重点关注接近光速的区域
plt.xlim(0, 1)

# 为了显示曲线的急剧上扬，纵轴可以使用科学计数法或对数刻度
# 这里暂时使用普通坐标，但可能会看到在0.99c处y值很大
# 为了更好展示，可以设置纵轴上限，或者使用对数坐标
# plt.ylim(0, 50 * m0 * c**2) # 可以根据需要调整

plt.xlabel('速度 $v / c$', fontsize=12)
plt.ylabel('动能 $K$ (单位: $m_0 c^2$)', fontsize=12) # 纵轴以静止能量为单位
plt.title('相对论动能随速度的变化', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)

# 显示图像
plt.show()