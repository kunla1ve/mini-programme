# -*- coding: utf-8 -*-
"""
Created on Sun Mar 16 15:55:56 2025

@author: kunla1ve
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from docx import Document

def save_to_docx():
    text = text_area.get("1.0", tk.END).strip()  # 获取文本框中的内容
    if not text:
        messagebox.showwarning("警告", "请输入文本内容！")
        return
    
    # 弹出文件保存对话框
    file_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word 文件", "*.docx")])
    
    if file_path:
        try:
            doc = Document()
            doc.add_paragraph(text)  # 将文本添加到Word文档中
            doc.save(file_path)  # 保存文档
            messagebox.showinfo("成功", "文件保存成功！")
        except Exception as e:
            messagebox.showerror("错误", f"保存文件时出错: {e}")

# 创建主窗口
root = tk.Tk()
root.title("Convert Text to DOCX")

# 创建文本框
text_area = tk.Text(root, wrap=tk.WORD, width=60, height=20)
text_area.pack(padx=10, pady=10)

# 创建保存按钮
save_button = tk.Button(root, text="保存为DOCX", command=save_to_docx)
save_button.pack(pady=10)

# 运行主循环
root.mainloop()