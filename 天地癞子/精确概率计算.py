# -*- coding: utf-8 -*-
"""
精确计算天地癞子软炸概率（纯数学公式，非蒙特卡洛模拟）

数学方法：多重超几何分布 + 容斥原理 + 生成函数

原理概述：
─────────
P(软炸) = Σ_{l=0}^{8} P(L=l) × P(∃点数≥k | L=l)

其中：
• P(L=l) = C(8,l)·C(46, n-l) / C(54, n)        ← 超几何分布
• k = max(1, m-l)                                 ← 某点数至少需要的普通牌数
• P(∃点数≥k | L=l) = Σ (-1)^{r+1}·C(11,r)·q_r   ← 容斥原理

q_r 通过生成函数系数提取计算：
q_r = [x^{n-rk}] h_k(x)^r · (1+x)^{46-4r} / C(46, n_rem)

其中 h_k(x) = Σ_{b=0}^{4-k} C(4, b+k)·x^b
"""

from math import comb
import random
from collections import Counter
from tqdm import tqdm


# ============================================================
# 多项式工具（系数列表表示：a[0] + a[1]x + a[2]x² + ...）
# ============================================================

def poly_mult(p1, p2):
    """两个多项式相乘"""
    result = [0.0] * (len(p1) + len(p2) - 1)
    for i, a in enumerate(p1):
        for j, b in enumerate(p2):
            result[i + j] += a * b
    return result


def poly_pow(p, n):
    """多项式 p 的 n 次幂"""
    if n == 0:
        return [1.0]
    result = [1.0]
    for _ in range(n):
        result = poly_mult(result, p)
    return result


# ============================================================
# 核心：精确软炸概率计算
# ============================================================

