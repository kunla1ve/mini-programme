# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 22:30:26 2026

@author: kunlave
"""


'地主手牌的某 m 张软炸概率'
'软炸12概率 ≈ 0.0000035000'
'地主 m=12 软炸概率 ≈ 0.0000100000'


import random
from collections import Counter
from tqdm import tqdm

# 定义牌结构：普通牌 (点数, 花色无所谓，只需要点数区分)
def create_deck(laizi_points):
    suits = ['s', 'h', 'd', 'c']
    deck = []
    for point in range(1, 14):  # 1~13
        for _ in range(4):
            deck.append(point)
    deck.extend(['joker', 'JOKER'])  # 大小王
    # 将 laizi_points 中的点数的牌改为标记为 laizi
    # 这里简单处理：标记手牌时判断该牌是否在 laizi_points 中
    return deck, laizi_points

def is_laizi(card, laizi_points):
    return card in laizi_points

def has_soft_bomb(hand, laizi_points, m):
    # hand: list of points (普通点数) or 'joker'/'JOKER'
    # laizi_points: set of int points 作为癞子
    l = sum(1 for c in hand if is_laizi(c, laizi_points))
    
    # 全癞子
    if m <= l:
        return True
    
    # 普通牌计数
    normal_counts = Counter()
    for c in hand:
        if not is_laizi(c, laizi_points) and c not in ['joker', 'JOKER']:
            normal_counts[c] += 1
    
    # 对每个普通点数，尝试作为软炸主体
    for pt, cnt in normal_counts.items():
        for t in range(1, cnt+1):  # t 张普通牌用这个点数
            need_laizi = m - t
            if need_laizi >= 0 and need_laizi <= l:
                return True
    return False

def simulate(laizi_points, m, trials=100000):
    deck, _ = create_deck(laizi_points)
    laizi_set = set(laizi_points)
    # 洗牌
    success = 0
    
    # 添加进度条
    for _ in tqdm(range(trials), desc=f"模拟 m={m}", unit="次"):
        random.shuffle(deck)
        landlord_hand = deck[:20]   #  地主手牌20 农民17
        if has_soft_bomb(landlord_hand, laizi_set, m):
            success += 1
    return success / trials

# 测试
if __name__ == "__main__":
    laizi = [1, 2]  # 选点数 1 和 2 作为癞子
    
    # 外层总进度条
    m_values = list(range(5, 13))
    for m in tqdm(m_values, desc="总进度", unit="m值"):
        prob = simulate(laizi, m, trials=100000000)
        print(f"地主 m={m} 软炸概率 ≈ {prob:.8f}")
        print()
