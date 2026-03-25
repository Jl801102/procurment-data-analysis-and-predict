# pages/02_物料分析.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.material_analysis import (
    category_spend, monthly_category_price, price_volatility, scale_effect
)
from modules.abc_analysis import abc_by_category

st.title("📦 物料分析")

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("请先上传数据")
    st.stop()

df = st.session_state['df']
mapping = st.session_state.get('column_mapping', {})
category_col = mapping.get('category')
material_col = mapping.get('material_name')
if not category_col or category_col not in df.columns:
    st.error("数据缺少物料类别列，请先在数据上传页面完成列名映射。")
    st.stop()

# 选择分析维度
analysis_dim = st.radio("分析维度", ["按物料类别", "按物料"], horizontal=True)

if analysis_dim == "按物料类别":
    # ---------- 原有按类别分析 ----------
    tab1, tab2, tab3, tab4 = st.tabs(["📊 品类结构", "📈 价格趋势", "📉 价格波动性", "📐 规模效应"])

    with tab1:
        st.subheader("各类别采购金额占比")
        cat_spend = category_spend(df, category_col, 'total_amount')
        if cat_spend is not None:
            fig = px.pie(cat_spend, values='total_amount', names=category_col, title='各类别采购金额占比')
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("各类别月度平均价格趋势")
        monthly_price = monthly_category_price(df, 'date', category_col, 'unit_price')
        if monthly_price is not None:
            fig = px.line(monthly_price, x='date', y='unit_price', color=category_col,
                          title='各类别月度平均价格趋势')
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("📊 各类别价格波动性（变异系数）")
        volatility = price_volatility(df, category_col, 'unit_price')
        if volatility is not None:
            threshold = 0.15
            volatility['color'] = volatility['变异系数'].apply(lambda x: 'red' if x > threshold else 'steelblue')
            fig = go.Figure()
            for _, row in volatility.iterrows():
                fig.add_trace(go.Bar(
                    x=[row[category_col]],
                    y=[row['变异系数']],
                    name=row[category_col],
                    marker_color=row['color'],
                    text=[f"{row['变异系数']:.3f}"],
                    textposition='outside'
                ))
            fig.add_hline(y=threshold, line_dash="dash", line_color="orange",
                          annotation_text=f"警示线 (CV={threshold})", annotation_position="top right")
            fig.update_layout(title="各类别价格波动性（变异系数）", xaxis_title="物料类别", yaxis_title="变异系数", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            high_risk = volatility[volatility['变异系数'] > threshold]
            if not high_risk.empty:
                st.warning(f"⚠️ 以下类别价格波动性超过 {threshold}：{', '.join(high_risk[category_col].tolist())}，建议重点关注！")
        else:
            st.info("无法计算价格波动性，请检查数据。")

    with tab4:
        st.subheader("规模效应分析")
        categories = df[category_col].unique()
        selected = st.selectbox("选择物料类别", categories)
        corr, fig = scale_effect(df, selected, category_col, 'quantity', 'unit_price')
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
            if corr < -0.1:
                st.success(f"✅ {selected} 存在规模效应（相关系数 {corr:.2f}），建议整合采购获取折扣。")
            else:
                st.info(f"ℹ️ {selected} 规模效应不明显（相关系数 {corr:.2f}），可关注其他降本方式。")

    # ABC 分类（按类别）
    st.subheader("📊 ABC 分类（按物料类别）")
    abc_df = abc_by_category(df, category_col, 'total_amount', thresholds=(70, 90))
    if abc_df is not None:
        st.dataframe(abc_df)
        # 帕累托图
        from plotly.subplots import make_subplots
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=abc_df[category_col], y=abc_df['total_amount'], name="采购金额"), secondary_y=False)
        fig.add_trace(go.Scatter(x=abc_df[category_col], y=abc_df['累计占比'], name="累计占比 (%)", mode='lines+markers'), secondary_y=True)
        fig.update_yaxes(title_text="采购金额", secondary_y=False)
        fig.update_yaxes(title_text="累计占比 (%)", secondary_y=True)
        fig.update_layout(title="物料类别ABC分析（帕累托图）")
        st.plotly_chart(fig, use_container_width=True)

        a_items = abc_df[abc_df['ABC分类'] == 'A类 (70%)'][category_col].tolist()
        if a_items:
            a_spend = abc_df[abc_df[category_col].isin(a_items)]['total_amount'].sum()
            st.info(f"**A类物料**（占70%支出）：{', '.join(a_items)}，采购总额 ¥{a_spend:,.2f}，建议作为降本重点。")
    else:
        st.warning("无法进行ABC分类，请检查数据。")

