import matplotlib.pyplot as plt
import matplotlib.patches as patches
from math import sqrt

# 给定概率（用于标注）
prob_data = {
    "地主概率": 0.88818080,
    "单个农民概率": 0.73892750,
    "两个农民都有": 0.51370220,
    "地主+任一农民": 0.63705985,
    "三方都有": 0.42166960
}

# 创建图形
fig, ax = plt.subplots(figsize=(10, 8))
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.2, 1.2)
ax.set_aspect('equal')
ax.axis('off')

# 手动绘制三个重叠圆（位置和半径经过调整以近似展示重叠关系）
# 地主（红色）- 中心左偏上
circle_landlord = plt.Circle((-0.4, 0.3), 0.9, color='red', alpha=0.4, label='地主')
# 农民 A（蓝色）- 中心右偏下
circle_farmerA = plt.Circle((0.4, -0.2), 0.85, color='blue', alpha=0.4, label='农民 A')
# 农民 B（绿色）- 中心右偏上
circle_farmerB = plt.Circle((0.3, 0.5), 0.85, color='green', alpha=0.4, label='农民 B')

ax.add_patch(circle_landlord)
ax.add_patch(circle_farmerA)
ax.add_patch(circle_farmerB)

# 添加标签
ax.text(-0.4, 0.5, '地主\n88.8%', fontsize=12, ha='center', fontweight='bold')
ax.text(0.7, -0.5, '农民 A\n73.9%', fontsize=12, ha='center', fontweight='bold')
ax.text(0.6, 0.8, '农民 B\n73.9%', fontsize=12, ha='center', fontweight='bold')

# 标注关键重叠区域（用箭头指向大致位置）
# 三方重叠区域
ax.annotate('三方都有\n42.2%', xy=(0.1, 0.25), xytext=(-0.8, -0.6),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5),
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7))

# 两个农民重叠（不含地主）
ax.annotate('两个农民都有\n51.4%', xy=(0.5, 0.15), xytext=(1.0, -0.8),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5),
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))

# 地主+任一农民重叠
ax.annotate('地主+任一农民\n63.7%', xy=(-0.1, 0.1), xytext=(-1.2, 0.6),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5),
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.7))

# 添加图例
legend_elements = [patches.Patch(facecolor='red', alpha=0.4, label='地主 (88.8%)'),
                   patches.Patch(facecolor='blue', alpha=0.4, label='农民 A (73.9%)'),
                   patches.Patch(facecolor='green', alpha=0.4, label='农民 B (73.9%)')]
ax.legend(handles=legend_elements, loc='upper left', fontsize=10)

plt.title('概率重合示意图\n（圆面积/重叠面积仅为示意，具体概率见标注）', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

# 同时输出数值表格
print("\n" + "="*50)
print("概率数据汇总")
print("="*50)
for key, value in prob_data.items():
    print(f"{key:15}: {value:.4f} ({value*100:.2f}%)")
print("="*50)
print("说明：图中圆的大小和重叠区域为示意图，")
print("      具体概率值以左侧数字为准。")
