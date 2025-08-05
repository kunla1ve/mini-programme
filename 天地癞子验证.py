# -*- coding: utf-8 -*-
"""
Created on Tue Aug  5 20:39:08 2025

@author: kunlave
"""

import math

def comb(n, k):
    """计算组合数 C(n, k)"""
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)

def calculate_probability():
    # 牌堆总数
    total_cards = 54

    # 癞子牌数量
    laizi_cards = 8

    # 非癞子牌数量
    non_laizi_cards = total_cards - laizi_cards

    # 地主手牌数
    landlord_cards = 20

    # 农民手牌数
    farmer_cards = 17

    # 某个非癞子点数的自然牌数量
    natural_cards_per_point = 4

    # 计算地主满足条件的概率
    # 地主手牌需要包含 4张自然牌 + 8张癞子牌，共12张固定牌
    # 剩余 20 - 12 = 8 张牌从其他牌中选
    remaining_cards_landlord = non_laizi_cards - natural_cards_per_point
    landlord_favorable = comb(remaining_cards_landlord, landlord_cards - 12)
    landlord_total = comb(total_cards, landlord_cards)
    prob_landlord = landlord_favorable / landlord_total

    # 计算农民满足条件的概率
    # 农民手牌需要包含 4张自然牌 + 8张癞子牌，共12张固定牌
    # 剩余 17 - 12 = 5 张牌从其他牌中选
    remaining_cards_farmer = non_laizi_cards - natural_cards_per_point
    farmer_favorable = comb(remaining_cards_farmer, farmer_cards - 12)
    farmer_total = comb(total_cards, farmer_cards)
    prob_farmer = farmer_favorable / farmer_total

    # 非癞子点数数量（假设癞子点数为2个，非癞子点数为11个）
    non_laizi_points = 11

    # 总概率
    total_prob = non_laizi_points * (prob_landlord + 2 * prob_farmer)

    return total_prob

# 计算并输出概率
probability = calculate_probability()