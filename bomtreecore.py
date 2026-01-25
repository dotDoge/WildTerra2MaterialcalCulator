import pandas as pd
from collections import defaultdict

class BOMTreeViewer:
    def __init__(self, file_path):
        self.recipe_map = self._load_recipes(file_path)

    def _load_recipes(self, file_path):
        """解析 Excel 配方表"""
        df = pd.read_excel(file_path)
        df['产物'] = df['产物'].astype(str).str.strip()
        df['原料'] = df['原料'].astype(str).str.strip()
        
        recipes = defaultdict(list)
        for _, row in df.dropna(subset=['产物', '原料']).iterrows():
            recipes[row['产物']].append({
                'ing': row['原料'],
                'consume': float(row['单次原料消耗数量']),
                'produce': float(row['单次产物数量'])
            })
        return recipes

    def show_tree(self, item, amount=1, level=0):
        """
        API 入口：递归打印树状结构
        :param item: 目标产物名称
        :param amount: 目标数量
        :param level: 当前层级（递归用）
        """
        indent = "      " * level
        # 格式化输出：[L层级] 物品名称 × 数量
        print(f"{indent}[L{level}] {item} × {amount:.2f}")

        if item in self.recipe_map:
            for recipe in self.recipe_map[item]:
                # 计算子材料需求量
                child_qty = (amount / recipe['produce']) * recipe['consume']
                # 递归打印
                self.show_tree(recipe['ing'], child_qty, level + 1)

# --- 使用示例 ---
if __name__ == "__main__":
    # 初始化
    viewer = BOMTreeViewer("材料统计.xlsx")
    
    target = "半木结构仓库"
    print(f"========== {target} 的合成树状图 ==========")
    viewer.show_tree(target, 1)