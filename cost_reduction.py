def calculate_savings(total_spend, total_high_spend, negotiation_rate, process_rate):
    """计算预期降本"""
    negotiation_saving = total_high_spend * negotiation_rate
    process_saving = total_spend * process_rate
    total_saving = negotiation_saving + process_saving
    percent = (total_saving / total_spend) * 100 if total_spend > 0 else 0
    return {
        'negotiation': negotiation_saving,
        'process': process_saving,
        'total': total_saving,
        'percent': percent
    }