# -*- coding: utf-8 -*-
"""
Created on Sat Mar 29 15:21:15 2025

@author: kunla1ve
"""

import re
from typing import Tuple, Union

def parse_dms(dms_str: str) -> float:
    """
    解析度分秒格式的经纬度字符串，返回十进制度数
    支持格式如：39°52'48" N, 116°24'20" E, 北纬 39.9042°等
    """
    # 预处理字符串
    dms_str = dms_str.strip().replace('′', "'").replace('″', '"')
    
    # 提取方向标识
    direction = 1
    if any(x in dms_str for x in ['S', 's', 'W', 'w', '南', '西']):
        direction = -1
    
    # 清除所有方向标识和无关字符
    dms_str = re.sub(r'[北南东西]纬|[东西南北]经|[NSEWnsew]|纬度|经度|lat|lon|:', '', dms_str, flags=re.IGNORECASE)
    dms_str = dms_str.strip(' °\'"')  # 去除首尾的特殊字符
    
    # 尝试解析度分秒格式
    match = re.match(r'(\d+)[°度](\d+)[\'′](\d+\.?\d*)[\"″]?', dms_str)
    if match:
        degrees, minutes, seconds = map(float, match.groups())
        decimal = degrees + minutes/60 + seconds/3600
        return decimal * direction
    
    # 尝试解析度分格式
    match = re.match(r'(\d+)[°度](\d+\.?\d*)[\'′]?', dms_str)
    if match:
        degrees, minutes = map(float, match.groups())
        decimal = degrees + minutes/60
        return decimal * direction
    
    # 尝试解析十进制格式
    try:
        number_str = re.search(r'[-+]?\d*\.?\d+', dms_str)
        if number_str:
            return float(number_str.group()) * direction
        else:
            raise ValueError("找不到有效的数字部分")
    except ValueError as e:
        raise ValueError(f"无法解析的经纬度格式: {dms_str}") from e

def decimal_to_dms(decimal: float, is_latitude: bool) -> Tuple[str, str]:
    """
    将十进制度数转换为度分秒格式
    返回: (中文格式, 英文格式)
    """
    # 确定方向
    if is_latitude:
        ch_dir = '北纬' if decimal >= 0 else '南纬'
        en_dir = 'N' if decimal >= 0 else 'S'
    else:
        ch_dir = '东经' if decimal >= 0 else '西经'
        en_dir = 'E' if decimal >= 0 else 'W'
    
    decimal = abs(decimal)
    degrees = int(decimal)
    minutes_float = (decimal - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60, 1)
    
    # 处理秒数为60的情况
    if seconds >= 60:
        seconds -= 60
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        degrees += 1
    
    # 构建格式字符串
    ch_format = f"{ch_dir}{degrees}°{minutes}′{seconds}″"
    en_format = f"{degrees}°{minutes}'{seconds}\" {en_dir}"
    
    return ch_format, en_format

def calculate_antipode(lat: float, lon: float) -> Tuple[Tuple[float, float], Tuple[str, str], Tuple[str, str]]:
    """
    计算对跖点坐标
    返回: 
    - 十进制坐标 (lat, lon)
    - 中文度分秒格式 (lat_str, lon_str)
    - 英文度分秒格式 (lat_str, lon_str)
    """
    # 计算对跖点
    antipode_lat = -lat
    antipode_lon = lon + 180 if lon <= 0 else lon - 180
    
    # 规范化经度到[-180,180]范围
    if antipode_lon > 180:
        antipode_lon -= 360
    elif antipode_lon <= -180:
        antipode_lon += 360
    
    # 转换为度分秒格式
    ch_lat, en_lat = decimal_to_dms(antipode_lat, True)
    ch_lon, en_lon = decimal_to_dms(antipode_lon, False)
    
    return (antipode_lat, antipode_lon), (ch_lat, ch_lon), (en_lat, en_lon)

def main():
    print("经纬度对跖点计算器，输入!退出程序")
    print("支持格式示例:")
    print("1. 39°52'48\" N, 116°24'20\" E")
    print("2. 22.311437, 114.2756289")
    print("3. 北纬 34°03′08″, 西经 118°14′37″")
    print("4. 北纬 34.0522°, 西经 118°14'37″","北纬 51°30'26″, 西经 0.1278°")

    while True:
        try:
            input_str = input("\n请输入经纬度（纬度在前，经度在后，用逗号分隔）: \n").strip()
            
            if input_str == "!":
                print("程序终止")
                break
            
            if not input_str:
                continue
            
            # 分割纬度和经度
            parts = [p.strip() for p in re.split(r'[,，]', input_str) if p.strip()]
            if len(parts) != 2:
                print("错误：请输入纬度和经度两个值，用逗号分隔")
                continue
            
            lat_str, lon_str = parts
            
            # 解析输入
            lat = parse_dms(lat_str)
            lon = parse_dms(lon_str)
            
            # 输出解析结果
            print(f"\n解析结果: {lat:.6f}, {lon:.6f}")
            
            # 计算对跖点
            (antipode_lat, antipode_lon), (ch_lat, ch_lon), (en_lat, en_lon) = calculate_antipode(lat, lon)
            
            # 输出结果
            print("计算结果:")
            print(f"十进制坐标: {antipode_lat:.6f}, {antipode_lon:.6f}")
            print(f"中文格式: {ch_lat}, {ch_lon}")
            print(f"英文格式: {en_lat}, {en_lon}")
            
        except ValueError as e:
            print(f"错误: {e}")
        except Exception as e:
            print(f"发生未知错误: {e}")

if __name__ == "__main__":
    main()