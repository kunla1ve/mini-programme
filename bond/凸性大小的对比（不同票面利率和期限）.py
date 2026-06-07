import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def convexity(coupon_rate, ytm, years, face=100, freq=1):
    """计算凸性"""
    # 确保所有数值都是整数或浮点数，但periods必须是整数
    periods = int(years * freq)  # 关键：强制转换为整数
    coupon_payment = face * coupon_rate / 100 / freq
    ytm_period = ytm / 100 / freq
    
    # 计算债券价格
    price = 0
    for t in range(1, periods + 1):
        cf = coupon_payment if t < periods else coupon_payment + face
        price += cf / (1 + ytm_period) ** t
    
    # 计算凸性
    convexity_sum = 0
    for t in range(1, periods + 1):
        cf = coupon_payment if t < periods else coupon_payment + face
        convexity_sum += cf * t * (t + 1) / ((1 + ytm_period) ** (t + 2))
    
    return convexity_sum / price / freq ** 2


# 参数设置
coupons = np.arange(1, 11, 1)  # 票面利率 1% 到 10%
maturities = np.arange(1, 31, 1)  # 期限 1 到 30 年
ytm_fixed = 5  # 到期收益率 5%

print("正在计算凸性网格...")
# 创建凸性网格
X, Y = np.meshgrid(maturities, coupons)
convexity_grid = np.zeros((len(coupons), len(maturities)))

for i, coup in enumerate(coupons):
    for j, mat in enumerate(maturities):
        convexity_grid[i, j] = convexity(coup, ytm_fixed, mat)
        if (i * len(maturities) + j) % 50 == 0:  # 显示进度
            print(f"进度: {((i * len(maturities) + j) / (len(coupons) * len(maturities)) * 100):.1f}%")

print("计算完成！开始绘图...")

# 创建自定义渐变色映射（从浅黄到深红）
colors = ['#ffffcc', '#ffeda3', '#feb24c', '#fd8d3c', '#f03b20', '#bd0026']
custom_cmap = LinearSegmentedColormap.from_list('custom_red', colors, N=256)

# 创建图形
fig = plt.figure(figsize=(16, 10))

# 1. 主图：渐变色热力图
ax1 = plt.subplot2grid((2, 2), (0, 0), colspan=2)

# 绘制热力图
im = ax1.imshow(convexity_grid, cmap=custom_cmap, aspect='auto', 
                origin='lower', interpolation='bilinear',
                extent=[maturities[0]-0.5, maturities[-1]+0.5, 
                       coupons[0]-0.5, coupons[-1]+0.5])

# 添加等高线
contour_levels = np.linspace(convexity_grid.min(), convexity_grid.max(), 10)
contour = ax1.contour(X, Y, convexity_grid, levels=contour_levels, 
                      colors='white', alpha=0.5, linewidths=0.5)
ax1.clabel(contour, inline=True, fontsize=8, fmt='%.0f')

# 设置坐标轴
ax1.set_xlabel('期限 (年)', fontsize=12, fontweight='bold')
ax1.set_ylabel('票面利率 (%)', fontsize=12, fontweight='bold')
ax1.set_title('债券凸性热力图：期限 vs 票面利率\n(到期收益率固定为5%)', 
              fontsize=14, fontweight='bold', pad=20)

# 添加颜色条
cbar = plt.colorbar(im, ax=ax1, label='凸性', shrink=0.8, pad=0.05)
cbar.ax.tick_params(labelsize=10)

