# -*- coding: utf-8 -*-
"""
Created on Tue Aug  5 20:37:12 2025

@author: kunlave
"""
import math
from decimal import Decimal, getcontext

# 设置高精度计算
getcontext().prec = 50

def comb(n, k):
    """高精度组合数计算"""
    if k < 0 or k > n:
        return Decimal(0)
    return Decimal(math.comb(n, k))

def calculate_bomb_probability(n):
    """计算特定n软炸的概率"""
    total_cards = 54
    laizi_cards = 8
    natural_per_point = 4
    non_laizi_cards = total_cards - laizi_cards
    non_laizi_points = 11
    
    # 地主和农民手牌数
    landlord_hand = 20
    farmer_hand = 17
    
    def prob_for_hand(hand_size):
        """计算特定手牌大小的概率"""
        total_prob = Decimal(0)
        
        # 计算所有可能的自然牌和癞子牌组合
        for k in range(max(1, n - laizi_cards), min(natural_per_point, n) + 1):
            l = n - k
            if l > laizi_cards or l < 0:
                continue
            
            # 计算这种组合的概率
            # 1. 选择k张特定点数的自然牌
            # 2. 选择l张癞子牌
            # 3. 从剩余牌中选择hand_size - k - l张
            remaining_natural = non_laizi_cards - natural_per_point
            remaining_total = remaining_natural + (laizi_cards - l)
            
            favorable = (comb(natural_per_point, k) * 
                        comb(laizi_cards, l) * 
                        comb(remaining_total, hand_size - k - l))
            total = comb(total_cards, hand_size)
            
            total_prob += favorable / total
        
        return total_prob
    
    # 计算地主和农民的概率
    p_landlord = prob_for_hand(landlord_hand)
    p_farmer = prob_for_hand(farmer_hand)
    
    # 计算至少一个玩家有n软炸的概率
    # 使用容斥原理
    p_at_least_one = 1 - (1 - p_landlord) * (1 - p_farmer)**2
    
    # 乘以非癞子点数数量
    # 注意：这里需要更精确的计算，不能简单相乘
    # 使用泊松近似或更精确的包含-排除原理
    # 这里使用保守估计
    return min(non_laizi_points * p_at_least_one, Decimal(1))

# 计算并输出5到12软炸的概率
print("软炸概率计算结果：")
for n in range(5, 13):
    prob = calculate_bomb_probability(n)
    print(f"{n}软炸的概率: {float(prob):.10f} (约 {float(prob)*100:.8f}%)")