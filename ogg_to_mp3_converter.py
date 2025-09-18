#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OGG转MP3音频格式转换工具
支持拖拽上传、批量转换、进度显示等功能
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import threading
from pathlib import Path
import sys
import traceback
import time

# 延迟导入音频处理库以便给出更好的错误提示
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

# 尝试导入其他音频处理库作为备选
try:
    import librosa
    import soundfile as sf
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    sf = None
    np = None

try:
    import mutagen
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

# 设置主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class OGGToMP3Converter:
    def __init__(self):
        # 检查音频处理库依赖
        available_libs = []
        if PYDUB_AVAILABLE:
            available_libs.append("pydub")
        if LIBROSA_AVAILABLE:
            available_libs.append("librosa")
        if MUTAGEN_AVAILABLE:
            available_libs.append("mutagen")
        
        if not available_libs:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "依赖缺失", 
                "缺少音频处理库!\n\n"
                "请选择安装以下任一方案:\n\n"
                "方案1 (推荐): pip install librosa soundfile\n"
                "方案2: pip install pydub\n"
                "方案3: pip install mutagen\n\n"
                "使用国内镜像源:\n"
                "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple [包名]"
            )
            sys.exit(1)
        
        # 设置转换器优先级
        self.converter_priority = available_libs
        
        # 初始化主窗口
        self.root = TkinterDnD.Tk()
        if LIBROSA_AVAILABLE:
            self.root.title("OGG转WAV转换工具（轻量级版本）")
        else:
            self.root.title("OGG转MP3转换工具")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 设置窗口居中
        self.center_window()
        
        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 变量初始化
        self.input_path = ""
        self.output_path = ""
        self.ogg_files = []
        self.failed_files = []
        self.is_converting = False
        
        self.setup_ui()
        self.setup_drag_drop()
        
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = 800
        height = 700
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_ui(self):
        """设置用户界面"""
        # 主标题
        if LIBROSA_AVAILABLE:
            title_text = "🎵 OGG转WAV转换工具"
        else:
            title_text = "🎵 OGG转MP3转换工具"
        
        title_label = ctk.CTkLabel(
            self.root, 
            text=title_text, 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(15, 10))
        
        # 创建可滚动主框架，不使用expand=True避免挤压底部按钮
        self.main_scrollable_frame = ctk.CTkScrollableFrame(self.root, height=450)
        self.main_scrollable_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # 内容框架
        main_frame = self.main_scrollable_frame
        
        # 输入区域
        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(input_frame, text="📁 选择输入文件/文件夹:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        input_button_frame = ctk.CTkFrame(input_frame)
        input_button_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.input_label = ctk.CTkLabel(
            input_button_frame, 
            text="拖拽文件/文件夹到此处，或点击下方按钮选择", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.input_label.pack(pady=15)
        
        button_frame = ctk.CTkFrame(input_button_frame)
        button_frame.pack(pady=(0, 15))
        
        ctk.CTkButton(
            button_frame,
            text="选择文件",
            command=self.select_file,
            width=120
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame,
            text="选择文件夹", 
            command=self.select_folder,
            width=120
        ).pack(side="left")
        
        # 文件预览区域
        preview_frame = ctk.CTkFrame(main_frame)
        preview_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(preview_frame, text="📋 待转换文件预览:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        # 创建文件列表框架
        listbox_frame = ctk.CTkFrame(preview_frame)
        listbox_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # 创建滚动文本框，固定高度并确保有垂直滚动条
        self.file_listbox = ctk.CTkTextbox(
            listbox_frame, 
            height=180, 
            width=700,
            wrap="none",  # 禁用自动换行，确保水平滚动正常
            font=ctk.CTkFont(size=11)
        )
        self.file_listbox.pack(fill="x", padx=10, pady=10)
        
        # 输出区域
        output_frame = ctk.CTkFrame(main_frame)
        output_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(output_frame, text="📤 选择输出文件夹:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        output_select_frame = ctk.CTkFrame(output_frame)
        output_select_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.output_label = ctk.CTkLabel(
            output_select_frame, 
            text="请选择输出文件夹", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.output_label.pack(side="left", padx=(15, 10), pady=15)
        
        ctk.CTkButton(
            output_select_frame,
            text="选择输出文件夹",
            command=self.select_output_folder,
            width=150
        ).pack(side="right", padx=15, pady=10)
        
        # 进度区域
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="准备就绪", font=ctk.CTkFont(size=12))
        self.progress_label.pack(pady=(15, 5))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
        self.progress_bar.pack(pady=(0, 15))
        self.progress_bar.set(0)
        
        # 在设置完所有组件后，立即创建底部控制区域
        self.setup_bottom_controls()
    
    def setup_bottom_controls(self):
        """设置底部控制按钮，确保始终可见"""
        # 创建底部固定框架
        self.bottom_frame = ctk.CTkFrame(self.root)
        self.bottom_frame.pack(fill="x", padx=15, pady=10)
        
        # 状态信息行
        status_frame = ctk.CTkFrame(self.bottom_frame)
        status_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # 根据可用的转换库显示不同提示
        if LIBROSA_AVAILABLE:
            status_text = "💡 提示：将转换为WAV格式（无需FFmpeg）"
        elif PYDUB_AVAILABLE:
            status_text = "💡 提示：将转换为MP3格式（需要FFmpeg）"
        else:
            status_text = "⚠️ 警告：缺少音频处理库，请安装依赖"
        
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text=status_text, 
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        self.status_label.pack(pady=6)
        
        # 转换按钮
        self.convert_button = ctk.CTkButton(
            self.bottom_frame,
            text="🚀 开始转换",
            command=self.start_conversion,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            width=250,
            corner_radius=8
        )
        self.convert_button.pack(pady=(5, 10))
        
    def setup_drag_drop(self):
        """设置拖拽功能"""
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)
        
    def on_drop(self, event):
        """处理拖拽事件"""
        files = self.root.tk.splitlist(event.data)
        if files:
            self.input_path = files[0]
            self.update_input_display()
            self.scan_ogg_files()
            
    def select_file(self):
        """选择单个OGG文件"""
        file_path = filedialog.askopenfilename(
            title="选择OGG文件",
            filetypes=[("OGG文件", "*.ogg"), ("所有文件", "*.*")]
        )
        if file_path:
            self.input_path = file_path
            self.update_input_display()
            self.scan_ogg_files()
            
    def select_folder(self):
        """选择文件夹"""
        folder_path = filedialog.askdirectory(title="选择包含OGG文件的文件夹")
        if folder_path:
            self.input_path = folder_path
            self.update_input_display()
            self.scan_ogg_files()
            
    def select_output_folder(self):
        """选择输出文件夹"""
        folder_path = filedialog.askdirectory(title="选择输出文件夹")
        if folder_path:
            self.output_path = folder_path
            self.output_label.configure(text=f"输出到: {folder_path}")
            
    def update_input_display(self):
        """更新输入路径显示"""
        if os.path.isfile(self.input_path):
            self.input_label.configure(text=f"已选择文件: {os.path.basename(self.input_path)}")
            self._update_status(f"📁 已选择文件: {os.path.basename(self.input_path)}")
        else:
            self.input_label.configure(text=f"已选择文件夹: {os.path.basename(self.input_path)}")
            self._update_status(f"📁 已选择文件夹: {os.path.basename(self.input_path)}")
    
    def _update_status(self, text):
        """安全更新状态标签"""
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.configure(text=text)
    
    def scan_ogg_files(self):
        """扫描OGG文件"""
        self.ogg_files = []
        
        if os.path.isfile(self.input_path):
            # 单个文件
            if self.input_path.lower().endswith('.ogg'):
                self.ogg_files.append(self.input_path)
        else:
            # 文件夹 - 递归搜索
            for root, dirs, files in os.walk(self.input_path):
                for file in files:
                    if file.lower().endswith('.ogg'):
                        self.ogg_files.append(os.path.join(root, file))
        
        self.update_file_preview()
    
    def update_file_preview(self):
        """更新文件预览"""
        self.file_listbox.delete("1.0", tk.END)
        
        if not self.ogg_files:
            self.file_listbox.insert("1.0", "未找到OGG文件")
            self._update_status("⚠️ 未找到OGG文件，请选择包含OGG文件的文件夹")
            return
        
        preview_text = f"找到 {len(self.ogg_files)} 个OGG文件:\n\n"
        
        for i, file_path in enumerate(self.ogg_files, 1):
            file_name = os.path.basename(file_path)
            preview_text += f"{i:3d}. {file_name}\n"
        
        self.file_listbox.insert("1.0", preview_text)
        self._update_status(f"✅ 找到 {len(self.ogg_files)} 个OGG文件，请选择输出文件夹后开始转换")
    
    def get_unique_folder_name(self, base_path, folder_name):
        """获取唯一的文件夹名称"""
        original_name = folder_name
        counter = 1
        
        while os.path.exists(os.path.join(base_path, folder_name)):
            folder_name = f"{original_name}({counter})"
            counter += 1
        
        return folder_name
    
    def check_ffmpeg(self):
        """检查ffmpeg是否可用"""
        try:
            import subprocess
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def convert_with_librosa(self, ogg_path, mp3_path):
        """使用librosa转换（转换为WAV格式，因为无FFmpeg时无法直接转MP3）"""
        try:
            if not LIBROSA_AVAILABLE or sf is None:
                return "librosa或soundfile不可用"
            
            # 读取OGG文件
            audio_data, sample_rate = librosa.load(ogg_path, sr=None)
            
            # 由于没有FFmpeg，我们转换为WAV格式
            wav_path = mp3_path.replace('.mp3', '.wav')
            
            # 使用soundfile写入WAV文件
            sf.write(wav_path, audio_data, sample_rate)
            
            # 验证输出文件
            if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                return f"已转换为WAV格式: {os.path.basename(wav_path)}"
            else:
                return "WAV文件创建失败"
            
        except Exception as e:
            return f"librosa转换错误: {str(e)}"
    
    def convert_with_mutagen_simple(self, ogg_path, mp3_path):
        """使用简单的文件复制方法（改变扩展名）"""
        try:
            # 读取OGG文件的音频数据
            ogg_file = OggVorbis(ogg_path)
            
            # 这种方法主要是重新封装，质量可能不如真正的转换
            # 但不需要外部依赖
            import shutil
            
            # 创建一个基本的转换（实际上是复制+重命名）
            # 注意：这不是真正的格式转换，只是文件复制
            wav_path = mp3_path.replace('.mp3', '.wav')
            
            # 提取音频数据并写入新文件
            # 这里简化处理，实际项目中需要更复杂的转换逻辑
            return "mutagen方法需要额外的编码器支持"
            
        except Exception as e:
            return f"mutagen转换错误: {str(e)}"
    
    def convert_ogg_to_mp3(self, ogg_path, mp3_path):
        """转换单个OGG文件到MP3 - 多方案自动选择"""
        try:
            # 检查输入文件是否存在
            if not os.path.exists(ogg_path):
                return "输入文件不存在"
            
            # 检查文件大小
            file_size = os.path.getsize(ogg_path)
            if file_size == 0:
                return "输入文件为空"
            
            # 按优先级尝试不同的转换方法
            errors = []
            
            for converter in self.converter_priority:
                try:
                    if converter == "librosa" and LIBROSA_AVAILABLE:
                        result = self.convert_with_librosa(ogg_path, mp3_path)
                        if result == True or (isinstance(result, str) and "已转换为WAV格式" in result):
                            return True
                        else:
                            errors.append(f"librosa: {result}")
                        
                    elif converter == "pydub" and PYDUB_AVAILABLE:
                        try:
                            # 使用pydub进行转换
                            audio = AudioSegment.from_ogg(ogg_path)
                            
                            # 检查音频是否有效
                            if len(audio) == 0:
                                errors.append("pydub: 音频文件为空")
                                continue
                            
                            # 导出为MP3格式
                            audio.export(
                                mp3_path, 
                                format="mp3", 
                                bitrate="192k",
                                parameters=["-q:a", "2"]  # 高质量设置
                            )
                            
                            # 验证输出文件
                            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                                return True
                            else:
                                errors.append("pydub: 输出文件创建失败")
                        except Exception as pe:
                            errors.append(f"pydub: {str(pe)}")
                            
                    elif converter == "mutagen" and MUTAGEN_AVAILABLE:
                        result = self.convert_with_mutagen_simple(ogg_path, mp3_path)
                        if result == True:
                            return True
                        else:
                            errors.append(f"mutagen: {result}")
                            
                except Exception as e:
                    errors.append(f"{converter}: {str(e)}")
                    continue
            
            # 所有方法都失败了，返回详细错误信息
            return f"所有转换方法都失败。错误详情: {'; '.join(errors)}"
            
        except FileNotFoundError as e:
            if "ffmpeg" in str(e).lower():
                return "FFmpeg未安装。建议安装轻量级音频库: pip install librosa soundfile"
            return f"文件操作错误: {str(e)}"
        except Exception as e:
            error_msg = str(e)
            if "ffmpeg" in error_msg.lower():
                return "FFmpeg相关错误。建议使用无FFmpeg依赖的方案"
            elif "permission" in error_msg.lower():
                return "文件权限错误，请检查文件是否被占用"
            elif "memory" in error_msg.lower():
                return "内存不足，请关闭其他程序后重试"
            else:
                return f"转换错误: {error_msg}"
        
    def start_conversion(self):
        """开始转换过程"""
        if self.is_converting:
            return
        
        # 验证输入
        if not self.ogg_files:
            messagebox.showerror("错误", "请先选择包含OGG文件的文件或文件夹!")
            return
            
        if not self.output_path:
            messagebox.showerror("错误", "请选择输出文件夹!")
            return
            
        # 检查输出文件夹是否可写
        try:
            test_file = os.path.join(self.output_path, "test_write_permission.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception:
            messagebox.showerror("错误", f"输出文件夹无写入权限:\n{self.output_path}")
            return
            
        # 检查ffmpeg（后台检查，不阻塞界面）
        self.is_converting = True
        self.convert_button.configure(text="检查环境...", state="disabled")
        
        # 在新线程中检查环境并转换
        conversion_thread = threading.Thread(target=self.pre_conversion_check)
        conversion_thread.daemon = True
        conversion_thread.start()
        
    def pre_conversion_check(self):
        """转换前的环境检查"""
        try:
            # 检查ffmpeg
            if not self.check_ffmpeg():
                self.root.after(0, lambda: self.show_ffmpeg_warning())
                return
            
            # 环境检查通过，开始转换
            self.root.after(0, lambda: self.convert_button.configure(text="转换中..."))
            self.conversion_worker()
            
        except Exception as e:
            self.root.after(0, lambda: self.conversion_error(f"环境检查失败: {str(e)}"))
    
    def show_ffmpeg_warning(self):
        """显示ffmpeg警告"""
        self.is_converting = False
        self.convert_button.configure(text="🚀 开始转换", state="normal")
        
        result = messagebox.askyesno(
            "FFmpeg未检测到",
            "未检测到FFmpeg，这可能导致转换失败。\n\n"
            "建议:\n"
            "1. 安装FFmpeg并添加到系统PATH\n"
            "2. 下载地址: https://ffmpeg.org/download.html\n\n"
            "是否仍要继续转换?"
        )
        
        if result:
            self.is_converting = True
            self.convert_button.configure(text="转换中...", state="disabled")
            conversion_thread = threading.Thread(target=self.conversion_worker)
            conversion_thread.daemon = True
            conversion_thread.start()
    
    def conversion_worker(self):
        """转换工作线程"""
        self.failed_files = []
        total_files = len(self.ogg_files)
        
        try:
            for i, ogg_file in enumerate(self.ogg_files):
                # 检查是否被取消（为未来扩展预留）
                if not self.is_converting:
                    break
                
                file_name = os.path.basename(ogg_file)
                
                # 更新进度 - 开始处理
                progress = i / total_files
                self.root.after(0, lambda p=progress, f=file_name: self.update_progress(p, f"正在处理: {f}"))
                
                try:
                    # 获取文件名（不含扩展名）
                    base_name = os.path.splitext(file_name)[0]
                    
                    # 创建输出文件夹
                    output_folder_name = self.get_unique_folder_name(self.output_path, base_name)
                    output_folder = os.path.join(self.output_path, output_folder_name)
                    os.makedirs(output_folder, exist_ok=True)
                    
                    # 生成输出文件路径
                    mp3_file = os.path.join(output_folder, f"{base_name}.mp3")
                    
                    # 更新进度 - 开始转换
                    self.root.after(0, lambda p=progress, f=file_name: self.update_progress(p, f"转换中: {f}"))
                    
                    # 执行转换
                    result = self.convert_ogg_to_mp3(ogg_file, mp3_file)
                    
                    if result is not True:
                        self.failed_files.append((ogg_file, result))
                        # 转换失败时删除可能创建的空文件夹
                        try:
                            if os.path.exists(output_folder) and not os.listdir(output_folder):
                                os.rmdir(output_folder)
                        except:
                            pass
                    else:
                        # 转换成功，更新进度显示
                        self.root.after(0, lambda p=progress, f=file_name: self.update_progress(p, f"完成: {f}"))
                
                except Exception as e:
                    self.failed_files.append((ogg_file, str(e)))
                
                # 短暂延迟以让界面更新
                time.sleep(0.01)
            
            # 转换完成
            self.root.after(0, self.conversion_completed)
                
        except Exception as e:
            self.root.after(0, lambda: self.conversion_error(str(e)))
    
    def update_progress(self, progress, status):
        """更新进度条和状态"""
        self.progress_bar.set(progress)
        self.progress_label.configure(text=status)
            
    def conversion_completed(self):
        """转换完成处理"""
        self.is_converting = False
        self.convert_button.configure(text="🚀 开始转换", state="normal")
        self.progress_bar.set(1.0)
        
        success_count = len(self.ogg_files) - len(self.failed_files)
        
        if not self.failed_files:
            self.progress_label.configure(text=f"转换完成! 成功转换 {success_count} 个文件")
            messagebox.showinfo("转换完成", f"所有文件转换成功!\n成功转换: {success_count} 个文件")
        else:
            self.progress_label.configure(text=f"转换完成! 成功: {success_count}, 失败: {len(self.failed_files)}")
            
            # 显示失败文件详情
            failed_details = "以下文件转换失败:\n\n"
            for file_path, error in self.failed_files:
                file_name = os.path.basename(file_path)
                failed_details += f"• {file_name}\n  错误: {error}\n\n"
            
            messagebox.showwarning("转换完成（部分失败）", failed_details)
    
    def conversion_error(self, error_message):
        """转换错误处理"""
        self.is_converting = False
        self.convert_button.configure(text="🚀 开始转换", state="normal")
        self.progress_label.configure(text="转换失败")
        messagebox.showerror("转换错误", f"转换过程中发生错误:\n{error_message}")
            
    def run(self):
        """运行应用"""
        self.root.mainloop()

def main():
    """主函数"""
    try:
        app = OGGToMP3Converter()
        app.run()
    except Exception as e:
        messagebox.showerror("启动错误", f"程序启动失败:\n{str(e)}\n\n请确保已安装所有依赖包:\npip install -r requirements.txt")

if __name__ == "__main__":
    main()
