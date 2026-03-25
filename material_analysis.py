import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def category_spend(df, category_col, amount_col):
    """各类别采购金额汇总"""
    if category_col not in df.columns or amount_col not in df.columns:
        return None
    return df.groupby(category_col)[amount_col].sum().reset_index()

def monthly_category_price(df, date_col, category_col, price_col):
    """各类别月度平均价格"""
    if date_col not in df.columns or category_col not in df.columns or price_col not in df.columns:
        return None
    monthly = df.groupby([pd.Grouper(key=date_col, freq='M'), category_col])[price_col].mean().reset_index()
    return monthly

def price_volatility(df, category_col, price_col):
    """各类别价格变异系数"""
    if category_col not in df.columns or price_col not in df.columns:
        return None
    cv = df.groupby(category_col)[price_col].agg(lambda x: x.std()/x.mean()).reset_index(name='变异系数')
    return cv

def scale_effect(df, category, category_col, quantity_col, price_col):
    """分析指定类别的规模效应（数量 vs 单价）"""
    if category_col not in df.columns or quantity_col not in df.columns or price_col not in df.columns:
        return None, None
    cat_df = df[df[category_col] == category]
    if len(cat_df) < 5:
        return None, None
    fig = px.scatter(cat_df, x=quantity_col, y=price_col, trendline='ols',
                     labels={quantity_col: '采购数量', price_col: '单价'},
                     title=f'{category} 采购量 vs 单价')
    # 计算相关系数
    corr = cat_df[[quantity_col, price_col]].corr().iloc[0,1]
    return corr, fig