import streamlit as st
import plotly.express as px
from modules.supplier_analysis import analyze_suppliers

st.title("🏭 供应商分析")

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("请先上传数据")
    st.stop()

df = st.session_state['df']
mapping = st.session_state.get('column_mapping', {})
supplier_col = mapping.get('supplier_name')
if not supplier_col or supplier_col not in df.columns:
    st.error("数据缺少供应商列，请先在数据上传页面完成列名映射。")
    st.stop()

# 执行供应商分析
with st.spinner("正在分析供应商..."):
    result = analyze_suppliers(df, supplier_col)
    if result is None:
        st.error("供应商分析失败，请检查数据是否包含必要字段（价格、质量率、准时率等）。")
        st.stop()
    supplier_stats, high_value_low_perf = result

# 保存结果到 session_state
st.session_state['supplier_stats'] = supplier_stats
st.session_state['high_value_low_perf'] = high_value_low_perf
st.session_state['total_high_spend'] = high_value_low_perf['total_amount'].sum() if not high_value_low_perf.empty else 0

# 显示
st.subheader("供应商评分与等级")
display_cols = ['supplier', 'total_amount', '综合得分', '等级']
if 'unit_price' in supplier_stats.columns:
    display_cols.append('unit_price')
if 'quality_rate' in supplier_stats.columns:
    display_cols.append('quality_rate')
if 'ontime_rate' in supplier_stats.columns:
    display_cols.append('ontime_rate')
if 'relationship_years' in supplier_stats.columns:
    display_cols.append('relationship_years')
st.dataframe(supplier_stats[display_cols].style.format({'total_amount': '¥{:,.2f}', '综合得分': '{:.3f}'}))

# 散点图（质量 vs 准时率）
if 'quality_rate' in supplier_stats.columns and 'ontime_rate' in supplier_stats.columns:
    fig = px.scatter(supplier_stats, x='ontime_rate', y='quality_rate', size='total_amount',
                     color='等级', hover_name='supplier',
                     labels={'ontime_rate': '准时率', 'quality_rate': '质量率', 'total_amount': '采购额'},
                     title='供应商绩效分布（气泡大小=采购额）')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("缺少质量率或准时率字段，无法绘制绩效散点图。")

# 高价值低绩效供应商
st.subheader("🎯 重点降本机会")
if not high_value_low_perf.empty:
    st.markdown("**高价值低绩效供应商**（建议谈判或替换）：")
    st.dataframe(high_value_low_perf[['supplier', 'total_amount', '等级', '综合得分']].style.format({'total_amount': '¥{:,.2f}'}))
    st.metric("这些供应商采购总额", f"¥{high_value_low_perf['total_amount'].sum():,.2f}")
else:
    st.info("未发现高价值低绩效供应商。")