else:
    # ---------- 按物料分析 ----------
    if not material_col or material_col not in df.columns:
        st.error("缺少物料名称列，无法进行物料级分析。")
        st.stop()

    # 获取所有物料
    materials = df[material_col].unique()
    selected_material = st.selectbox("选择物料", materials)
    material_df = df[df[material_col] == selected_material].copy()

    if len(material_df) < 5:
        st.warning("该物料数据点不足5条，无法进行详细分析。")
    else:
        # 价格趋势
        st.subheader(f"📈 {selected_material} 价格趋势")
        fig = px.line(material_df, x='date', y='unit_price', title=f"{selected_material} 价格趋势", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # 价格波动性
        st.subheader(f"📊 {selected_material} 价格波动性")
        # 计算变异系数
        cv = material_df['unit_price'].std() / material_df['unit_price'].mean()
        threshold = 0.15
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[selected_material], y=[cv], name="变异系数", marker_color='red' if cv > threshold else 'steelblue',
                              text=[f"{cv:.3f}"], textposition='outside'))
        fig.add_hline(y=threshold, line_dash="dash", line_color="orange", annotation_text=f"警示线 (CV={threshold})")
        fig.update_layout(title=f"{selected_material} 价格变异系数", yaxis_title="变异系数")
        st.plotly_chart(fig, use_container_width=True)
        if cv > threshold:
            st.warning(f"⚠️ {selected_material} 价格波动性较高（CV={cv:.3f}），建议关注市场变化。")
        else:
            st.info(f"✅ {selected_material} 价格波动性在可控范围内（CV={cv:.3f}）。")

        # 采购量与单价关系（规模效应）
        if len(material_df) >= 5:
            st.subheader(f"📐 {selected_material} 规模效应分析")
            fig = px.scatter(material_df, x='quantity', y='unit_price', trendline='ols',
                             labels={'quantity': '采购数量', 'unit_price': '单价'},
                             title=f"{selected_material} 采购量 vs 单价")
            st.plotly_chart(fig, use_container_width=True)
            corr = material_df[['quantity', 'unit_price']].corr().iloc[0,1]
            if corr < -0.1:
                st.success(f"✅ {selected_material} 存在规模效应（相关系数 {corr:.2f}），建议整合采购获取折扣。")
            else:
                st.info(f"ℹ️ {selected_material} 规模效应不明显（相关系数 {corr:.2f}），可关注其他降本方式。")

        # 供应商分析（针对该物料）
        st.subheader(f"🏭 {selected_material} 供应商分布")
        supplier_list = material_df.groupby('supplier')['total_amount'].sum().reset_index()
        fig = px.bar(supplier_list, x='supplier', y='total_amount', title=f"{selected_material} 采购额按供应商分布")
        st.plotly_chart(fig, use_container_width=True)

    # 全物料 ABC 分类（按物料名称）
    st.subheader("📊 ABC 分类（按物料）")
    from modules.abc_analysis import abc_by_material  # 需要实现该函数
    # 如果未实现 abc_by_material，则用备选方法：按物料名称聚合
    try:
        abc_mat_df = abc_by_material(df, material_col, 'total_amount', thresholds=(70, 90))
    except:
        # 简单实现：按物料名称进行 ABC 分类
        mat_sum = df.groupby(material_col)['total_amount'].sum().reset_index()
        mat_sum = mat_sum.sort_values('total_amount', ascending=False).reset_index(drop=True)
        mat_sum['累计占比'] = mat_sum['total_amount'].cumsum() / mat_sum['total_amount'].sum() * 100
        def assign_abc(cum):
            if cum <= 70:
                return 'A类 (70%)'
            elif cum <= 90:
                return 'B类 (20%)'
            else:
                return 'C类 (10%)'
        mat_sum['ABC分类'] = mat_sum['累计占比'].apply(assign_abc)
        abc_mat_df = mat_sum[[material_col, 'total_amount', '累计占比', 'ABC分类']]
    st.dataframe(abc_mat_df)