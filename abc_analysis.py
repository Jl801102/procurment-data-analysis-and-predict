import pandas as pd

def abc_by_category(df, group_col, amount_col, thresholds=(70, 90)):
    """
    按类别进行ABC分类
    thresholds: (A类累计占比上限, B类累计占比上限) 例如 (70, 90)
    """
    if group_col not in df.columns or amount_col not in df.columns:
        return None
    cat_spend = df.groupby(group_col)[amount_col].sum().reset_index()
    cat_spend = cat_spend.sort_values(amount_col, ascending=False).reset_index(drop=True)
    cat_spend['累计占比'] = cat_spend[amount_col].cumsum() / cat_spend[amount_col].sum() * 100

    def assign_abc(cum):
        if cum <= thresholds[0]:
            return 'A类 (70%)'
        elif cum <= thresholds[1]:
            return 'B类 (20%)'
        else:
            return 'C类 (10%)'
    cat_spend['ABC分类'] = cat_spend['累计占比'].apply(assign_abc)

    # 格式化金额
    cat_spend[amount_col] = cat_spend[amount_col].round(2)
    cat_spend['累计占比'] = cat_spend['累计占比'].round(2)
    return cat_spend[[group_col, amount_col, '累计占比', 'ABC分类']]
def abc_by_material(df, material_col, amount_col, thresholds=(70, 90)):
    """
    按物料进行ABC分类
    df: 原始数据DataFrame
    material_col: 物料名称列
    amount_col: 金额列
    thresholds: (A类累计占比上限, B类累计占比上限) 例如 (70, 90)
    返回：DataFrame 包含物料名称、采购额、累计占比、ABC分类
    """
    # 按物料汇总采购额
    mat_sum = df.groupby(material_col)[amount_col].sum().reset_index()
    mat_sum = mat_sum.sort_values(amount_col, ascending=False).reset_index(drop=True)
    total = mat_sum[amount_col].sum()
    mat_sum['累计占比'] = mat_sum[amount_col].cumsum() / total * 100

    def assign_abc(cum):
        if cum <= thresholds[0]:
            return 'A类 (70%)'
        elif cum <= thresholds[1]:
            return 'B类 (20%)'
        else:
            return 'C类 (10%)'

    mat_sum['ABC分类'] = mat_sum['累计占比'].apply(assign_abc)
    mat_sum['累计占比'] = mat_sum['累计占比'].round(2)
    return mat_sum[[material_col, amount_col, '累计占比', 'ABC分类']]