# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 15:39:59 2026

@author: hongl
"""

# -*- coding: utf-8 -*-
"""
Spyder 编辑器

这是一个临时脚本文件。
"""

import numpy as np
import matplotlib.pyplot as plt

# Set parameters
P = 1.0  # Principal amount, set to 1 for easier comparison
t = np.linspace(0, 20, 500)  # Time range: 0 to 20 years, 500 points for higher resolution

# Define different compounding frequency and interest rate scenarios
scenarios = [
    {'n': 1, 'r': 0.05, 'label': 'n=1, r=5%', 'linestyle': '-', 'color': 'blue'},
    {'n': 4, 'r': 0.05, 'label': 'n=4, r=5%', 'linestyle': '--', 'color': 'blue'},
    {'n': 12, 'r': 0.05, 'label': 'n=12, r=5%', 'linestyle': ':', 'color': 'blue'},
    {'n': 365, 'r': 0.05, 'label': 'n=365, r=5%', 'linestyle': '-.', 'color': 'blue'},
    {'n': 1, 'r': 0.08, 'label': 'n=1, r=8%', 'linestyle': '-', 'color': 'red'},
    {'n': 4, 'r': 0.08, 'label': 'n=4, r=8%', 'linestyle': '--', 'color': 'red'},
    {'n': 12, 'r': 0.08, 'label': 'n=12, r=8%', 'linestyle': ':', 'color': 'red'},
    {'n': 365, 'r': 0.08, 'label': 'n=365, r=8%', 'linestyle': '-.', 'color': 'red'},
    {'n': 1, 'r': 0.10, 'label': 'n=1, r=10%', 'linestyle': '-', 'color': 'green'},
    {'n': 4, 'r': 0.10, 'label': 'n=4, r=10%', 'linestyle': '--', 'color': 'green'},
    {'n': 12, 'r': 0.10, 'label': 'n=12, r=10%', 'linestyle': ':', 'color': 'green'},
    {'n': 365, 'r': 0.10, 'label': 'n=365, r=10%', 'linestyle': '-.', 'color': 'green'},
]

# Create high-resolution figure
plt.figure(figsize=(14, 9), dpi=300)  # Increased size and DPI for higher resolution

# Calculate and plot each curve
for scenario in scenarios:
    n = scenario['n']
    r = scenario['r']
    # Compound interest formula: A = P * (1 + r/n)^(n*t)
    A = P * (1 + r/n)**(n * t)
    plt.plot(t, A, 
             label=scenario['label'], 
             linestyle=scenario['linestyle'], 
             color=scenario['color'],
             linewidth=2.5,
             alpha=0.8)

# Add plot details with larger fonts
plt.xlabel('Time (Years)', fontsize=16, fontweight='bold')
plt.ylabel('Total Value (Multiple of Principal)', fontsize=16, fontweight='bold')
plt.title('Compound Interest Curves: Effect of Interest Rates and Compounding Frequencies', 
          fontsize=18, fontweight='bold', pad=20)

# Add legend with better positioning and larger font
plt.legend(loc='upper left', fontsize=12, framealpha=0.9)

# Add grid for better readability
plt.grid(True, alpha=0.4, linestyle='--')

# Use logarithmic scale to better visualize long-term differences
plt.yscale('log')

# Set custom y-axis ticks for better readability on log scale
plt.yticks([1, 2, 5, 10], ['1x', '2x', '5x', '10x'], fontsize=12)
plt.xticks(fontsize=12)



# Adjust layout to prevent label cutting
plt.tight_layout()

# Save high-resolution image
plt.savefig('compound_interest_curves_high_res.png', dpi=300, bbox_inches='tight')

# Display the plot
plt.show()

# Additional: Print final values for reference after 20 years
print("Final values after 20 years (Multiple of principal):")
for scenario in scenarios:
    n = scenario['n']
    r = scenario['r']
    final_value = P * (1 + r/n)**(n * 20)
    print(f"{scenario['label']}: {final_value:.2f}x")
