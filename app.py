import streamlit as st

st.set_page_config(
    page_title="采购数据分析与降本策略平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

import hashlib

# 管理员密码（实际中应使用环境变量或更安全的存储）
ADMIN_PASSWORD_HASH = hashlib.sha256("Jl971026".encode()).hexdigest()

# 初始化会话状态中的认证标志
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# 侧边栏登录区域
with st.sidebar:
    st.markdown("---")
    if not st.session_state['authenticated']:
        st.subheader("🔐 管理员登录")
        password = st.text_input("密码", type="password", key="admin_password")
        if st.button("登录"):
            if hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
                st.session_state['authenticated'] = True
                st.success("登录成功！")
                st.rerun()
            else:
                st.error("密码错误")
    else:
        st.success("✅ 管理员模式已启用")
        if st.button("退出登录"):
            st.session_state['authenticated'] = False
            st.rerun()


# 自定义CSS
st.markdown("""
<style>
.main-header {
    font-size: 2rem;
    font-weight: bold;
    color: #1565C0;
    text-align: center;
    padding: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📊 采购数据分析与降本策略平台</p>', unsafe_allow_html=True)

st.markdown("""
### 🎯 平台简介
本平台面向制造业采购工程师，提供从数据上传到策略生成的全流程采购分析支持。

---
### 🚀 快速开始
👈 **请从左侧菜单选择功能模块**

| 模块 | 功能描述 |
|------|----------|
| 📁 数据上传 | 支持 Excel/CSV 格式，自动识别列名，一键清洗 |
| 📦 物料分析 | 品类结构、价格趋势、价格波动性、规模效应分析 |
| 🏭 供应商分析 | 多维度评分、分级（A~D）、高价值低绩效识别 |
| 🔮 价格预测 | 基于 SARIMA/ARIMAX 的预测，支持外部变量和风险溢价情景分析 |
| 💡 降本策略 | 自动生成品类策略、供应商策略、采购模式优化、价格监控建议，并量化降本效果 |
""")

with st.sidebar:
    st.markdown("---")
    st.markdown("**技术栈**")
    st.markdown("- Python + Streamlit\n- Pandas + Plotly\n- scikit-learn\n- statsmodels")