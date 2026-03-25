# pages/05_降本策略.py
import streamlit as st
import pandas as pd
import numpy as np
import re
from modules.cost_reduction import calculate_savings
from modules.abc_analysis import abc_by_category

st.set_page_config(layout="wide")
st.title("💡 降本策略报告")

# 从 session_state 中读取分析结果
total_spend = st.session_state.get('total_spend', 0)
total_high_spend = st.session_state.get('total_high_spend', 0)
supplier_stats = st.session_state.get('supplier_stats', pd.DataFrame())
abc_category = st.session_state.get('abc_category', pd.DataFrame())
high_value_low_perf = st.session_state.get('high_value_low_perf', pd.DataFrame())
forecast = st.session_state.get('final_forecast', None)
forecast_group = st.session_state.get('forecast_group', None)
last_price = st.session_state.get('last_price', None)
df = st.session_state.get('df', pd.DataFrame())
mapping = st.session_state.get('column_mapping', {})

# 如果总采购额未计算，从 df 计算
if total_spend == 0 and not df.empty and 'total_amount' in df.columns:
    total_spend = df['total_amount'].sum()
    st.session_state['total_spend'] = total_spend

# 获取关键列名
category_col = mapping.get('category')
material_col = mapping.get('material_name')
supplier_col = mapping.get('supplier_name')
price_col = mapping.get('unit_price')
amount_col = 'total_amount'
quantity_col = 'quantity'

# 侧边栏参数（仅保留谈判降价幅度）
st.sidebar.header("📊 降本估算参数")
negotiation_rate = st.sidebar.slider("高价值供应商谈判降价幅度 (%)", 0.0, 20.0, 5.0) / 100.0

# ========== 计算谈判降本 ==========
negotiation_saving = total_high_spend * negotiation_rate

# ========== 流程优化机会分析 ==========
process_savings_total = 0
process_opportunities = []

# 1. 高频小批量物料集中采购
if material_col and quantity_col and material_col in df.columns and quantity_col in df.columns:
    material_stats = df.groupby(material_col).agg(
        采购次数=(quantity_col, 'count'),
        平均单次数量=(quantity_col, 'mean'),
        总金额=(amount_col, 'sum')
    ).reset_index()
    if len(material_stats) > 0:
        median_qty = material_stats['平均单次数量'].median()
        bulk_candidates = material_stats[(material_stats['采购次数'] > 6) & (material_stats['平均单次数量'] < median_qty)]
        for _, row in bulk_candidates.iterrows():
            saving = row['总金额'] * 0.02
            process_savings_total += saving
            process_opportunities.append({
                '类型': '集中采购',
                '物料': row[material_col],
                '描述': f'年采购{row["采购次数"]}次，平均每次{row["平均单次数量"]:.0f}件，建议合并为季度或年度订单，预计节约 ¥{saving:,.2f}（2%）。'
            })

# 2. 同一供应商物料合并采购
if supplier_col and material_col and supplier_col in df.columns and material_col in df.columns:
    supplier_materials = df.groupby(supplier_col).agg(
        物料种类=('material_name', 'nunique'),
        总采购额=(amount_col, 'sum')
    ).reset_index()
    merge_candidates = supplier_materials[supplier_materials['物料种类'] >= 2]
    for _, row in merge_candidates.iterrows():
        saving = row['总采购额'] * 0.01
        process_savings_total += saving
        process_opportunities.append({
            '类型': '合并采购',
            '供应商': row[supplier_col],
            '描述': f'该供应商供应 {row["物料种类"]} 种物料，建议将订单合并统一谈判，预计节约 ¥{saving:,.2f}（1%）。'
        })

# 3. 长期协议机会（针对采购额大且稳定的物料）
if material_col and 'date' in df.columns:
    top_materials = df.groupby(material_col)[amount_col].sum().reset_index()
    top_materials = top_materials.sort_values(amount_col, ascending=False).head(int(len(top_materials)*0.2))
    for _, row in top_materials.iterrows():
        saving = row[amount_col] * 0.015
        process_savings_total += saving
        process_opportunities.append({
            '类型': '长期协议',
            '物料': row[material_col],
            '描述': f'该物料采购额 ¥{row[amount_col]:,.2f}，建议签订长期框架协议，锁定价格，预计节约 ¥{saving:,.2f}（1.5%）。'
        })

