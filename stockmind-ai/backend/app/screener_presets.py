
PRESETS={
 "Bandarmology":[{"field":"broker_flow","op":">","value":15},{"field":"accumulation","op":">","value":60},{"field":"volume_ratio","op":">","value":1.5}],
 "Teknikal":[{"field":"rsi","op":">=","value":50},{"field":"ma20_ma50","op":">","value":0},{"field":"macd","op":">","value":0},{"field":"volume_ratio","op":">","value":1.2}],
 "Fundamental":[{"field":"roe","op":">","value":12},{"field":"eps_growth","op":">","value":5},{"field":"debt_equity","op":"<","value":1.5}]
}
def list_presets():
 return [{"name":k,"rules":v} for k,v in PRESETS.items()]
