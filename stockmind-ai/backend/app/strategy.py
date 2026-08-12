
import operator
OPS={"<":operator.lt,">":operator.gt,"<=":operator.le,">=":operator.ge,"==":operator.eq}
FIELDS={"rsi":"rsi","ma20":"ma20","ma50":"ma50","macd":"macd","signal":"signal","vol_ratio":"vol_ratio"}
ALLOWED=set(FIELDS)|{"ml_probability","lstm_probability","sentiment"}
def validate(rules):
    for r in rules:
        if r.get("field") not in ALLOWED or r.get("op") not in OPS:
            raise ValueError("Invalid no-code rule")
    return True
def evaluate(row,rules,ml_prob=.5,lstm_prob=.5,sentiment=0):
    validate(rules)
    results=[]
    for r in rules:
        f=r["field"]; v=float(r.get("value",0))
        actual={"ml_probability":ml_prob,"lstm_probability":lstm_prob,"sentiment":sentiment}.get(f,row[FIELDS[f]])
        results.append(OPS[r.get("op","<")](actual,v))
    return all(results) if results else False