# 在图上添加关键点标注
key_points = [(5, 2), (10, 5), (20, 8), (30, 10)]
for mat, coup in key_points:
    if coup <= coupons[-1] and mat <= maturities[-1]:
        conv_val = convexity_grid[int(coup)-1, int(mat)-1]
        ax1.plot(mat, coup, 'ro', markersize=8, markerfacecolor='white', 
                markeredgecolor='red', markeredgewidth=2)
        ax1.annotate(f'{conv_val:.1f}', xy=(mat, coup), xytext=(5, 5), 
                    textcoords='offset points', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

# 2. 右上：不同票面利率下凸性随期限变化（渐变线条）
ax2 = plt.subplot2grid((2, 2), (0, 1))

# 选取几个代表性的票面利率
sample_coupons = [1, 3, 5, 7, 10]
colors_line = plt.cm.RdYlBu_r(np.linspace(0, 1, len(sample_coupons)))

for idx, coup in enumerate(sample_coupons):
    conv_values = []
    for mat in maturities:
        conv_values.append(convexity(coup, ytm_fixed, mat))
    
    ax2.plot(maturities, conv_values, linewidth=2.5, 
            color=colors_line[idx], label=f'票面利率 {coup}%')
    
    # 标记最大值点
    max_idx = np.argmax(conv_values)
    ax2.plot(maturities[max_idx], conv_values[max_idx], 'o', 
            color=colors_line[idx], markersize=6, markeredgecolor='black', markeredgewidth=0.5)

ax2.set_xlabel('期限 (年)', fontsize=11, fontweight='bold')
ax2.set_ylabel('凸性', fontsize=11, fontweight='bold')
ax2.set_title('不同票面利率下的凸性-期限曲线', fontsize=12, fontweight='bold')
ax2.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.set_facecolor('#f8f9fa')

# 3. 右下：不同期限下凸性随票面利率变化
ax3 = plt.subplot2grid((2, 2), (1, 1))

sample_maturities = [5, 10, 15, 20, 30]
colors_line2 = plt.cm.viridis(np.linspace(0, 1, len(sample_maturities)))

for idx, mat in enumerate(sample_maturities):
    conv_values = []
    for coup in coupons:
        conv_values.append(convexity(coup, ytm_fixed, mat))
    
    ax3.plot(coupons, conv_values, linewidth=2.5, 
            color=colors_line2[idx], label=f'{mat}年期')
    
    # 标记最小值点
    min_idx = np.argmin(conv_values)
    ax3.plot(coupons[min_idx], conv_values[min_idx], 's', 
            color=colors_line2[idx], markersize=6, markeredgecolor='black', markeredgewidth=0.5)

ax3.set_xlabel('票面利率 (%)', fontsize=11, fontweight='bold')
ax3.set_ylabel('凸性', fontsize=11, fontweight='bold')
ax3.set_title('不同期限下的凸性-票面利率曲线', fontsize=12, fontweight='bold')
ax3.legend(loc='upper right', fontsize=9, framealpha=0.9)
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.set_facecolor('#f8f9fa')

# 4. 左下：3D曲面图
ax4 = plt.subplot2grid((2, 2), (1, 0), projection='3d')

# 为了更好的视觉效果，采样稍稀疏的点
sample_coupons_3d = np.arange(1, 11, 0.5)
sample_maturities_3d = np.arange(1, 31, 0.5)
X_3d, Y_3d = np.meshgrid(sample_maturities_3d, sample_coupons_3d)
Z_3d = np.zeros_like(X_3d)

for i, coup in enumerate(sample_coupons_3d):
    for j, mat in enumerate(sample_maturities_3d):
        Z_3d[i, j] = convexity(coup, ytm_fixed, mat)

# 绘制曲面
surf = ax4.plot_surface(X_3d, Y_3d, Z_3d, cmap=custom_cmap, 
                        linewidth=0, antialiased=True, alpha=0.9)

ax4.set_xlabel('期限 (年)', fontsize=10, labelpad=8)
ax4.set_ylabel('票面利率 (%)', fontsize=10, labelpad=8)
ax4.set_zlabel('凸性', fontsize=10, labelpad=8)
ax4.set_title('凸性三维曲面图', fontsize=12, fontweight='bold', pad=15)

# 调整视角
ax4.view_init(elev=25, azim=-60)

plt.suptitle('债券凸性完整分析：影响因素与变化规律', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout()
plt.show()

# 打印关键结论
print("\n" + "="*80)
print("凸性分析关键结论")
print("="*80)

print("\n【凸性大小规律】")
print("1. 期限越长 → 凸性越大（非线性增长）")
print("2. 票面利率越低 → 凸性越大")
print("3. 到期收益率越低 → 凸性越大")

print("\n【凸性的经济含义】")
print("• 正凸性：利率下降时价格上涨更多，利率上升时价格下跌更少")
print("• 凸性越大，债券对利率变化的\"弯度\"越大，对投资者越有利")

print("\n【实际应用建议】")
print("• 长期限、低票息债券凸性大，适合预期利率大幅下降时持有")
print("• 短期限、高票息债券凸性小，利率风险暴露更线性")
print("• 凸性修正使久期风险管理更精确")

plt.tight_layout()
plt.show()
