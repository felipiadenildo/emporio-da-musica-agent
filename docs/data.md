# Data available

What the store provided, what each part is used for, and how it was checked. All numbers below come from
[`scripts/audit_data.py`](../scripts/audit_data.py) (pandas), which can be run again at any time:

```bash
python scripts/audit_data.py
```

## Files

| File | Rows | What it holds | Used by the agent for |
|---|---|---|---|
| `products.csv` | 65 | id, name, price (R$), category, description, stock, status, specs (JSON text), creation date | catalogue search, price, stock |
| `categories.csv` | 9 | id, name, description | filtering and naming categories |
| `promotions.csv` | 25 | product, discount %, campaign name, `is_active` flag | current price of a product |
| `orders.csv` | 20 | customer, date, status, total, payment method, tracking code, estimated delivery, notes | order status (identified customer only) |
| `order_items.csv` | 22 | order, product, quantity | items of an order |
| `customers.csv` | 50 | name, phone, e-mail, city | identifying the customer before showing an order |
| `políticas_da_loja.pdf` | 8 pages | internal policy manual: store data, hours, payment, returns, shipping, promotions, service guidelines, warranty, privacy | answers about rules, and the agent's tone and service flow |

The CSV names keep the prefix they were received with (`desafio_tecnico_ai_eng - <table>.csv`).

## What the checks found

**Structure.** No duplicated rows. The only empty values are in `orders` (40 cells), and they are expected:
`tracking_code` and `estimated_delivery` only exist for orders already shipped, and `notes` is only filled for
cancelled ones. Every order item points to an existing product and every order to an existing customer.

**Products.** 62 `active`, 2 `discontinued`, 1 `coming_soon`. One active product has no stock (id 96). Prices go from
R$ 159.90 to R$ 19,567.00. Names and ids are unique. Products exist in 6 of the 9 categories (35 of them are violões,
15 ukuleles).

**Promotions.** 25 rows, but only 4 are active (`is_active = 1`): products 127 (10%), 121 (20%), 90 (18%) and 94 (8%).
Three products have more than one promotion row (93, 96, 99), all inactive.

**Orders.** 7 delivered, 1 shipped, 4 confirmed, 4 pending, 4 cancelled, dated from 2025-10-15 to 2026-03-22. Only
delivered and shipped orders have a tracking code.

**Customers.** 50 customers in 5 cities of Mato Grosso do Sul (24 in Campo Grande). Phones are unique, **e-mails are
not**: two different customers share one e-mail address. This matters for identification (see
[inconsistencies](inconsistencies.md#7-two-customers-share-an-e-mail)).

The problems found are listed, with how each one is handled, in [inconsistencies.md](inconsistencies.md).

## How the data is treated

The data is small (a few hundred rows), so it is loaded once into memory with pandas when the agent starts. No database
is needed. The treatment is only what the answers need:
- join the category name to each product and read the `specs` JSON;
- compute the current price from the active promotion, keeping the original price and the percentage;
- search names ignoring accents and upper/lower case, so "takamine gd20" finds "Takamine GD20";
- split the policy manual into its numbered sections, so the agent can look up one section at a time.
