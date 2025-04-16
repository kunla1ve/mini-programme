# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 21:10:08 2025

@author: kunla1ve
"""

import numpy as np
import matplotlib.pyplot as plt
from mpmath import zeta
from matplotlib.colors import hsv_to_rgb

def compute_zeta_values(xmin, xmax, ymin, ymax, width=800, height=800):
    """计算矩形区域内的ζ函数值"""
    x = np.linspace(xmin, xmax, width)
    y = np.linspace(ymin, ymax, height)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j*Y
    
    # 计算ζ函数值 (使用mpmath库的zeta函数)
    zeta_values = np.zeros(Z.shape, dtype=np.complex128)
    for i in range(Z.shape[0]):
        for j in range(Z.shape[1]):
            try:
                zeta_values[i, j] = complex(zeta(Z[i, j]))
            except ValueError:  # 处理极点
                zeta_values[i, j] = np.nan + np.nan*1j
    return zeta_values

def domain_coloring(z):
    """定义域着色方法"""
    # 创建掩码识别NaN值
    mask = np.isnan(z)
    z = np.nan_to_num(z, nan=0)  # 临时替换NaN
    
    # 相位角 (色调)
    H = np.angle(z) / (2 * np.pi) + 0.5
    # 模的对数 (饱和度)
    S = np.ones_like(H)
    # 亮度 (基于模)
    V = np.log(1 + np.abs(z)) / (1 + np.abs(z))
    V = np.clip(V, 0, 1)
    
    # 将HSV转换为RGB
    HSV = np.dstack((H, S, V))
    RGB = hsv_to_rgb(HSV)
    
    # 将极点位置设为白色
    RGB[mask] = [1, 1, 1]
    return RGB

def plot_zeta_function(xmin, xmax, ymin, ymax, width=800, height=800):
    """绘制ζ函数图像"""
    # 计算ζ函数值
    zeta_values = compute_zeta_values(xmin, xmax, ymin, ymax, width, height)
    
    # 应用定义域着色
    image = domain_coloring(zeta_values)
    
    # 创建图形
    plt.figure(figsize=(10, 8))
    plt.imshow(image, extent=[xmin, xmax, ymin, ymax], origin='lower')
    
    # 添加标签和标题
    plt.title(r"Domain Coloring of Riemann $\zeta$ function", fontsize=14)
    plt.xlabel("Re(z)", fontsize=12)
    plt.ylabel("Im(z)", fontsize=12)
    
    # 添加网格
    plt.grid(alpha=0.3)
    
    # 显示临界线 (Re(z)=0.5)
    plt.axvline(x=0.5, color='white', linestyle='--', alpha=0.7)
    
    plt.colorbar(label="Magnitude (log scale)")
    plt.show()

# 定义要绘制的矩形区域
xmin, xmax = -20, 20
ymin, ymax = -30, 30

# 绘制ζ函数图像
plot_zeta_function(xmin, xmax, ymin, ymax)