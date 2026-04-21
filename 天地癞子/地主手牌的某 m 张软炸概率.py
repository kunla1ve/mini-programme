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

def create_deck():
    """创建标准54张牌，返回牌列表（普通牌用点数1-13表示，大小王用'sJOKER'/'bJOKER'表示）"""
    deck = []
    # 普通牌：点数1-13，每种4张
    for point in range(1, 14):
        for _ in range(4):
            deck.append(point)
    # 大小王（不作为癞子，也不作为软炸元素）
    deck.append('sJOKER')  # 小王
    deck.append('bJOKER')  # 大王
    return deck

def is_laizi(card, laizi_points):
    """判断一张牌是否为癞子（癞子只能是普通牌点数）"""
    if card in ['sJOKER', 'bJOKER']:
        return False
    return card in laizi_points

def has_soft_bomb(hand, laizi_points, m):
    """
    判断手牌中是否有m张软炸（由m张相同点数的牌组成，癞子可以补全）
    要求：至少有一张普通牌（不能全癞子）
    注意：大小王不参与软炸
    """
    # 计算癞子数量（只统计手牌中的普通牌癞子）
    laizi_count = sum(1 for c in hand if is_laizi(c, laizi_points))
    
    # 统计非癞子的普通牌数量（不包括大小王）
    normal_counts = Counter()
    for c in hand:
        if c not in ['sJOKER', 'bJOKER'] and not is_laizi(c, laizi_points):
            normal_counts[c] += 1
    
    # 对每个点数，检查是否能用癞子补成m张，且至少有一张普通牌
    for pt, cnt in normal_counts.items():
        # 需要补的癞子数量
        need_laizi = m - cnt
        if need_laizi >= 0 and need_laizi <= laizi_count:
            # 确保至少有一张普通牌（cnt >= 1）
            if cnt >= 1:
                return True
    
    return False

def simulate(laizi_points, m, trials=100000):
    """模拟地主手牌，计算软炸概率"""
    deck = create_deck()
    laizi_set = set(laizi_points)
    success = 0
    
    # 使用position=0让进度条固定在同一个位置
    for _ in tqdm(range(trials), desc=f"模拟 m={m}", unit="次", 
                  position=0, leave=False):
        random.shuffle(deck)
        landlord_hand = deck[:20]  # 地主20张牌
        if has_soft_bomb(landlord_hand, laizi_set, m):
            success += 1
    
    return success / trials

if __name__ == "__main__":
    # 设置癞子点数（只能是普通牌点数1-13）
    laizi = [1, 2]  # 点数1和2作为癞子
    
    m_values = list(range(12, 13))  # 测试m=12
    # 外层进度条也使用position=1避免冲突
    for m in tqdm(m_values, desc="总进度", unit="m值", position=1, leave=True):
        prob = simulate(laizi, m, trials=100000000)
        print(f"\n地主 m={m} 软炸概率 ≈ {prob:.8f}")
        print()
