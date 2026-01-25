import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from bomcore import BOMCalculator
from bomtreecore import BOMTreeViewer
import sys
import os

class TextRedirector:
    def __init__(self, widget):
        self.widget = widget
    def write(self, str_val):
        self.widget.config(state=tk.NORMAL)
        self.widget.insert(tk.END, str_val)
        self.widget.see(tk.END)
        self.widget.config(state=tk.DISABLED)
    def flush(self):
        pass

class BOMApp:
    def __init__(self, master):
        self.master = master
        master.title("WildTerra2材料计算器")
        
        try:
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))

            # 拼接 Excel 路径
            excel_file = os.path.join(application_path, "bom.xlsx")
            self.calculator = BOMCalculator(excel_file)
            self.tree_viewer = BOMTreeViewer(excel_file)
        except Exception as e:
            messagebox.showerror("文件错误", f"无法加载数据: {e}")

        self.inventory_rows = []
        self.create_widgets()

    def create_widgets(self):
        # --- 顶部：目标设置 ---
        top_frame = tk.LabelFrame(self.master, text=" 目标设置 ", padx=10, pady=10)
        top_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(top_frame, text="产物名称:").grid(row=0, column=0, padx=5)
        self.item_entry = tk.Entry(top_frame, width=25)
        self.item_entry.grid(row=0, column=1, padx=5)
        self.item_entry.insert(0, "半木结构仓库")

        tk.Label(top_frame, text="数量:").grid(row=0, column=2, padx=5)
        self.qty_entry = tk.Entry(top_frame, width=8)
        self.qty_entry.grid(row=0, column=3, padx=5)
        self.qty_entry.insert(0, "1")

        # --- 中部：库存动态列表 ---
        inv_frame = tk.LabelFrame(self.master, text=" 当前库存 ", padx=10, pady=10)
        inv_frame.pack(fill="x", padx=10, pady=5)

        self.canvas = tk.Canvas(inv_frame, height=120)
        self.inv_scrollbar = ttk.Scrollbar(inv_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.inv_scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inv_scrollbar.pack(side="right", fill="y")

        self.add_inventory_row("铁锭", 10)
        self.add_inventory_row("青铜锭", 20)

        btn_bar = tk.Frame(self.master)
        btn_bar.pack(fill="x", padx=10)
        tk.Button(btn_bar, text="+ 添加新物品", command=lambda: self.add_inventory_row()).pack(side="left", padx=5)
        tk.Button(btn_bar, text="🚀 运行计算", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.perform_calculation).pack(side="right", padx=5)

        # --- 底部：输出区域 ---
        out_frame = tk.Frame(self.master)
        out_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 严格分配权重：左侧合成树(0)权重为 2，右侧清单(1)权重为 1
        out_frame.columnconfigure(0, weight=2)
        out_frame.columnconfigure(1, weight=1)
        out_frame.rowconfigure(1, weight=1) # 确保第二行（文本框行）可以纵向拉伸

        # 1. 左侧合成树视图
        tk.Label(out_frame, text="合成树视图:").grid(row=0, column=0, sticky="w")
        tree_container = tk.Frame(out_frame)
        tree_container.grid(row=1, column=0, sticky="nsew", padx=5)
        
        # 将 width 设小一点（比如 40），让 weight 来决定最终宽度
        self.tree_output = tk.Text(tree_container, font=("Consolas", 9), bg="#f0f0f0", 
                                   state=tk.DISABLED, wrap="none", height=20, width=40)
        h_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree_output.xview)
        v_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree_output.yview)
        self.tree_output.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.tree_output.pack(side="left", fill="both", expand=True)

        # 2. 右侧基础材料清单
        tk.Label(out_frame, text="基础材料清单:").grid(row=0, column=1, sticky="w")
        list_container = tk.Frame(out_frame)
        list_container.grid(row=1, column=1, sticky="nsew", padx=5)
        
        # 这里的 width 设为左侧的一半左右（比如 20）
        self.materials_output = scrolledtext.ScrolledText(list_container, font=("Consolas", 10), 
                                                          bg="#f0f0f0", state=tk.DISABLED, 
                                                          height=20, width=20)
        self.materials_output.pack(fill="both", expand=True)
    def add_inventory_row(self, name="", qty=""):
        row_frame = tk.Frame(self.scrollable_frame)
        row_frame.pack(fill="x", pady=2)
        name_ent = tk.Entry(row_frame, width=20)
        name_ent.insert(0, name)
        name_ent.pack(side="left", padx=2)
        qty_ent = tk.Entry(row_frame, width=10)
        qty_ent.insert(0, str(qty))
        qty_ent.pack(side="left", padx=2)
        tk.Button(row_frame, text="✖", fg="red", command=lambda: self.remove_row(row_frame)).pack(side="left", padx=5)
        self.inventory_rows.append({"frame": row_frame, "name": name_ent, "qty": qty_ent})

    def remove_row(self, frame):
        for i, row in enumerate(self.inventory_rows):
            if row["frame"] == frame:
                row["frame"].destroy()
                self.inventory_rows.pop(i)
                break

    def perform_calculation(self):
        for widget in [self.tree_output, self.materials_output]:
            widget.config(state=tk.NORMAL)
            widget.delete(1.0, tk.END)

        item = self.item_entry.get().strip()
        try:
            qty = float(self.qty_entry.get())
        except:
            messagebox.showerror("错误", "数量请输入数字")
            return

        current_inv = {}
        for row in self.inventory_rows:
            n = row["name"].get().strip()
            v = row["qty"].get().strip()
            if n:
                try: current_inv[n] = float(v) if v else 0.0
                except: continue

        old_stdout = sys.stdout
        sys.stdout = TextRedirector(self.tree_output)
        try:
            self.tree_viewer.show_tree(item, 1)
        except Exception as e:
            print(f"解析失败: {e}")
        finally:
            sys.stdout = old_stdout

        try:
            needed, _ = self.calculator.calculate(item, qty, current_inv)
            self.materials_output.config(state=tk.NORMAL)
            if not needed:
                self.materials_output.insert(tk.END, "✅ 库存完全覆盖。")
            else:
                for m, q in needed.items():
                    self.materials_output.insert(tk.END, f"• {m}: {q:.2f}\n")
        except Exception as e:
            self.materials_output.insert(tk.END, f"计算出错: {e}")
        
        self.tree_output.config(state=tk.DISABLED)
        self.materials_output.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    app = BOMApp(root)
    root.mainloop()