# 总流程优化降本
process_saving = process_savings_total
total_saving = negotiation_saving + process_saving
saving_percent = (total_saving / total_spend) * 100 if total_spend > 0 else 0

# ---------- 报告正文 ----------
st.header("📈 预期降本效果")
col1, col2, col3 = st.columns(3)
col1.metric("直接降本（谈判+替换）", f"¥{negotiation_saving/10000:,.2f} 万元")
col2.metric("流程优化降本", f"¥{process_saving/10000:,.2f} 万元")
col3.metric("合计预期降本", f"¥{total_saving/10000:,.2f} 万元")
st.metric("降本比例", f"{saving_percent:.2f}%", delta=f"相对总采购额 ¥{total_spend/10000:,.2f} 万元")

# 流程优化具体机会展示
if process_opportunities:
    st.subheader("🔧 流程优化具体机会")
    for opp in process_opportunities:
        if opp['类型'] == '集中采购':
            st.markdown(f"- **{opp['类型']}**：{opp['物料']} - {opp['描述']}")
        elif opp['类型'] == '合并采购':
            st.markdown(f"- **{opp['类型']}**：供应商 {opp['供应商']} - {opp['描述']}")
        else:
            st.markdown(f"- **{opp['类型']}**：{opp['物料']} - {opp['描述']}")
else:
    st.info("未发现明显的流程优化机会。")

# ========== 品类策略 ==========
st.header("📌 品类策略")

# 按物料类别的 ABC 分类
if category_col and category_col in df.columns:
    abc_cat = abc_by_category(df, category_col, amount_col, thresholds=(70, 90))
    a_cats = abc_cat[abc_cat['ABC分类'] == 'A类 (70%)'][category_col].tolist()
    if a_cats:
        a_cat_spend = abc_cat[abc_cat[category_col].isin(a_cats)]['total_amount'].sum()
        st.markdown(f"- **A类物料类别（{', '.join(a_cats)}）**：采购额 ¥{a_cat_spend:,.2f}（占 {a_cat_spend/total_spend:.1%}），建议实施战略采购，集中谈判，目标降价2-5%，预计可节约 ¥{a_cat_spend*0.03:,.2f}（按3%估算）。")
    else:
        st.markdown("- 暂无A类物料类别。")
else:
    st.markdown("- 无法进行ABC分类（缺少物料类别列）。")

# 按具体物料的 ABC 分类
if material_col and material_col in df.columns:
    mat_sum = df.groupby(material_col)[amount_col].sum().reset_index()
    mat_sum = mat_sum.sort_values(amount_col, ascending=False).reset_index(drop=True)
    total = mat_sum[amount_col].sum()
    mat_sum['累计占比'] = mat_sum[amount_col].cumsum() / total * 100
    def assign_abc(cum):
        if cum <= 70:
            return 'A类 (70%)'
        elif cum <= 90:
            return 'B类 (20%)'
        else:
            return 'C类 (10%)'
    mat_sum['ABC分类'] = mat_sum['累计占比'].apply(assign_abc)
    a_materials = mat_sum[mat_sum['ABC分类'] == 'A类 (70%)'][material_col].tolist()
    a_materials_spend = mat_sum[mat_sum[material_col].isin(a_materials)]['total_amount'].sum()
    if a_materials:
        st.markdown(f"- **A类物料（具体）**：共 {len(a_materials)} 种，采购总额 ¥{a_materials_spend:,.2f}（占 {a_materials_spend/total_spend:.1%}），建议对每个物料进行专项成本分析，与供应商开展一对一谈判。")
        st.markdown(f"  主要A类物料：{', '.join(a_materials[:5])}{'等' if len(a_materials)>5 else ''}")
    else:
        st.markdown("- 暂无A类物料。")
else:
    st.markdown("- 缺少物料名称列，无法进行按物料的ABC分类。")

