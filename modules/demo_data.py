# modules/demo_data.py
import pandas as pd
import numpy as np

def generate_demo_data():
    """生成包含完整字段的示例采购数据"""
    np.random.seed(42)
    n = 200
    suppliers = ['上海精密五金', '广东力合电子', '苏州联达材料', '深圳鑫源科技', '浙江华锐制造']
    materials = ['铜排A型', '绝缘套管', '铝合金壳体', '精密螺丝M4', '导热硅脂']
    categories = ['金属材料', '电子元件', '机械零件']
    
    df = pd.DataFrame({
        'date': pd.date_range('2022-01-01', periods=n, freq='W'),  # 每周一条
        'supplier': np.random.choice(suppliers, n),
        'material_name': np.random.choice(materials, n),
        'material_id': ['MAT-' + str(np.random.randint(1000, 9999)) for _ in range(n)],
        'category': np.random.choice(categories, n),
        'unit_price': np.random.uniform(10, 500, n).round(2),
        'quantity': np.random.randint(50, 500, n),
        'quality_rate': np.random.uniform(0.85, 1.0, n).round(2),
        'ontime_rate': np.random.uniform(0.8, 1.0, n).round(2),
        'relationship_years': np.random.randint(1, 10, n)
    })
    df['total_amount'] = (df['unit_price'] * df['quantity']).round(2)
    return df