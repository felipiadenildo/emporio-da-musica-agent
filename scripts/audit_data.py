"""Quick audit of the store data with pandas.

Prints the size, types, value counts and cross-table checks used in docs/data.md and docs/inconsistencies.md.
Run from the repository root:  python scripts/audit_data.py
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
PREFIX = "desafio_tecnico_ai_eng - "
TABLES = ["products", "categories", "promotions", "orders", "order_items", "customers"]

pd.set_option("display.width", 200)
t = {name: pd.read_csv(DATA / f"{PREFIX}{name}.csv") for name in TABLES}

print("== Tables")
for name, df in t.items():
    print(f"{name:12s} rows={len(df):3d}  nulls={int(df.isna().sum().sum()):3d}  duplicated rows={int(df.duplicated().sum())}"
          f"  columns={list(df.columns)}")

products, categories, promotions = t["products"], t["categories"], t["promotions"]
orders, items, customers = t["orders"], t["order_items"], t["customers"]

print("\n== Products")
print("status:", products.status.value_counts().to_dict())
print("active with stock 0:", products.query("status == 'active' and stock_quantity == 0").product_id.tolist())
print("products per category:", products.groupby("category_id").size().to_dict())
print("categories without products:",
      categories.loc[~categories.category_id.isin(products.category_id), ["category_id", "name"]].values.tolist())
print("price range: R$ %.2f to R$ %.2f" % (products.price_brl.min(), products.price_brl.max()))
print("unique names:", products.name.is_unique, "| unique ids:", products.product_id.is_unique)

print("\n== Promotions")
print("active (is_active=1):", promotions.query("is_active == 1")[["product_id", "discount_percent", "description"]].values.tolist())
print("products with more than one promotion row:", promotions.product_id.value_counts().loc[lambda s: s > 1].to_dict())
print("promotions on unknown products:", sorted(set(promotions.product_id) - set(products.product_id)))

print("\n== Orders")
print("status:", orders.status.value_counts().to_dict())
print("order date range:", orders.order_date.min(), "to", orders.order_date.max())
print("orders with tracking code by status:", orders.dropna(subset=["tracking_code"]).status.value_counts().to_dict())
lines = items.merge(products[["product_id", "price_brl", "status"]], on="product_id", how="left")
lines["subtotal"] = lines.quantity * lines.price_brl
check = orders.merge(lines.groupby("order_id").subtotal.sum().rename("items_total"), on="order_id")
mismatch = check.loc[(check.total_brl - check.items_total).abs() > 0.01, ["order_id", "status", "total_brl", "items_total"]]
print("orders whose total differs from the sum of the items:\n", mismatch.to_string(index=False))
print("orders containing products not active:",
      lines.loc[lines.status != "active", ["order_id", "product_id", "status"]].values.tolist())
print("items with unknown product:", int(lines.price_brl.isna().sum()),
      "| orders with unknown customer:", int((~orders.customer_id.isin(customers.customer_id)).sum()))

print("\n== Customers")
print("cities:", customers.city.value_counts().to_dict())
print("unique e-mail:", customers.email.is_unique, "| unique phone:", customers.phone.is_unique)