# ========== 供应商策略 ==========
st.header("📌 供应商策略")
if not supplier_stats.empty:
    top_suppliers = supplier_stats[supplier_stats['等级'] == 'A级（优质）']['supplier'].tolist()
    if top_suppliers:
        st.markdown(f"- **优质供应商（{len(top_suppliers)}家）**：{', '.join(top_suppliers)}，建议增加采购份额，深化合作，争取更优价格。")
    if not high_value_low_perf.empty:
        high_suppliers = high_value_low_perf['supplier'].tolist()
        st.markdown(f"- **重点关注（高价值低绩效）**：{', '.join(high_suppliers)}，采购总额 ¥{total_high_spend:,.2f}，建议启动谈判，目标降价{negotiation_rate*100:.0f}%，可节约 ¥{negotiation_saving:,.2f}，或寻找替代供应商。")
    poor_suppliers = supplier_stats[supplier_stats['等级'] == 'D级（待改进）']['supplier'].tolist()
    if poor_suppliers:
        st.markdown(f"- **待改进供应商（{len(poor_suppliers)}家）**：{', '.join(poor_suppliers)}，建议约谈要求降价/提升质量，或逐步淘汰。")
else:
    st.markdown("- 供应商分级未完成，无法提供具体供应商策略。")

# ========== 采购模式优化 ==========
st.header("📌 采购模式优化")

# 单一供应商风险
if material_col and supplier_col and material_col in df.columns and supplier_col in df.columns:
    supplier_count = df.groupby(material_col)[supplier_col].nunique().reset_index()
    supplier_count.columns = [material_col, '供应商数量']
    single_source = supplier_count[supplier_count['供应商数量'] == 1]
    if not single_source.empty:
        st.markdown(f"- **单一供应商风险**：以下物料仅有单一供应商：{', '.join(single_source[material_col].tolist()[:5])}（共{len(single_source)}种），建议开发备选供应商，降低供应风险。")
    else:
        st.markdown("- 未检测到单一供应商风险，所有物料均有多个供应商。")
else:
    st.markdown("- 缺少物料名称或供应商列，无法识别单一供应商风险。")

# ========== 价格监控建议 ==========
st.header("📌 价格监控建议")
if price_col and material_col and price_col in df.columns and material_col in df.columns:
    volatile = df.groupby(material_col)[price_col].agg(lambda x: x.std()/x.mean()).reset_index(name='cv')
    high_vol = volatile[volatile['cv'] > 0.15][material_col].tolist()
    if high_vol:
        st.markdown(f"- 以下物料价格波动较大（变异系数>0.15）：{', '.join(high_vol[:5])}，建议建立价格预警机制。")
    else:
        st.markdown("- 物料价格波动均在正常范围，可维持现有监控。")
else:
    st.markdown("- 缺少物料名称或价格列，无法进行价格波动监控。")

# ========== 基于市场风险的补充建议 ==========
st.header("🌍 基于市场风险的补充建议")
if forecast is not None and last_price is not None:
    future_price = forecast['预测值'].iloc[-1]
    change_pct = (future_price - last_price) / last_price * 100
    if change_pct > 5:
        st.markdown(f"- **{forecast_group}价格预计上涨 {change_pct:.1f}%**（含风险溢价），建议提前采购锁定库存，或与供应商签订长协。")
    elif change_pct < -5:
        st.markdown(f"- **{forecast_group}价格预计下跌 {change_pct:.1f}%**，建议采用JIT采购，减少库存资金占用。")
    else:
        st.markdown(f"- **{forecast_group}价格走势平稳**，可维持现有采购策略。")
else:
    st.markdown("- 未进行价格预测或预测结果不可用。")

# 地理风险
if not supplier_stats.empty and 'geo_risk' in supplier_stats.columns:
    high_risk_suppliers = supplier_stats[supplier_stats['geo_risk'] > 1]['supplier'].tolist()
    if high_risk_suppliers:
        st.markdown(f"- **高风险地区供应商**：{', '.join(high_risk_suppliers)}，建议开发备选供应商以分散地缘风险。")

st.success(f"综合以上策略，预期可实现直接降本 ¥{negotiation_saving:,.2f}，流程优化降本 ¥{process_saving:,.2f}，合计 ¥{total_saving:,.2f}，占采购总额的 {saving_percent:.2f}%。")

