# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 22:53:33 2025

@author: kunla1ve
"""

import math


def nth_prime_optimized(n):
    if n < 1:
        raise ValueError("n必须为正整数")
    if n == 1:
        return 2
    
    # 根据素数定理估算上限
    if n < 6:
        limit = 15
    else:
        limit = int(n * (math.log(n) + math.log(math.log(n)))) + 1
    
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for current in range(2, int(limit**0.5) + 1):
        if sieve[current]:
            sieve[current*current :: current] = [False] * len(sieve[current*current :: current])
    
    primes = [i for i, is_prime in enumerate(sieve) if is_prime]
    return primes[n-1]


nth_prime_optimized(1000)