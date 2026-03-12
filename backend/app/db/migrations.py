from sqlalchemy import text


def ensure_deal_columns(engine):
    with engine.begin() as conn:
        info = conn.execute(text("PRAGMA table_info(deals)")).fetchall()
        existing = {row[1] for row in info}
        if "ai_payload" not in existing:
            conn.execute(text("ALTER TABLE deals ADD COLUMN ai_payload TEXT"))
