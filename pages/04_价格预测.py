# pages/04_价格预测.py
import streamlit as st
import pandas as pd
import numpy as np
from modules.price_forecast import forecast_price
from modules.data_loader import load_external_data

st.title("🔮 价格预测")

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("请先上传数据")
    st.stop()

df = st.session_state['df']
mapping = st.session_state.get('column_mapping', {})

# 获取必要的列名
category_col = mapping.get('category')
material_col = mapping.get('material_name')
date_col = 'date'
price_col = 'unit_price'

# 检查必要列是否存在
if date_col not in df.columns or price_col not in df.columns:
    st.error("缺少日期或单价列，无法进行价格预测")
    st.stop()

# 选择分析维度
analysis_dim = st.radio("预测维度", ["按物料类别", "按物料"], horizontal=True)

# 根据维度选择具体项
if analysis_dim == "按物料类别":
    if not category_col or category_col not in df.columns:
        st.error("数据缺少物料类别列，无法按类别预测。请先在数据上传页面完成列名映射。")
        st.stop()
    group_col = category_col
    group_name = "物料类别"
    groups = df[group_col].unique()
else:
    if not material_col or material_col not in df.columns:
        st.error("数据缺少物料名称列，无法按物料预测。请先在数据上传页面完成列名映射。")
        st.stop()
    group_col = material_col
    group_name = "物料"
    groups = df[group_col].unique()

selected_group = st.selectbox(f"选择{group_name}", groups)

# 过滤数据
group_filter = df[group_col] == selected_group
group_df = df[group_filter].copy()

# 准备时间序列（按月平均）
monthly = group_df.set_index(date_col).resample('ME')[price_col].mean().dropna()
if len(monthly) < 12:
    st.warning(f"{selected_group} 的历史数据不足12个月（仅有{len(monthly)}个月），无法进行可靠预测。")
    st.stop()

# 外部变量加载
use_external = st.checkbox("使用外部经济指标（原油价格、地缘风险指数）增强预测", value=True)
external_df = None
if use_external:
    external_df = load_external_data()
    if external_df is None:
        st.warning("未找到外部数据文件 external_data.csv，将使用纯时间序列预测。")
        use_external = False

# 模型选择
model_type = st.radio("预测模型", ["纯时间序列 (SARIMA)", "含外部变量 (ARIMAX)"], horizontal=True)

# 风险溢价
risk_premium = st.slider("地缘风险溢价 (%)", -20, 20, 0, step=1) / 100.0

if st.button("开始预测", type="primary"):
    with st.spinner("训练预测模型中..."):
        try:
            # 准备外生变量（如果使用）
            exog = None
            if model_type == "含外部变量 (ARIMAX)" and use_external and external_df is not None:
                # 对齐时间序列
                exog = external_df.reindex(monthly.index, method='ffill')
                exog = exog.dropna()
                # 确保索引一致
                common_idx = monthly.index.intersection(exog.index)
                if len(common_idx) < 12:
                    st.warning("外部变量与价格数据时间对齐后数据点不足，将使用纯时间序列预测。")
                    exog = None
                else:
                    monthly = monthly.loc[common_idx]
                    exog = exog.loc[common_idx]

            # 调用预测函数
            forecast, fig = forecast_price(monthly, exog=exog, steps=3, risk_premium=risk_premium)
            st.plotly_chart(fig, use_container_width=True)

            # 显示预测表格
            st.subheader("未来3个月价格预测")
            forecast.index = forecast.index.strftime('%Y-%m')
            st.dataframe(forecast.round(2))

            # 保存预测结果供降本策略使用（覆盖之前的预测结果）
            st.session_state['final_forecast'] = forecast
            st.session_state['forecast_group'] = selected_group
            st.session_state['last_price'] = monthly.iloc[-1]

        except Exception as e:
            st.error(f"预测失败：{e}")