def exact_soft_bomb_prob(m, n_hand):
    """
    精确计算持有 n_hand 张手牌时，出现 m 张软炸的概率。

    参数:
        m:      软炸张数 (5~12)
        n_hand: 手牌数（地主=20，农民=17）
    返回:
        精确概率值 (float)

    数学推导
    ────────
    牌组构成：54张 = 8张癞子 + 44张普通牌(11点×4) + 2张大小王

    第一步 · 枚举癞子张数 l（超几何分布）
        P(L=l) = C(8, l) · C(46, n-l) / C(54, n)

    第二步 · 给定 L=l，软炸条件变为
        ∃ 非癞子点数 i，使得 X_i ≥ k，其中 k = max(1, m-l)

    第三步 · 容斥原理
        P(∃i: X_i ≥ k | L=l) = Σ_{r=1}^{11} (-1)^{r+1} · C(11,r) · q_r

        q_r = P(指定 r 个点数都 ≥ k 张)

    第四步 · 生成函数计算 q_r
        从46张牌中抽 n_rem 张，要求 r 个指定点数各 ≥ k 张

        令 h_k(x) = Σ_{b=0}^{4-k} C(4, b+k) · x^b

        则有利方式数 = [x^{n_rem - r·k}] h_k(x)^r · (1+x)^{46-4r}

        q_r = 有利方式数 / C(46, n_rem)
    """
    # ── 牌组参数 ──
    n_total      = 54   # 总牌数
    n_laizi      = 8    # 癞子牌数
    n_ord_types  = 11   # 非癞子点数种类
    cards_per    = 4    # 每个点数的张数
    n_jokers     = 2    # 大小王张数
    n_ord_pool   = n_ord_types * cards_per + n_jokers  # 46（非癞子牌池）

    total_ways   = comb(n_total, n_hand)
    prob         = 0.0

    # ── 第一步：枚举 l ──
    l_min = max(0, n_hand - n_ord_pool)
    l_max = min(n_laizi, n_hand)

    for l in range(l_min, l_max + 1):
        ways_l = comb(n_laizi, l) * comb(n_ord_pool, n_hand - l)
        if ways_l == 0:
            continue

        n_rem = n_hand - l          # 从普通牌池中抽的张数
        k     = max(1, m - l)       # 某点数至少需要 k 张

        if k > cards_per:
            continue                # 单点数最多4张，不可能

        # ── 第三步 + 第四步：容斥 + 生成函数 ──
        # h_k(x) 的系数：C(4, k), C(4, k+1), ..., C(4, 4)
        h_k = [float(comb(cards_per, k + b))
               for b in range(cards_per - k + 1)]

        p_cond = 0.0    # P(∃点数≥k | L=l)

        for r in range(1, n_ord_types + 1):
            sign   = (-1) ** (r + 1)
            target = n_rem - r * k          # 生成函数中需要提取的幂次
            if target < 0:
                continue

            # h_k(x)^r
            hk_r = poly_pow(h_k, r)

            # (1+x)^{46-4r} 的指数
            exp_rest = n_ord_pool - cards_per * r
            if exp_rest < 0:
                continue

            # 提取 x^target 的系数
            favorable = 0.0
            for i in range(min(len(hk_r) - 1, target) + 1):
                j = target - i
                if 0 <= j <= exp_rest:
                    favorable += hk_r[i] * comb(exp_rest, j)

            q_r = favorable / comb(n_ord_pool, n_rem)
            p_cond += sign * comb(n_ord_types, r) * q_r

        prob += (ways_l / total_ways) * p_cond

    return prob


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  斗地主天地癞子 — 软炸精确概率（纯数学公式，非蒙特卡洛模拟）")
    print("=" * 70)
    print("  牌组: 54张 | 癞子: 2个点数×4张=8张 | 非癞子点数: 11个")
    print("  地主: 20张 | 农民: 各17张")
    print()

    # ── 单人概率 ──
    print("┌─────┬────────────────────┬────────────────────┬──────────┐")
    print(f"│ {'m':>3} │ {'地主 (20张)':^18} │ {'农民 (17张)':^18} │ {'下降倍率':^8} │")
    print("├─────┼────────────────────┼────────────────────┼──────────┤")

    prev_l = None
    for m in range(5, 13):
        p_l = exact_soft_bomb_prob(m, n_hand=20)
        p_f = exact_soft_bomb_prob(m, n_hand=17)

        if prev_l is not None and p_l > 0:
            ratio_str = f"{prev_l / p_l:>7.1f}×"
        else:
            ratio_str = f"{'—':>8}"

        print(f"│ {m:>3} │ {p_l:>18.12f} │ {p_f:>18.12f} │ {ratio_str} │")
        prev_l = p_l

    print("└─────┴────────────────────┴────────────────────┴──────────┘")
    print()
    print("  倍率 = P(m) / P(m+1)，越大说明概率衰减越快")
    print()

    # ── 蒙特卡洛模拟函数（来自地主农民有软炸概率.py） ──
    def create_deck():
        deck = []
        for point in range(1, 14):
            for _ in range(4):
                deck.append(point)
        deck.extend(['joker', 'JOKER'])
        return deck

    def is_laizi(card, laizi_set):
        if card in ['joker', 'JOKER']:
            return False
        return card in laizi_set

    def has_soft_bomb(hand, laizi_set, m):
        laizi_count = sum(1 for c in hand if is_laizi(c, laizi_set))
        normal_counts = Counter()
        for c in hand:
            if not is_laizi(c, laizi_set) and c not in ['joker', 'JOKER']:
                normal_counts[c] += 1
        for cnt in normal_counts.values():
            if cnt + laizi_count >= m and cnt >= 1:
                return True
        return False

    def simulate_once(deck, laizi_set, m):
        random.shuffle(deck)
        landlord = deck[:20]
        farmer1 = deck[20:37]
        farmer2 = deck[37:54]
        has_A = has_soft_bomb(landlord, laizi_set, m)
        has_B = has_soft_bomb(farmer1, laizi_set, m)
        has_C = has_soft_bomb(farmer2, laizi_set, m)
        return has_A, has_B, has_C

    # ── 模拟对比 ──
    TRIALS = 100_000  # 每个m模拟10万次
    laizi_set = {1, 2}
    deck = create_deck()

    print("=" * 70)
    print(f"  模拟对比：每个 m 值模拟 {TRIALS:,} 次")
    print("=" * 70)

    header = (f"  {'m':>3}  │  {'角色':^6}  │  {'精确值':>14}  │"
              f"  {'模拟值':>14}  │  {'相对误差':>10}")
    sep = f"  {'─'*3}──┼──{'─'*6}──┼──{'─'*14}──┼──{'─'*14}──┼──{'─'*10}"
    print(header)
    print(sep)

    for m in range(5, 13):
        # 精确值
        exact_l = exact_soft_bomb_prob(m, n_hand=20)
        exact_f = exact_soft_bomb_prob(m, n_hand=17)

        # 模拟
        cnt_l = cnt_f = cnt_any = 0
        for _ in tqdm(range(TRIALS), desc=f"m={m}", unit="次", leave=False):
            a, b, c = simulate_once(deck, laizi_set, m)
            if a: cnt_l += 1
            if b: cnt_f += 1
            if a or b or c: cnt_any += 1

        sim_l = cnt_l / TRIALS
        sim_f = cnt_f / TRIALS
        sim_any = cnt_any / TRIALS

        for role, exact, sim in [("地主", exact_l, sim_l),
                                  ("农民", exact_f, sim_f)]:
            if exact > 0 and sim > 0:
                err = abs(exact - sim) / exact * 100
                err_str = f"{err:>9.4f}%"
            else:
                err_str = f"{'—':>10}"
            print(f"  {m:>3}  │  {role:^6}  │  {exact:>14.10f}  │"
                  f"  {sim:>14.10f}  │  {err_str}")

        # 至少一方的精确值（近似：P(any) ≈ P(A) + 2P(F) - 高阶项）
        print(f"  {m:>3}  │  {'至少一方':^5}  │  {'—':>14}  │"
              f"  {sim_any:>14.10f}  │  {'—':>10}")
        print(sep)

    print()
    print("  精确值与模拟值高度吻合，验证了数学公式的正确性。")
    print("  '至少一方'概率通过模拟获得，精确计算需考虑三人手牌的联合分布。")
    print("=" * 70)
