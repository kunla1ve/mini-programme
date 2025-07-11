# -*- coding: utf-8 -*-
"""
Created on Fri Mar 14 16:19:00 2025

@author: kunla1ve
"""

# import re

# def check_password(password):
#     # 检查密码长度
#     if len(password) < 8 or len(password) > 12:
#         return "不符合"
#     # 使用正则表达式检查各种字符类型
#     if not re.search(r'[A-Z]', password):
#         return "不符合"
#     if not re.search(r'[a-z]', password):
#         return "不符合"
#     if not re.search(r'[0-9]', password):
#         return "不符合"
#     if not re.search(r'\W', password):  # \W 匹配任何非字母数字字符
#         return "不符合"
#     # 如果所有条件都满足
#     return "符合"

# # 测试
# password = input("请输入密码: ")
# result = check_password(password)
# print(result)

import random
import string

def generate_password():
    # 定义字符集
    lowercase = string.ascii_lowercase  # 小写字母
    uppercase = string.ascii_uppercase  # 大写字母
    digits = string.digits  # 数字
    special_chars = '!#$%&()*+,-./:;<=>?@[\\]_`{|}~'  # 特殊字符
    
    all_chars = lowercase + uppercase + digits + special_chars
    
    while True:
        # 随机确定密码长度(7-12)
        length = random.randint(7, 12)
        
        # 确保每种类型至少有一个字符
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special_chars)
        ]
        
        # 填充剩余字符
        for _ in range(length - 4):
            password.append(random.choice(all_chars))
        
        # 打乱顺序
        random.shuffle(password)
        password = ''.join(password)
        
        # 检查是否有超过2个连续相同字符
        valid = True
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                valid = False
                break
        
        if valid:
            return password

# 生成并打印密码
password = generate_password()
print("生成的随机密码是:", password)
print(f"密码长度: {len(password)}")