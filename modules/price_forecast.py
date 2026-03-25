# modules/price_forecast.py
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.statespace.sarimax import SARIMAX

def forecast_price(ts, exog=None, steps=3, risk_premium=0):
    """
    时间序列预测（SARIMA/ARIMAX）
    ts: pandas Series，索引为日期，值为价格
    exog: 外生变量DataFrame，索引需与ts对齐
    steps: 预测步数（月）
    risk_premium: 风险溢价（如0.05表示+5%）
    返回：预测DataFrame，绘图对象
    """
    if len(ts) < 12:
        raise ValueError("数据量不足12个月")

    # 拟合模型
    if exog is not None:
        model = SARIMAX(ts, exog=exog, order=(1,1,1), seasonal_order=(1,1,1,12))
    else:
        model = SARIMAX(ts, order=(1,1,1), seasonal_order=(1,1,1,12))
    results = model.fit(disp=False)

    # 预测
    if exog is not None:
        # 使用最后三个月的外生变量平均值作为未来值
        last_exog = exog.iloc[-3:].mean().values.reshape(1, -1)
        future_exog = np.repeat(last_exog, steps, axis=0)
        forecast = results.get_forecast(steps=steps, exog=future_exog)
    else:
        forecast = results.get_forecast(steps=steps)

    pred_mean = forecast.predicted_mean
    pred_ci = forecast.conf_int()
    pred_mean_adj = pred_mean * (1 + risk_premium)

    forecast_df = pd.DataFrame({
        '预测值': pred_mean_adj,
        '下限': pred_ci.iloc[:,0],
        '上限': pred_ci.iloc[:,1]
    })

    # 绘图
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts.index, y=ts.values, mode='lines', name='历史价格'))
    fig.add_trace(go.Scatter(x=pred_mean.index, y=pred_mean_adj, mode='lines+markers', name=f'预测值 (风险溢价 {risk_premium:.1%})', line=dict(dash='dash')))
    fig.add_trace(go.Scatter(x=pred_ci.index, y=pred_ci.iloc[:,0], mode='lines', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=pred_ci.index, y=pred_ci.iloc[:,1], mode='lines', fill='tonexty', fillcolor='rgba(255,0,0,0.2)', name='80%置信区间'))
    fig.update_layout(title='价格预测（未来3个月）', xaxis_title='日期', yaxis_title='价格')

    return forecast_df, fig