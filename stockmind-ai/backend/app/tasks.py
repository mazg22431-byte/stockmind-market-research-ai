
from .core import celery
@celery.task
def ingest_train_ensemble(ticker,start=None,end=None):
    import asyncio, tempfile, os, pandas as pd, json
    from .ingest import ingest_idx
    from .feature_store import build
    from .ml import train_from_csv
    from .ensemble import train_lstm_walkforward, save_lstm, register_ensemble

    df,actions=asyncio.run(ingest_idx(ticker,start,end))
    meta=build(ticker,df)
    with tempfile.NamedTemporaryFile(suffix=".csv",delete=False) as f:path=f.name
    df.to_csv(path,index=False)
    tree=train_from_csv(ticker,path)
    os.unlink(path)

    lstm_model,lstm_metrics=train_lstm_walkforward(df)
    lstm_version="v"+pd.Timestamp.utcnow().strftime("%Y%m%d%H%M%S")
    lstm_path=save_lstm(lstm_model,ticker,lstm_version)

    metrics={"tree":tree["metrics"],"lstm":lstm_metrics,
             "walk_forward":"expanding+embargo","corporate_actions":len(actions)}
    weights={"tree":0.45,"lstm":0.35,"finbert":0.20}
    ensemble_version,registry=register_ensemble(ticker,tree["version"],
                                                  f"model_registry/{ticker}_{tree['version']}.joblib",
                                                  lstm_path,metrics,weights)
    return {"ticker":ticker,"bars":len(df),"features":meta,
            "ensemble_version":ensemble_version,"registry":registry,
            "metrics":metrics}


@celery.task
def daily_breaking_news():
    import asyncio, json
    from .news_ai import auto_posts
    from .core import redis
    posts=asyncio.run(auto_posts(5))
    redis.setex("stockmind:breaking-news:daily", 24*60*60, json.dumps(posts))
    return {"count":len(posts),"generated_at":posts[0]["generated_at"] if posts else None}
