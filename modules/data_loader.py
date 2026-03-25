import pandas as pd
import streamlit as st

FIELD_ALIASES = {
    'date': ['date', '日期', 'Date', '采购日期', '交易日期'],
    'supplier': ['supplier', '供应商', 'Supplier', '供应商名称', '卖方'],
    'unit_price': ['unit_price', '单价', 'Unit Price', '价格', '采购单价'],
    'quantity': ['quantity', '数量', 'Quantity', '采购数量'],
    'material_id': ['material_id', '物料编码', '物料编号', 'Material ID'],
    'material_name': ['material_name', '物料名称', 'Material Name'],
    'category': ['category', '物料类别', '类别', 'Category', '物料分类'],
    'total_amount': ['total_amount', '总金额', '金额', 'Total Amount', '采购金额'],
    'lead_time': ['lead_time', '交货周期', 'Lead Time', '交期'],
    'ontime_rate': ['ontime_rate', '准时率', 'Ontime Rate', '按时交付率'],
    'quality_rate': ['quality_rate', '质量合格率', 'Quality Rate', '合格率'],
    'relationship_years': ['relationship_years', '合作年限', '合作年数', 'Relationship Years']
}

def auto_rename_columns(df, field_aliases):
    rename_map = {}
    matched_fields = set()
    original_names = {}
    actual_cols_lower = {col.strip().lower(): col for col in df.columns}
    for std_field, aliases in field_aliases.items():
        for alias in aliases:
            alias_lower = alias.strip().lower()
            if alias_lower in actual_cols_lower:
                original_col = actual_cols_lower[alias_lower]
                rename_map[original_col] = std_field
                original_names[std_field] = original_col
                matched_fields.add(std_field)
                break
    if rename_map:
        df = df.rename(columns=rename_map)
    return df, matched_fields, original_names

def load_and_clean(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, parse_dates=False)
    else:
        df = pd.read_excel(uploaded_file, parse_dates=False)

    df, matched_fields, original_names = auto_rename_columns(df, FIELD_ALIASES)

    # 解析日期
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
    else:
        st.error("数据中未找到日期列，请确保包含日期字段")
        return None

    # 数值字段转换
    numeric_cols = ['unit_price', 'quantity'] + [c for c in ['total_amount', 'lead_time', 'ontime_rate', 'quality_rate', 'relationship_years'] if c in df.columns]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['unit_price', 'quantity'])

    # 如果 total_amount 不存在，则计算
    if 'total_amount' not in df.columns:
        df['total_amount'] = df['unit_price'] * df['quantity']
        st.info("未找到“总金额”字段，已自动计算（单价×数量）。")

    return df, matched_fields, original_names

def load_external_data():
    """加载外部经济指标数据（需放在项目根目录的 external_data.csv）"""
    try:
        df = pd.read_csv('external_data.csv', parse_dates=['date'])
        df.set_index('date', inplace=True)
        return df
    except Exception:
        return None

# 增加分析执行函数

def run_all_analyses(df, mapping, st_session_state):
    """
    执行所有分析模块，并将结果存入 session_state
    """
    from modules.supplier_analysis import analyze_suppliers
    from modules.material_analysis import category_spend, monthly_category_price, price_volatility
    from modules.abc_analysis import abc_by_category
    from modules.cost_reduction import calculate_savings  # 仅用于计算总采购额等

    # 获取必要字段
    supplier_col = mapping.get('supplier_name')
    category_col = mapping.get('category')
    amount_col = 'total_amount'
    price_col = 'unit_price'
    date_col = 'date'

    # 总采购额
    total_spend = df[amount_col].sum()
    st_session_state['total_spend'] = total_spend

    # 供应商分析
    if supplier_col and supplier_col in df.columns:
        result = analyze_suppliers(df, supplier_col)
        if result is not None:
            supplier_stats, high_value_low_perf = result
            st_session_state['supplier_stats'] = supplier_stats
            st_session_state['high_value_low_perf'] = high_value_low_perf
            st_session_state['total_high_spend'] = high_value_low_perf['total_amount'].sum() if not high_value_low_perf.empty else 0

    # 物料分析：品类支出、月度价格、波动性
    if category_col and category_col in df.columns:
        cat_spend = category_spend(df, category_col, amount_col)
        if cat_spend is not None:
            st_session_state['category_spend'] = cat_spend
        monthly_price = monthly_category_price(df, date_col, category_col, price_col)
        if monthly_price is not None:
            st_session_state['monthly_category_price'] = monthly_price
        volatility = price_volatility(df, category_col, price_col)
        if volatility is not None:
            st_session_state['price_volatility'] = volatility

        # ABC 分类
        abc_df = abc_by_category(df, category_col, amount_col, thresholds=(70, 90))
        if abc_df is not None:
            st_session_state['abc_category'] = abc_df

    # 可选：价格预测结果需在预测页面动态生成，不在此处计算