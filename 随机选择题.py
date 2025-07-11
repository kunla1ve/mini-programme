# -*- coding: utf-8 -*-
"""
Created on Thu Jul 10 18:03:06 2025

@author: hongl
"""

import random

def generate_answers(num_questions=100):
    """生成指定数量的随机选择题答案"""
    answers = []
    for _ in range(num_questions):
        answer = random.choice(['A', 'B', 'C', 'D'])
        answers.append(answer)
    return answers

# 生成100道题的答案
answers = generate_answers()

# 打印结果（每10个答案一行）
for i in range(0, 100, 10):
    print(f"题目{i+1:3}-{i+10:3}:", " ".join(answers[i:i+10]))