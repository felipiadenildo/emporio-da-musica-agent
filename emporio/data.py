"""Loads the store CSV files once and applies the light treatment described in docs/data.md."""
import json
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PREFIX = "desafio_tecnico_ai_eng - "


def normalize(text: str) -> str:
    """Lower case without accents, so 'Violão' and 'violao' match."""
    text = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


def digits(text: str) -> str:
    """Only the digits of a phone number: '(67) 99812-3456' -> '67998123456'."""
    return "".join(c for c in str(text) if c.isdigit())


@dataclass
class Store:
    products: pd.DataFrame     # one row per product, with category name, specs and current price
    customers: pd.DataFrame
    orders: pd.DataFrame
    order_items: pd.DataFrame
    categories: pd.DataFrame


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / f"{PREFIX}{name}.csv")


@lru_cache(maxsize=1)
def load_store() -> Store:
    categories = _read("categories")
    products = _read("products").merge(
        categories[["category_id", "name"]].rename(columns={"name": "category"}), on="category_id", how="left")
    products["specs"] = products["specs"].apply(json.loads)

    # Current price: only promotions with is_active = 1 count (manual 7.3). There is at most one active per product.
    active = _read("promotions").query("is_active == 1")[["product_id", "discount_percent", "description"]]
    products = products.merge(active.rename(columns={"description": "promotion"}), on="product_id", how="left")
    products["discount_percent"] = products["discount_percent"].fillna(0).astype(int)
    products["current_price"] = (products["price_brl"] * (1 - products["discount_percent"] / 100)).round(2)
    products["search_text"] = (products["name"] + " " + products["category"]).map(normalize)

    customers = _read("customers")
    customers["phone_digits"] = customers["phone"].map(digits)

    return Store(products=products, customers=customers, orders=_read("orders"),
                 order_items=_read("order_items"), categories=categories)
