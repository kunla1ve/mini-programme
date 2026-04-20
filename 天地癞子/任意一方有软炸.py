# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 18:55:29 2026

@author: kunlave
"""

import random
from collections import Counter

def create_deck(laizi_points):
    deck = []
    for point in range(1, 14):
        for _ in range(4):
            deck.append(point)
    deck.extend(['joker', 'JOKER'])
    return deck

def is_laizi(card, laizi_points):
    return card in laizi_points

def has_soft_bomb(hand, laizi_points, m):
    l = sum(1 for c in hand if is_laizi(c, laizi_points))
    if m <= l:
        return True
    
    normal_counts = Counter()
    for c in hand:
        if not is_laizi(c, laizi_points) and c not in ['joker', 'JOKER']:
            normal_counts[c] += 1
    
    for cnt in normal_counts.values():
        for t in range(1, cnt+1):
            if m - t <= l and m - t >= 0:
                return True
    return False

def simulate_total(laizi_points, m, trials=100000):
    deck = create_deck(laizi_points)
    laizi_set = set(laizi_points)
    
    count_A = 0  # 地主有
    count_B = 0  # 农民有
    count_both = 0
    count_either = 0
    
    for _ in range(trials):
        random.shuffle(deck)
        landlord_hand = deck[:20]
        farmer_hand = deck[20:37]
        
        has_landlord = has_soft_bomb(landlord_hand, laizi_set, m)
        has_farmer = has_soft_bomb(farmer_hand, laizi_set, m)
        
        if has_landlord:
            count_A += 1
        if has_farmer:
            count_B += 1
        if has_landlord and has_farmer:
            count_both += 1
        if has_landlord or has_farmer:
            count_either += 1
    
    return {
        'P_landlord': count_A / trials,
        'P_farmer': count_B / trials,
        'P_both': count_both / trials,
        'P_either': count_either / trials
    }

# 测试
if __name__ == "__main__":
    laizi = [1, 2]
    for m in range(5, 13):   #从5到12炸
        probs = simulate_total(laizi, m, trials=100000)
        print(f"\n=== m={m} 张软炸 ===")
        print(f"地主概率: {probs['P_landlord']:.8f}")
        print(f"农民概率: {probs['P_farmer']:.8f}")
        print(f"双方都有: {probs['P_both']:.8f}")
        print(f"至少一方有: {probs['P_either']:.8f}")
