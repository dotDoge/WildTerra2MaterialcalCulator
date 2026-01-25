import pandas as pd
from collections import defaultdict

class BOMCalculator:
    def __init__(self, file_path):
        self.recipe_map = self._load_recipes(file_path)

    def _load_recipes(self, file_path):
        """解析 Excel 配方表"""
        df = pd.read_excel(file_path)
        # 统一清理空格，确保名称匹配准确
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

    def calculate(self, target_item, amount, inventory):
        """
        API 入口：计算给定物品在考虑库存后的基础材料缺口
        :param target_item: 目标产物名称
        :param amount: 目标数量
        :param inventory: 当前库存 dict, 如 {"铁锭": 100}
        :return: 基础材料缺口 dict, 消耗后的剩余库存 dict
        """
        # 复制一份库存，避免直接修改原始输入
        current_inv = inventory.copy()
        deficits = defaultdict(float)
        
        # 执行递归逻辑
        self._recursive_calc(target_item, amount, current_inv, deficits)
        
        return dict(deficits), current_inv

    def _recursive_calc(self, item, amount, inv, deficits):
        # 1. 优先消耗库存
        have = inv.get(item, 0)
        if have > 0:
            used = min(have, amount)
            inv[item] -= used
            amount -= used

        # 2. 如果需求已满足，停止
        if amount <= 0:
            return

        # 3. 如果有配方，拆解到下一层
        if item in self.recipe_map:
            for recipe in self.recipe_map[item]:
                # 核心公式：所需原料 = (当前缺口 / 产出倍率) * 消耗倍率
                needed_qty = (amount / recipe['produce']) * recipe['consume']
                self._recursive_calc(recipe['ing'], needed_qty, inv, deficits)
        else:
            # 4. 没配方，说明是基础原料，记录总缺口
            deficits[item] += amount

# --- 使用示例 ---
if __name__ == "__main__":
    calc = BOMCalculator("材料统计.xlsx")
    
    # 模拟输入
    my_inv = {"铁锭": 100, "青铜锭": 200}
    target = "半木结构仓库"
    count = 1

    # 调用 API
    needed, remaining_inv = calc.calculate(target, count, my_inv)

    print(f"目标: {target} x {count}")
    print("-" * 30)
    print("需要补充的基础材料:")
    for m, q in needed.items():
        print(f"  {m}: {q:.2f}")
    
    print("\n消耗后的剩余库存 (部分):")
    for m, q in remaining_inv.items():
        if q != my_inv.get(m): # 只显示有变化的
            print(f"  {m}: {q:.2f}")