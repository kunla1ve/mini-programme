# -*- coding: utf-8 -*-
"""
Created on Fri Mar 14 16:19:00 2025

@author: kunla1ve
"""

import re

def check_password(password):
    # 检查密码长度
    if len(password) < 8 or len(password) > 12:
        return "不符合"
    # 使用正则表达式检查各种字符类型
    if not re.search(r'[A-Z]', password):
        return "不符合"
    if not re.search(r'[a-z]', password):
        return "不符合"
    if not re.search(r'[0-9]', password):
        return "不符合"
    if not re.search(r'\W', password):  # \W 匹配任何非字母数字字符
        return "不符合"
    # 如果所有条件都满足
    return "符合"

# 测试
password = input("请输入密码: ")
result = check_password(password)
print(result)

