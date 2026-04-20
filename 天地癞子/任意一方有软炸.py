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
        for t in range(1, cnt + 1):
            need_laizi = m - t
            if 0 <= need_laizi <= l:
                return True
    return False

def simulate_total(laizi_points, m, trials=100000):
    deck = create_deck(laizi_points)
    laizi_set = set(laizi_points)
    
    count_A = 0  # 地主
    count_B = 0  # 农民1
    count_C = 0  # 农民2
    count_AB = 0
    count_AC = 0
    count_BC = 0
    count_ABC = 0
    count_any = 0
    
    for _ in range(trials):
        random.shuffle(deck)
        landlord = deck[:20]
        farmer1 = deck[20:37]
        farmer2 = deck[37:54]
        
        has_A = has_soft_bomb(landlord, laizi_set, m)
        has_B = has_soft_bomb(farmer1, laizi_set, m)
        has_C = has_soft_bomb(farmer2, laizi_set, m)
        
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
    
    return {
        'P_landlord': count_A / trials,
        'P_farmer_each': count_B / trials,  # 对称，等于 count_C/trials
        'P_both_farmers': count_BC / trials,
        'P_landlord_and_one_farmer': (count_AB + count_AC) / trials / 2,  # 平均一下
        'P_all_three': count_ABC / trials,
        'P_any': count_any / trials
    }

# 测试
if __name__ == "__main__":
    laizi = [1, 2]
    print("癞子点数:", laizi)
    print()
    for m in range(5, 13):
        probs = simulate_total(laizi, m, trials=50000)
        print(f"=== m={m} 张软炸 ===")
        print(f"  地主概率: {probs['P_landlord']:.8f}")
        print(f"  单个农民概率: {probs['P_farmer_each']:.8f}")
        print(f"  两个农民都有: {probs['P_both_farmers']:.8f}")
        print(f"  地主+任一农民: {probs['P_landlord_and_one_farmer']:.8f}")
        print(f"  三方都有: {probs['P_all_three']:.8f}")
        print(f"  ★ 总牌局至少一方有: {probs['P_any']:.8f}")
        print()
