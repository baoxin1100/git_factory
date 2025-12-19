import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import pyautogui
import threading
import time
import os
from PIL import Image

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
        
        # 红框相关变量
        self.overlay_window = None
        self.overlay_rect = None
        self.overlay_label = None
        
        # 创建按钮框架（第一行：区域选择相关按钮）
        area_frame = tk.Frame(self.root)
        area_frame.pack(pady=5)
        # 创建UI
        self.shotscreen_btn = tk.Button(area_frame, text="选择识别区域", command=self.select_area, font=("微软雅黑", 14))
        self.shotscreen_btn.pack(side=tk.LEFT, padx=(0, 10))
        # 使用默认识别区域按钮
        self.default_area_btn = tk.Button(
            area_frame,
            text="使用默认区域",
            command=self.use_default_area,
            font=("微软雅黑", 14)
        )
        self.default_area_btn.pack(side=tk.LEFT)
        
        tk.Button(self.root, text="加载模板", command=self.load_templates, font=("微软雅黑", 14)).pack(pady=5)
        self.start_btn = tk.Button(self.root, text="开始识别", command=self.toggle_recognition, font=("微软雅黑", 14))
        self.start_btn.pack(pady=5)

        self.root.mainloop()
    
    def show_area_overlay(self):
        """显示红框覆盖层"""
        # 如果已经有红框窗口，先关闭
        if self.overlay_window:
            try:
                self.overlay_window.destroy()
            except:
                pass
        
        if not self.screenshot_area:
            return
        
        x, y, w, h = self.screenshot_area
        
        # 创建仅覆盖红框区域的窗口，而不是全屏
        self.overlay_window = tk.Toplevel(self.root)
        
        # 设置窗口位置和大小（仅覆盖红框区域）
        self.overlay_window.geometry(f"{w+6}x{h+6}+{x-3}+{y-3}")  # +6和-3是为了留出边框空间
        
        # 关键设置：无边框、透明、置顶但允许其他窗口激活
        self.overlay_window.overrideredirect(True)      # 无边框
        self.overlay_window.attributes('-topmost', True) # 置顶，但在红框区域外可以点击其他窗口
        self.overlay_window.attributes('-transparentcolor', 'black')  # 黑色透明
        
        # 设置窗口为工具窗口（减少干扰）
        self.overlay_window.attributes('-toolwindow', True)
        
        # 允许穿透点击（关键！）
        self.overlay_window.attributes('-disabled', True)  # 窗口本身不接受输入
        self.overlay_window.attributes('-alpha', 0.7)      # 70%透明度
        
        canvas = tk.Canvas(self.overlay_window, bg='black', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绘制红框（内缩3像素，避免被窗口边框遮挡）
        self.overlay_rect = canvas.create_rectangle(
            3, 3, w+3, h+3,  # 内缩3像素
            outline='red', width=3
        )
        
        print(f"显示红框: {self.screenshot_area}")
    
    def update_area_overlay(self):
        """更新红框位置（重新显示）"""
        self.show_area_overlay()
    
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

        # 添加提示文字
        self.canvas.create_text(
            self.selection_win.winfo_screenwidth() // 2,
            100,
            text="拖动鼠标选择区域，完成后按ESC退出",
            font=("微软雅黑", 16),
            fill='white'
        )

    def use_default_area(self):
        # 获取窗口截图
        try:
            self.running = False
            self.start_btn.config(text="开始识别")
            window = pyautogui.getWindowsWithTitle('胜利女神：新的希望')[0]  # 根据窗口标题获取
            window.activate()  # 激活窗口（可选）
            nx = 0.5
            ny = 0.6
            nh = 391/1414
            wh = 339/391 
            regionh = int(window.box.height * nh)
            regionw = int(regionh * wh)
            regionx = window.box.width // 2 - regionw//2 + window.box.left
            reriony = int(window.box.height * ny) - regionh//2 + window.box.top
            self.screenshot_area = (regionx, reriony, 
                               regionw, regionh)
            messagebox.showinfo("选择完成", f"区域已选择: {self.screenshot_area}")
            self.shotscreen_btn.config(text="重新选择区域")
            if self.templates:
                self.load_templates_when_shotscreen()
            # 显示红框
            self.show_area_overlay()
            
        except Exception:
            messagebox.showerror("错误", "请先打开胜利女神")
        
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
        
        # 显示红框
        self.show_area_overlay()

    def load_templates(self):
        if not self.screenshot_area:
            messagebox.showerror("错误", "请先选择识别区域")
            return
        self.template_folder = filedialog.askdirectory(title="选择模板文件夹")
        if self.template_folder:
            self.templates = []
            for file in os.listdir(self.template_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    pil_img = Image.open(os.path.join(self.template_folder, file))
                
                    # 转换为OpenCV格式 (BGR)
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
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
            messagebox.showinfo("加载完成", f"已加载 {len(self.templates)} 个模板")

    def load_templates_when_shotscreen(self):
        if self.template_folder:
            self.templates = []
            for file in os.listdir(self.template_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    pil_img = Image.open(os.path.join(self.template_folder, file))
                    # 转换为OpenCV格式 (BGR)
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
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
            try:
                window = pyautogui.getWindowsWithTitle('胜利女神：新的希望')[0]  # 根据窗口标题获取
                window.activate()  # 激活窗口（可选）
            except:
                pass
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