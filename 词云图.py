# -*- coding: utf-8 -*-
"""
Created on Mon Mar 10 15:10:43 2025

@author: kunla1ve
"""


import fitz  # PyMuPDF
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# 打开PDF文件
pdf_path = r"D:\BFM-44094\semester2\International Operations Management\w8\OMS-20-670-CE.pdf"
document = fitz.open(pdf_path)

# 提取PDF中的文本
text = ""
for page_num in range(document.page_count):
    page = document.load_page(page_num)
    text += page.get_text()

# 使用jieba进行分词
words = jieba.lcut(text)

# 将分词结果合并成字符串，空格分隔
word_string = ' '.join(words)

# 生成词云
wordcloud = WordCloud(font_path='simhei.ttf',  # 指定字体路径以显示中文
                      width=800, 
                      height=400, 
                      background_color='white').generate(word_string)

# 显示词云图
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')  # 关闭坐标轴
plt.show()