# 导出报告按钮
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📄 导出报告 (Word)", use_container_width=True, type="primary"):
        # 构造分析摘要（使用原始数值，不格式化）
        analysis_summary = {
            "总采购额": total_spend,
            "直接降本（谈判）": negotiation_saving,
            "流程优化降本": process_saving,
            "总降本金额": total_saving,
            "降本比例": saving_percent,
            "分析周期": f"{df['date'].min().date()} 至 {df['date'].max().date()}" if not df.empty else "未知"
        }

        # 构造策略列表
        strategies = []

        # 谈判降本策略
        if total_high_spend > 0 and 'high_value_low_perf' in locals() and not high_value_low_perf.empty:
            strategies.append({
                '名称': '高价值低绩效供应商谈判',
                '金额': negotiation_saving,
                '比例': negotiation_rate,
                '难度': '中',
                '优先级': '高',
                '步骤': [
                    f"针对供应商 {', '.join(high_value_low_perf['supplier'].tolist())} 启动谈判",
                    f"目标降价 {negotiation_rate*100:.0f}%，预计节约 ¥{negotiation_saving:,.0f}",
                    "若谈判失败，则启动备选供应商开发"
                ],
                '风险提示': '谈判可能影响合作关系，需评估供应商依赖度'
            })

        # 流程优化策略（从 process_opportunities 提取）
        if 'process_opportunities' in locals():
            import re
            for opp in process_opportunities:
                # 提取金额（从描述中，格式如 "预计节约 ¥1,234.56"）
                match = re.search(r'¥([\d,]+\.?\d*)', opp['描述'])
                amount = float(match.group(1).replace(',', '')) if match else 0
                if opp['类型'] == '集中采购':
                    strategies.append({
                        '名称': f"集中采购：{opp['物料']}",
                        '金额': amount,
                        '比例': 0.02,
                        '难度': '低',
                        '优先级': '中',
                        '步骤': [
                            opp['描述'],
                            "将分散订单合并为季度或年度框架协议",
                            "与供应商重新协商价格"
                        ],
                        '风险提示': '可能增加库存资金占用，需平衡库存与采购成本'
                    })
                elif opp['类型'] == '合并采购':
                    strategies.append({
                        '名称': f"合并采购：供应商 {opp['供应商']}",
                        '金额': amount,
                        '比例': 0.01,
                        '难度': '低',
                        '优先级': '中',
                        '步骤': [
                            opp['描述'],
                            "整合该供应商所有物料的订单，统一谈判",
                            "争取更优价格和付款条件"
                        ],
                        '风险提示': '可能降低对单一物料的议价能力，但整体利大于弊'
                    })
                elif opp['类型'] == '长期协议':
                    strategies.append({
                        '名称': f"长期协议：{opp['物料']}",
                        '金额': amount,
                        '比例': 0.015,
                        '难度': '中',
                        '优先级': '高',
                        '步骤': [
                            opp['描述'],
                            "签订1-3年框架协议，锁定价格",
                            "约定价格调整机制（如与市场指数挂钩）"
                        ],
                        '风险提示': '长期锁定可能错过市场降价机会，需设置价格调整条款'
                    })

        # 品类策略（A类物料）
        if 'a_materials' in locals() and a_materials:
            strategies.append({
                '名称': 'A类物料重点管控',
                '金额': a_materials_spend * 0.03,
                '比例': 0.03,
                '难度': '高',
                '优先级': '高',
                '步骤': [
                    f"对 {', '.join(a_materials[:3])} 等A类物料进行专项成本分析",
                    "与关键供应商进行高层谈判",
                    "考虑引入电子竞标（e-auction）",
                    "建立价格监测与预警机制"
                ],
                '风险提示': 'A类物料更换供应商成本高，需谨慎评估质量与交期风险'
            })

        # 生成并下载报告
        from modules.report_generator import ReportGenerator
        report_bytes = ReportGenerator.generate_word_report(
            strategies=strategies,
            analysis_summary=analysis_summary,
            company_name="采购中心"
        )
        st.download_button(
            label="点击下载报告",
            data=report_bytes,
            file_name="采购降本策略报告.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="download_report"
        )