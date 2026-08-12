
import os
def analyze(texts):
    try:
        from transformers import pipeline
        pipe=pipeline("text-classification",model=os.getenv("FINBERT_MODEL","ProsusAI/finbert"),top_k=None)
        out=[]; scores=[]
        for text in texts:
            r=pipe(text[:2000])[0]
            best=max(r,key=lambda z:z["score"]); label=best["label"].lower()
            val={"positive":1,"neutral":0,"negative":-1}.get(label,0)*best["score"]
            scores.append(val); out.append({"label":label,"score":best["score"]})
        return {"items":out,"score":sum(scores)/len(scores) if scores else 0}
    except Exception as e:
        return {"items":[{"label":"neutral","score":1.0} for _ in texts],
                "score":0,"fallback":True,"error":str(e)}
