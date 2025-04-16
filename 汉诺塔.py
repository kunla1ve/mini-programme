# -*- coding: utf-8 -*-
"""
Created on Fri Mar 14 16:50:06 2025

@author: kunla1ve
"""


def iterative_hanoi(n, source, target, auxiliary):
    # 总共需要的移动次数
    total_moves = 2**n - 1

    # 如果圆盘数是偶数，交换目标柱子和辅助柱子
    if n % 2 == 0:
        target, auxiliary = auxiliary, target

    # 初始化三个柱子
    rods = {source: list(range(n, 0, -1)), target: [], auxiliary: []}

    for move in range(1, total_moves + 1):
        if move % 3 == 1:
            # 从 source 到 target
            move_disk(rods, source, target)
        elif move % 3 == 2:
            # 从 source 到 auxiliary
            move_disk(rods, source, auxiliary)
        elif move % 3 == 0:
            # 从 auxiliary 到 target
            move_disk(rods, auxiliary, target)

def move_disk(rods, from_rod, to_rod):
    if not rods[from_rod]:
        # 如果 from_rod 为空，则从 to_rod 移动到 from_rod
        disk = rods[to_rod].pop()
        rods[from_rod].append(disk)
        print(f"Move disk {disk} from {to_rod} to {from_rod}")
    elif not rods[to_rod]:
        # 如果 to_rod 为空，则从 from_rod 移动到 to_rod
        disk = rods[from_rod].pop()
        rods[to_rod].append(disk)
        print(f"Move disk {disk} from {from_rod} to {to_rod}")
    elif rods[from_rod][-1] < rods[to_rod][-1]:
        # 如果 from_rod 的顶部圆盘小于 to_rod 的顶部圆盘，则移动 from_rod 到 to_rod
        disk = rods[from_rod].pop()
        rods[to_rod].append(disk)
        print(f"Move disk {disk} from {from_rod} to {to_rod}")
    else:
        # 否则，移动 to_rod 到 from_rod
        disk = rods[to_rod].pop()
        rods[from_rod].append(disk)
        print(f"Move disk {disk} from {to_rod} to {from_rod}")

# 假设有 3 个圆盘，A 是起始柱子，C 是目标柱子，B 是辅助柱子
iterative_hanoi(4, 'A', 'C', 'B')