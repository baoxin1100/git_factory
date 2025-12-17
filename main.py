import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import pyautogui
import threading
import time
import os

class TemplateMatcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("模板匹配按键")
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 400
        window_height = 240
        # 计算窗口居中位置
        x = (screen_width - window_width) // 4 * 3
        y = (screen_height - window_height) // 2
        
        # 设置窗口位置和大小
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")        
        # 变量初始化
        self.screenshot_area = None
        self.templates = []
        self.template_folder = ""
        self.running = False
        
        # 创建UI
        self.shotscreen_btn = tk.Button(self.root, text="选择识别区域", command=self.select_area, font=("微软雅黑", 14))
        self.shotscreen_btn.pack(pady=5)
        tk.Button(self.root, text="加载模板", command=self.load_templates, font=("微软雅黑", 14)).pack(pady=5)
        self.start_btn = tk.Button(self.root, text="开始识别", command=self.toggle_recognition, font=("微软雅黑", 14))
        self.start_btn.pack(pady=5)

        self.root.mainloop()
    
    def select_area(self):
        from tkinter import Toplevel
        self.running = False
        self.start_btn.config(text="开始识别")
        self.selection_win = Toplevel(self.root)
        self.selection_win.attributes('-fullscreen', True)
        self.selection_win.attributes('-alpha', 0.3)
        
        self.canvas = tk.Canvas(self.selection_win, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.start_x = self.start_y = self.rect = None
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
    
    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
    def on_release(self, event):
        x1, y1, x2, y2 = self.canvas.coords(self.rect)
        self.screenshot_area = (int(min(x1, x2)), int(min(y1, y2)), 
                                int(abs(x2-x1)), int(abs(y2-y1)))
        self.selection_win.destroy()
        messagebox.showinfo("选择完成", f"区域已选择: {self.screenshot_area}")
        if self.templates:
            self.load_templates_when_shotscreen()
        self.shotscreen_btn.config(text="重新选择区域")

    def load_templates(self):
        self.template_folder = filedialog.askdirectory(title="选择模板文件夹")
        if self.template_folder:
            self.templates = []
            for file in os.listdir(self.template_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    img = cv2.imread(os.path.join(self.template_folder, file))
                    # 获取截图区域尺寸
                    _, _, region_width, region_height = self.screenshot_area
                    # 获取模板尺寸
                    template_height, template_width = img.shape[:2]
                    if img is not None:
                        if (template_width > region_width or template_height > region_height):
                            # 计算缩放比例
                            width_ratio = region_width / template_width
                            height_ratio = region_height / template_height
                            
                            # 使用较小的比例确保模板完全适合截图区域
                            scale_ratio = min(width_ratio, height_ratio, 1.0)  # 最大缩放比例为1（不放大）
                            
                            if scale_ratio < 1.0:
                                # 计算新尺寸
                                new_width = int(template_width * scale_ratio)
                                new_height = int(template_height * scale_ratio)
                                
                                # 缩放模板
                                img = cv2.resize(
                                    img, 
                                    (new_width, new_height), 
                                    interpolation=cv2.INTER_AREA
                                )
                        self.templates.append((file, img))
            print("加载完成" + f"已加载 {len(self.templates)} 个模板")

    def load_templates_when_shotscreen(self):
        if self.template_folder:
            self.templates = []
            for file in os.listdir(self.template_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    img = cv2.imread(os.path.join(self.template_folder, file))
                    # 获取截图区域尺寸
                    _, _, region_width, region_height = self.screenshot_area
                    # 获取模板尺寸
                    template_height, template_width = img.shape[:2]
                    if img is not None:
                        if (template_width > region_width or template_height > region_height):
                            # 计算缩放比例
                            width_ratio = region_width / template_width
                            height_ratio = region_height / template_height
                            
                            # 使用较小的比例确保模板完全适合截图区域
                            scale_ratio = min(width_ratio, height_ratio, 1.0)  # 最大缩放比例为1（不放大）
                            
                            if scale_ratio < 1.0:
                                # 计算新尺寸
                                new_width = int(template_width * scale_ratio)
                                new_height = int(template_height * scale_ratio)
                                
                                # 缩放模板
                                img = cv2.resize(
                                    img, 
                                    (new_width, new_height), 
                                    interpolation=cv2.INTER_AREA
                                )
                        self.templates.append((file, img))
            print("加载完成" + f"已加载 {len(self.templates)} 个模板")

    def toggle_recognition(self):
        if not self.screenshot_area:
            messagebox.showerror("错误", "请先选择识别区域")
            return
        if not self.templates:
            messagebox.showerror("错误", "请先加载模板")
            return
            
        self.running = not self.running
        if self.running:
            self.start_btn.config(text="停止识别")
            threading.Thread(target=self.recognition_loop, daemon=True).start()
        else:
            self.start_btn.config(text="开始识别")

    def start_spamming_a(self):
        """开始A键连发，持续4秒"""
        self.spamming_a = True
        self.spam_end_time = time.time() + 4  # 设置5秒后结束
        print(f"开始A键连发，持续4秒")
        self.spam_key_loop()
    
    def spam_key_loop(self):
        """A键连发循环"""
        while self.running and self.spamming_a:
            if self.spamming_a:
                # 检查是否超过6秒
                if time.time() > self.spam_end_time:
                    self.spamming_a = False
                    print("A键连发结束")
                else:
                    # 持续按A键
                    pyautogui.press('a')
                    time.sleep(0.05)  # 每50毫秒按一次，避免过快
            else:
                time.sleep(0.1)  # 减少CPU占用

    def press_key_with_focus(self, key):
        """带焦点控制的按键模拟"""
        try:
            # # 先激活目标窗口（通过点击截图区域）
            # if self.screenshot_area:
            #     x, y, w, h = self.screenshot_area
            #     pyautogui.click(x + w//2, y + h//2)
            #     # time.sleep(0.1)  # 等待窗口激活
            
            # 发送按键
            pyautogui.press(key)
            
            # 记录日志
            print(f"按键已发送: {key}")
            
        except Exception as e:
            print(f"按键失败: {e}")
    
    def recognition_loop(self):
        while self.running:
            try:
                screenshot = pyautogui.screenshot(region=self.screenshot_area)
                screen_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                best_match = None
                best_score = 0.1  # 最小匹配阈值
                
                # 查找最匹配的模板
                for filename, template in self.templates:
                    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, _, _ = cv2.minMaxLoc(result)
                    
                    if max_val > best_score:
                        best_score = max_val
                        best_match = filename
                
                # 如果有匹配的模板，执行按键操作
                if best_match:
                    print(f"最佳匹配: {best_match}, 分数: {best_score:.3f}")
                    if 'a4' in best_match.lower() and best_score > 0.7:
                        self.start_spamming_a()
                    elif 'a' in best_match.lower():
                        self.press_key_with_focus('a')
                    elif 'd' in best_match.lower():
                        self.press_key_with_focus('d')
                
                time.sleep(0.1)  # 检测间隔
            except Exception as e:
                print(f"识别错误: {e}")
                break

if __name__ == "__main__":
    # 添加调试信息
    print("程序启动...")
    TemplateMatcher()