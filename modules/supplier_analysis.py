import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def assign_geo_risk(supplier):
    """模拟地理风险评分（0-2），数值越大风险越高"""
    # 可根据实际数据调整
    if 'G' in supplier or 'I' in supplier:
        return 2
    elif 'B' in supplier or 'E' in supplier:
        return 1
    else:
        return 0

def analyze_suppliers(df, supplier_col):
    """
    供应商分级分析
    返回: (supplier_stats, high_value_low_perf)
    """
    # 检查必要字段
    if 'unit_price' not in df.columns:
        return None
    # 其他可选字段
    has_quality = 'quality_rate' in df.columns
    has_ontime = 'ontime_rate' in df.columns
    has_years = 'relationship_years' in df.columns

    # 聚合
    agg_dict = {
        'unit_price': 'mean',
        'total_amount': 'sum'
    }
    if has_quality:
        agg_dict['quality_rate'] = 'mean'
    if has_ontime:
        agg_dict['ontime_rate'] = 'mean'
    if has_years:
        agg_dict['relationship_years'] = 'mean'
    supplier_stats = df.groupby(supplier_col).agg(agg_dict).reset_index()

    # 添加地理风险
    supplier_stats['geo_risk'] = supplier_stats[supplier_col].apply(assign_geo_risk)

    # 评分列
    score_cols = ['unit_price']
    weights = [0.3]
    if has_quality:
        score_cols.append('quality_rate')
        weights.append(0.25)
    if has_ontime:
        score_cols.append('ontime_rate')
        weights.append(0.25)
    if has_years:
        score_cols.append('relationship_years')
        weights.append(0.1)
    score_cols.append('geo_risk')
    weights.append(0.1)
    # 归一化权重
    weights = [w/sum(weights) for w in weights]

    # 标准化
    scaler = MinMaxScaler()
    for col in score_cols:
        if col == 'unit_price':
            # 价格越低得分越高（反向）
            supplier_stats[f'{col}_score'] = 1 - scaler.fit_transform(supplier_stats[[col]])
        elif col == 'geo_risk':
            # 风险越低得分越高
            supplier_stats[f'{col}_score'] = 1 - scaler.fit_transform(supplier_stats[[col]])
        else:
            supplier_stats[f'{col}_score'] = scaler.fit_transform(supplier_stats[[col]])

    # 综合得分
    supplier_stats['综合得分'] = sum(supplier_stats[f'{col}_score'] * w for col, w in zip(score_cols, weights))

    # 分级
    def grade(score):
        if score >= 0.8:
            return 'A级（优质）'
        elif score >= 0.6:
            return 'B级（良好）'
        elif score >= 0.4:
            return 'C级（一般）'
        else:
            return 'D级（待改进）'
    supplier_stats['等级'] = supplier_stats['综合得分'].apply(grade)

    # 高价值低绩效：采购额高于平均值且等级为 C 或 D
    avg_spend = supplier_stats['total_amount'].mean()
    grade_map = {'A级（优质）': 4, 'B级（良好）': 3, 'C级（一般）': 2, 'D级（待改进）': 1}
    supplier_stats['等级分值'] = supplier_stats['等级'].map(grade_map)
    high_value_low_perf = supplier_stats[(supplier_stats['total_amount'] > avg_spend) & (supplier_stats['等级分值'] <= 2)].copy()

    return supplier_stats, high_value_low_perf