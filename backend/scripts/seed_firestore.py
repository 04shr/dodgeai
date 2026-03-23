"""
Seed Firestore
==============
Uploads processed data to Firestore on first deploy.

Usage:
    cd backend
    python scripts/seed_firestore.py

Requires FIREBASE_CREDENTIALS_PATH to be set in .env
or a firebase-service-account.json in backend/.
"""
import json, sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("seed")

from app.config import DATA_DIR, FIREBASE_ENABLED
from app.services.firebase_service import get_db


def seed():
    if not FIREBASE_ENABLED:
        log.error("Firebase credentials not found. Set FIREBASE_CREDENTIALS_PATH in .env")
        sys.exit(1)

    db = get_db()
    if not db:
        log.error("Could not connect to Firestore.")
        sys.exit(1)

    from firebase_admin import firestore

    # ── KPI summary ──────────────────────────────────────
    log.info("Seeding kpi_summary…")
    with open(DATA_DIR / "kpi_summary.json") as f:
        kpis = json.load(f)
    db.collection("kpis").document("summary").set(kpis)
    log.info("  ✓ kpi_summary")

    # ── Customer KPIs ─────────────────────────────────────
    log.info("Seeding customer_kpis…")
    with open(DATA_DIR / "customer_kpis.json") as f:
        customers = json.load(f)
    batch = db.batch()
    for c in customers:
        ref = db.collection("customers").document(c["customer_id"])
        batch.set(ref, c)
    batch.commit()
    log.info(f"  ✓ {len(customers)} customers")

    # ── Order summaries (first 100) ───────────────────────
    log.info("Seeding order summaries…")
    import pandas as pd
    import numpy as np
    orders = pd.read_csv(DATA_DIR / "unified_o2c_orders.csv")
    orders = orders.replace({np.nan: None})

    batch = db.batch()
    for _, row in orders.iterrows():
        doc = {k: (None if (isinstance(v, float) and v != v) else v)
               for k, v in row.to_dict().items()}
        ref = db.collection("orders").document(str(doc["sales_order_id"]))
        batch.set(ref, doc)
        if len(batch._write_pbs) >= 400:   # Firestore batch limit = 500
            batch.commit()
            batch = db.batch()
    batch.commit()
    log.info(f"  ✓ {len(orders)} orders")

    log.info("\nAll data seeded successfully ✓")


if __name__ == "__main__":
    seed()
