# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 16:43:58 2026

@author: hongl
"""


import random
import string

def generate_password(length=10):
    """
    生成随机密码
    
    参数:
        length: 密码长度，默认10个字符
    返回:
        符合要求的随机密码
    """
    # 定义字符集
    lowercase = string.ascii_lowercase  # 小写字母
    uppercase = string.ascii_uppercase  # 大写字母
    digits = string.digits  # 数字
    # 修正特殊字符集（去掉空格，避免生成问题）
    special_chars = '!#$%&()*+-./:;<=>?@[]^_{|}~'  # 特殊字符
    
    all_chars = lowercase + uppercase + digits + special_chars
    
    # 确保密码长度至少为4（因为需要包含4种类型各一个）
    if length < 4:
        raise ValueError("密码长度至少为4个字符")
    
    while True:
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

# 使用示例
if __name__ == "__main__":
    # 默认10位密码
    password = generate_password(10)  # 使用默认长度10
    print("生成的随机密码是:", password)
    print(f"密码长度: {len(password)}")
