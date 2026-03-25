# pages/01_数据上传.py
import streamlit as st
import pandas as pd
import traceback    
from modules.data_loader import load_and_clean, run_all_analyses
from modules.demo_data import generate_demo_data

st.title("📁 数据上传与处理")

# 获取认证状态
is_admin = st.session_state.get('authenticated', False)

# 选项卡
tab1, tab2, tab3 = st.tabs(["📤 上传文件", "🔍 数据预览", "🔧 列名映射"])

with tab1:
    st.subheader("支持格式：Excel / CSV")
    
    # 管理员：显示上传组件和Demo按钮
    if is_admin:
        uploaded_file = st.file_uploader("拖拽或点击上传文件", type=['xlsx', 'xls', 'csv'])
        # Demo按钮始终显示，但仅用于管理员快速体验
        if st.button("🚀 加载 Demo 数据（快速体验）"):
            with st.spinner("生成 Demo 数据中..."):
                try:
                    demo_df = generate_demo_data()
                    st.session_state['df'] = demo_df
                    auto_mapping = {
                        'supplier_name': 'supplier',
                        'material_code': 'material_id',
                        'material_name': 'material_name',
                        'unit_price': 'unit_price',
                        'quantity': 'quantity',
                        'total_amount': 'total_amount',
                        'order_date': 'date',
                        'category': 'category'
                    }
                    auto_mapping = {k: v for k, v in auto_mapping.items() if v is not None}
                    st.session_state['auto_mapping'] = auto_mapping
                    st.session_state['manual_mapping'] = {}
                    st.session_state['column_mapping'] = auto_mapping
                    st.session_state['original_names'] = {v: v for v in demo_df.columns}
                    run_all_analyses(demo_df, auto_mapping, st.session_state)
                    st.success("✅ Demo 数据加载成功！")
                    st.info(f"共 {len(demo_df)} 条记录...")
                    st.stop()
                except Exception as e:
                    st.error(f"加载失败：{e}")
                    st.code(traceback.format_exc())
        
        if uploaded_file:
            with st.spinner("处理文件中..."):
                result = load_and_clean(uploaded_file)
                if result is None:
                    st.error("数据加载失败，请检查文件格式。")
                else:
                    df, matched_fields, original_names = result
                    st.session_state['df'] = df
                    st.session_state['original_names'] = original_names
                    auto_mapping = {std: original_names[std] for std in matched_fields if std in original_names}
                    st.session_state['auto_mapping'] = auto_mapping
                    st.session_state['manual_mapping'] = {}
                    st.success(f"✅ 数据加载成功！共 {len(df)} 条记录。")
                    st.info(f"自动识别字段：{', '.join([f'{std}（→{original_names[std]}）' for std in matched_fields])}")
                    st.info("请前往「列名映射」选项卡确认字段映射，并点击保存按钮以进行分析。")
    else:
        # 非管理员（招聘方）：只显示Demo按钮，不显示上传组件
        st.info("当前为访客模式，仅可体验 Demo 数据。如需上传数据，请联系管理员获取权限。")
        if st.button("🚀 加载 Demo 数据（快速体验）"):
            with st.spinner("生成 Demo 数据中..."):
                try:
                    demo_df = generate_demo_data()
                    st.session_state['df'] = demo_df
                    auto_mapping = {
                        'supplier_name': 'supplier',
                        'material_code': 'material_id',
                        'material_name': 'material_name',
                        'unit_price': 'unit_price',
                        'quantity': 'quantity',
                        'total_amount': 'total_amount',
                        'order_date': 'date',
                        'category': 'category'
                    }
                    auto_mapping = {k: v for k, v in auto_mapping.items() if v is not None}
                    st.session_state['auto_mapping'] = auto_mapping
                    st.session_state['manual_mapping'] = {}
                    st.session_state['column_mapping'] = auto_mapping
                    st.session_state['original_names'] = {v: v for v in demo_df.columns}
                    run_all_analyses(demo_df, auto_mapping, st.session_state)
                    st.success("✅ Demo 数据加载成功！")
                    st.info(f"共 {len(demo_df)} 条记录...")
                    st.stop()
                except Exception as e:
                    st.error(f"加载失败：{e}")
                    st.code(traceback.format_exc())

with tab2:
    # 数据预览部分（与认证无关，直接显示 session_state 中的数据）
    if 'df' in st.session_state:
        df = st.session_state['df']
        st.subheader(f"数据预览（共 {len(df)} 条，{len(df.columns)} 列）")
        st.dataframe(df.head(50), use_container_width=True)
        with st.expander("📊 数值列统计摘要"):
            st.dataframe(df.describe(), use_container_width=True)
    else:
        st.info("请先加载 Demo 数据或上传文件")

with tab3:
    # 列名映射部分，同样需要数据存在
    if 'df' in st.session_state:
        df = st.session_state['df']
        auto_mapping = st.session_state.get('auto_mapping', {})
        manual_mapping = st.session_state.get('manual_mapping', {})
        standard_fields = [
            'supplier_name', 'material_code', 'material_name', 'unit_price',
            'quantity', 'total_amount', 'order_date', 'delivery_date', 'category'
        ]
        updated_mapping = {}
        col1, col2 = st.columns(2)
        for i, field in enumerate(standard_fields):
            with col1 if i < len(standard_fields)//2 else col2:
                current = manual_mapping.get(field, auto_mapping.get(field, "不使用"))
                options = ["不使用"] + list(df.columns)
                idx = options.index(current) if current in options else 0
                selected = st.selectbox(f"{field}", options, index=idx, key=f"map_{field}")
                if selected != "不使用":
                    updated_mapping[field] = selected

        if st.button("✅ 保存列名映射", type="primary"):
            # 合并自动和手动映射（手动优先）
            final_mapping = {**auto_mapping, **updated_mapping}
            # 只保留标准字段
            final_mapping = {k: v for k, v in final_mapping.items() if k in standard_fields}
            st.session_state['column_mapping'] = final_mapping
            # 保存映射后，执行所有分析
            run_all_analyses(df, final_mapping, st.session_state)
            st.success("列名映射已保存！分析已完成，现在可以查看各分析页面。")
            st.json(final_mapping)

        # 以下映射UI保持不变，但保存按钮应仅在管理员模式下有效？这里可以保留，但只有管理员能修改映射
        # 但访客模式下，用户可能修改映射但无法上传新数据，所以也可以保留映射UI，但保存后数据仍为Demo数据，无妨。
        # 为了简化，映射UI对所有用户可见，但只有管理员能够保存后重新分析（但访客保存也会重新分析，只是数据源仍是Demo）
        # 这不会造成问题，因为数据未变。所以不需要额外限制。
        # 但为了体验，可以保留
 
    else:
        st.info("请先加载 Demo 数据或上传文件")
