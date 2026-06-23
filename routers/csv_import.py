import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from database.db import SessionLocal
from models.shop_model import Shop, ImportedOrder, ImportedProduct, CSVImportLog

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _float(val) -> float:
    try:
        return float(str(val).replace(",", "").strip() or 0)
    except (ValueError, TypeError):
        return 0.0


def _int(val) -> int:
    try:
        return int(str(val).replace(",", "").strip() or 0)
    except (ValueError, TypeError):
        return 0


def _decode(content_bytes: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return content_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return content_bytes.decode("latin-1", errors="replace")


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_orders_csv(content: str) -> tuple:
    """
    Shopify orders export has one row per line-item.
    Order-level fields (Name, Total, Created at) appear only on the first row per order.
    Returns (list[dict], list[str errors])
    """
    errors = []
    orders = {}

    try:
        reader = csv.DictReader(io.StringIO(content))
    except Exception as e:
        return [], [f"CSV read error: {e}"]

    for i, row in enumerate(reader, start=2):
        try:
            name = row.get("Name", "").strip()
            if not name:
                continue

            if name not in orders:
                orders[name] = {
                    "order_name": name,
                    "created_at": row.get("Created at", "").strip(),
                    "financial_status": (row.get("Financial Status") or "paid").strip().lower(),
                    "currency": (row.get("Currency") or "INR").strip(),
                    "total_price": _float(row.get("Total", "0")),
                    "line_items": [],
                }

            title = row.get("Lineitem name", "").strip()
            qty = _int(row.get("Lineitem quantity", "1"))
            price = _float(row.get("Lineitem price", "0"))

            if title:
                orders[name]["line_items"].append({
                    "title": title,
                    "quantity": qty,
                    "price": price,
                    "sku": row.get("Lineitem sku", "").strip(),
                    "vendor": row.get("Vendor", "").strip(),
                    "revenue": round(qty * price, 2),
                })
        except Exception as e:
            errors.append(f"Row {i}: {e}")

    return list(orders.values()), errors


def parse_products_csv(content: str) -> tuple:
    """
    Shopify products export has one row per variant.
    Title/Vendor appear only on the first row per Handle.
    Returns (list[dict], list[str errors])
    """
    errors = []
    products = {}

    try:
        reader = csv.DictReader(io.StringIO(content))
    except Exception as e:
        return [], [f"CSV read error: {e}"]

    for i, row in enumerate(reader, start=2):
        try:
            handle = row.get("Handle", "").strip()
            if not handle:
                continue

            if handle not in products:
                title = row.get("Title", "").strip() or handle
                products[handle] = {
                    "handle": handle,
                    "title": title,
                    "vendor": row.get("Vendor", "").strip(),
                    "product_type": row.get("Type", "").strip(),
                    "sku": row.get("Variant SKU", "").strip(),
                    "price": _float(row.get("Variant Price", "0")),
                    "cost_per_item": _float(row.get("Cost per item", "0")),
                    "inventory_qty": _int(row.get("Variant Inventory Qty", "0")),
                }
            else:
                # Additional variants — sum inventory
                products[handle]["inventory_qty"] += _int(row.get("Variant Inventory Qty", "0"))
        except Exception as e:
            errors.append(f"Row {i}: {e}")

    return list(products.values()), errors


# ── Upload endpoint ───────────────────────────────────────────────────────────

@router.post("/csv/upload")
async def upload_csv(
    file: UploadFile = File(...),
    shop: str = Form(...),
    import_type: str = Form(...),
):
    if import_type not in ("orders", "products"):
        raise HTTPException(400, "import_type must be 'orders' or 'products'")

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only .csv files are accepted")

    raw = await file.read()
    content = _decode(raw)

    db = SessionLocal()
    try:
        # Ensure shop row exists (CSV-only shops have no access_token)
        shop_rec = db.query(Shop).filter(Shop.shop_domain == shop).first()
        if not shop_rec:
            shop_rec = Shop(
                shop_domain=shop,
                platform="shopify",
                access_token=None,
                shop_name=shop,
            )
            db.add(shop_rec)
            db.flush()

        if import_type == "orders":
            records, errors = parse_orders_csv(content)
            db.query(ImportedOrder).filter(ImportedOrder.shop_domain == shop).delete()

            saved = 0
            for o in records:
                try:
                    db.add(ImportedOrder(
                        shop_domain=shop,
                        order_name=o["order_name"],
                        created_at=o["created_at"],
                        financial_status=o["financial_status"],
                        currency=o["currency"],
                        total_price=o["total_price"],
                        line_items_json=json.dumps(o["line_items"], ensure_ascii=False),
                    ))
                    saved += 1
                except Exception as e:
                    errors.append(str(e))

            db.add(CSVImportLog(
                shop_domain=shop,
                import_type="orders",
                file_name=file.filename,
                total_rows=len(records),
                success_rows=saved,
                error_rows=len(errors),
                status="success" if not errors else "partial",
            ))
            db.commit()

            return {
                "status": "success" if not errors else "partial",
                "import_type": "orders",
                "imported": saved,
                "errors": errors[:5],
                "message": f"{saved} orders imported successfully",
            }

        else:  # products
            records, errors = parse_products_csv(content)
            db.query(ImportedProduct).filter(ImportedProduct.shop_domain == shop).delete()

            saved = 0
            for p in records:
                try:
                    db.add(ImportedProduct(
                        shop_domain=shop,
                        handle=p["handle"],
                        title=p["title"],
                        vendor=p["vendor"],
                        product_type=p["product_type"],
                        sku=p["sku"],
                        price=p["price"],
                        cost_per_item=p["cost_per_item"],
                        inventory_qty=p["inventory_qty"],
                    ))
                    saved += 1
                except Exception as e:
                    errors.append(str(e))

            db.add(CSVImportLog(
                shop_domain=shop,
                import_type="products",
                file_name=file.filename,
                total_rows=len(records),
                success_rows=saved,
                error_rows=len(errors),
                status="success" if not errors else "partial",
            ))
            db.commit()

            return {
                "status": "success" if not errors else "partial",
                "import_type": "products",
                "imported": saved,
                "errors": errors[:5],
                "message": f"{saved} products imported successfully",
            }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


# ── Status endpoint ───────────────────────────────────────────────────────────

@router.get("/csv/import-status")
def get_import_status(shop: str):
    db = SessionLocal()
    try:
        logs = (
            db.query(CSVImportLog)
            .filter(CSVImportLog.shop_domain == shop)
            .order_by(CSVImportLog.imported_at.desc())
            .limit(5)
            .all()
        )
        orders_count = db.query(ImportedOrder).filter(ImportedOrder.shop_domain == shop).count()
        products_count = db.query(ImportedProduct).filter(ImportedProduct.shop_domain == shop).count()

        return {
            "shop": shop,
            "imported_orders": orders_count,
            "imported_products": products_count,
            "history": [
                {
                    "type": l.import_type,
                    "file": l.file_name,
                    "imported": l.success_rows,
                    "status": l.status,
                    "at": l.imported_at.isoformat() if l.imported_at else None,
                }
                for l in logs
            ],
        }
    finally:
        db.close()


# ── Fallback data helpers (called by api.py when live API fails) ─────────────

def get_csv_sales_intelligence(shop_domain: str) -> dict:
    db = SessionLocal()
    try:
        orders = (
            db.query(ImportedOrder)
            .filter(ImportedOrder.shop_domain == shop_domain)
            .all()
        )

        if not orders:
            return {
                "gross_sales": 0, "net_revenue": 0,
                "total_orders": 0, "avg_order_value": 0,
                "data_source": "csv_empty",
            }

        paid = [o for o in orders if o.financial_status in ("paid", "partially_paid", "")]
        total = len(paid)
        gross = sum(o.total_price for o in paid)

        return {
            "gross_sales": round(gross, 2),
            "net_revenue": round(gross, 2),
            "total_orders": total,
            "avg_order_value": round(gross / total, 2) if total else 0,
            "data_source": "csv",
        }
    finally:
        db.close()


def get_csv_top_products(shop_domain: str, limit: int = 5) -> dict:
    db = SessionLocal()
    try:
        orders = (
            db.query(ImportedOrder)
            .filter(ImportedOrder.shop_domain == shop_domain)
            .all()
        )

        agg = {}
        for order in orders:
            if order.financial_status not in ("paid", "partially_paid", ""):
                continue
            for item in json.loads(order.line_items_json or "[]"):
                title = item.get("title", "Unknown")
                if title not in agg:
                    agg[title] = {
                        "title": title,
                        "sku": item.get("sku", ""),
                        "vendor": item.get("vendor", ""),
                        "units_sold": 0,
                        "revenue": 0.0,
                        "image": None,
                    }
                agg[title]["units_sold"] += item.get("quantity", 0)
                agg[title]["revenue"] += item.get("revenue", 0.0)

        top = sorted(agg.values(), key=lambda x: x["revenue"], reverse=True)[:limit]
        for p in top:
            p["revenue"] = round(p["revenue"], 2)

        return top
    finally:
        db.close()
