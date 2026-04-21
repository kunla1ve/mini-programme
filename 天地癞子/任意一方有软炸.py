# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 21:40:33 2026
Modified on 2026-04-21

@author: kunlave
"""

import random
from collections import Counter
from tqdm import tqdm  # 需要安装: pip install tqdm

def create_deck(laizi_points):
    """
    创建一副完整的扑克牌（54张）
    参数:
        laizi_points: 癞子点数列表（仅用于文档说明，实际创建时不影响）
    返回:
        包含54张牌的列表，其中1-13各4张，加上大小王（'joker'和'JOKER'）
    """
    deck = []
    # 添加1-13点数的牌，每个点数4张（对应四种花色）
    for point in range(1, 14):
        for _ in range(4):
            deck.append(point)
    # 添加大小王
    deck.extend(['joker', 'JOKER'])
    return deck

def is_laizi(card, laizi_points):
    """
    判断一张牌是否为癞子
    注意：大小王不能作为癞子
    参数:
        card: 牌面值（数字或字符串）
        laizi_points: 癞子点数集合
    返回:
        True表示是癞子，False表示不是
    """
    # 大小王永远不能作为癞子
    if card in ['joker', 'JOKER']:
        return False
    return card in laizi_points

def has_soft_bomb(hand, laizi_points, m):
    """
    判断一手牌是否包含m张软炸（癞子可替代其他牌形成炸弹）
    软炸定义：由t张相同点数的普通牌 + (m-t)张癞子组成，其中1≤t≤m（至少1张普通牌）
    注意：大小王不能作为软炸的元素
    
    参数:
        hand: 手牌列表
        laizi_points: 癞子点数集合
        m: 软炸所需的总张数
    返回:
        True表示有软炸，False表示没有
    """
    # 统计手牌中的癞子数量（排除大小王）
    laizi_count = sum(1 for c in hand if is_laizi(c, laizi_points))
    
    # 统计非癞子、非王牌的普通牌数量
    normal_counts = Counter()
    for c in hand:
        # 排除癞子、大小王（大小王不能作为软炸元素）
        if not is_laizi(c, laizi_points) and c not in ['joker', 'JOKER']:
            normal_counts[c] += 1
    
    # 检查每种点数的牌能否与癞子组合成m张软炸
    for cnt in normal_counts.values():
        # t是实际普通牌的数量，从1到cnt（至少1张普通牌）
        for t in range(1, cnt + 1):
            need_laizi = m - t  # 需要的癞子数量
            # 需要的癞子数量必须在0到laizi_count之间
            # 且t >= 1（已有保证），且need_laizi >= 0
            if 0 <= need_laizi <= laizi_count:
                return True
    
    # 全癞子不能算软炸（因为没有普通牌），所以这里不检查laizi_count >= m的情况
    
    return False

def simulate_total(laizi_points, m, trials=100000):
    """
    模拟斗地主发牌，统计各方拥有软炸的概率
    
    参数:
        laizi_points: 癞子点数列表
        m: 软炸所需张数
        trials: 模拟次数
    
    返回:
        包含各种概率的字典
    """
    deck = create_deck(laizi_points)
    laizi_set = set(laizi_points)
    
    # 初始化计数器
    count_A = 0      # 地主有软炸
    count_B = 0      # 农民1有软炸
    count_C = 0      # 农民2有软炸
    count_AB = 0     # 地主和农民1都有
    count_AC = 0     # 地主和农民2都有
    count_BC = 0     # 两个农民都有
    count_ABC = 0    # 三方都有
    count_any = 0    # 至少一方有
    
    # 使用tqdm显示进度条
    print(f"正在模拟 {trials:,} 次发牌...")
    for _ in tqdm(range(trials), desc="模拟进度", unit="次"):
        # 随机洗牌
        random.shuffle(deck)
        
        # 发牌：地主20张，农民各17张
        landlord = deck[:20]      # 地主手牌
        farmer1 = deck[20:37]     # 农民1手牌
        farmer2 = deck[37:54]     # 农民2手牌
        
        # 判断各方是否有软炸
        has_A = has_soft_bomb(landlord, laizi_set, m)
        has_B = has_soft_bomb(farmer1, laizi_set, m)
        has_C = has_soft_bomb(farmer2, laizi_set, m)
        
        # 更新计数器
        if has_A:
            count_A += 1
        if has_B:
            count_B += 1
        if has_C:
            count_C += 1
        if has_A and has_B:
            count_AB += 1
        if has_A and has_C:
            count_AC += 1
        if has_B and has_C:
            count_BC += 1
        if has_A and has_B and has_C:
            count_ABC += 1
        if has_A or has_B or has_C:
            count_any += 1
    
    print("\n模拟完成！计算结果：\n")
    
    # 返回概率结果
    return {
        'P_landlord': count_A / trials,           # 地主有软炸的概率
        'P_farmer_each': count_B / trials,        # 单个农民有软炸的概率（对称）
        'P_both_farmers': count_BC / trials,      # 两个农民都有软炸的概率
        'P_landlord_and_one_farmer': (count_AB + count_AC) / trials / 2,  # 地主和任一农民都有软炸的平均概率
        'P_all_three': count_ABC / trials,        # 三方都有软炸的概率
        'P_any': count_any / trials               # 至少一方有软炸的概率
    }

# 主程序入口
if __name__ == "__main__":
    # 设置癞子点数（这里设定1和2为癞子，但大小王不会成为癞子）
    laizi = [1, 2]
    print("="*60)
    print("斗地主软炸概率模拟程序")
    print("="*60)
    print(f"癞子点数: {laizi}")
    print("注意：大小王不能作为癞子，也不能作为软炸的元素")
    print("注意：全癞子组合不能算作软炸（必须至少有一张普通牌）")
    print("说明: 数字1-13表示点数，'joker'和'JOKER'表示大小王")
    print("="*60)
    print()
    
    # 模拟m=12张的软炸概率（可以修改m值）
    for m in range(5, 13):
        print(f"正在计算 m={m} 张软炸的概率...")
        print("-"*60)
        
        # 进行模拟（trials可调整，越大越精确但耗时更长）
        probs = simulate_total(laizi, m, trials=10000)  # 100万次模拟
        
        # 输出结果（保留8位小数）
        print(f"=== m={m} 张软炸 ===")
        print(f"  地主概率: {probs['P_landlord']:.8f} ({probs['P_landlord']*100:.4f}%)")
        print(f"  单个农民概率: {probs['P_farmer_each']:.8f} ({probs['P_farmer_each']*100:.4f}%)")
        print(f"  两个农民都有: {probs['P_both_farmers']:.8f} ({probs['P_both_farmers']*100:.4f}%)")
        print(f"  地主+任一农民: {probs['P_landlord_and_one_farmer']:.8f} ({probs['P_landlord_and_one_farmer']*100:.4f}%)")
        print(f"  三方都有: {probs['P_all_three']:.8f} ({probs['P_all_three']*100:.4f}%)")
        print(f"  ★ 总牌局至少一方有: {probs['P_any']:.8f} ({probs['P_any']*100:.4f}%)")
        print("="*60)
        print()
