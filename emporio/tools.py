"""Tools the agent can call: catalogue, policies, customer identification and orders (see docs/decisions.md, D1 and D5).

Each tool returns a small dict that is sent back to the model as JSON. The identified customer lives in `Session`, in
code: the order tool only reads orders of that customer, whatever the model asks for.
"""
import difflib
import os
from dataclasses import dataclass, field
from datetime import date

from emporio.data import digits, load_store, normalize
from emporio.policies import SECTIONS, load_policies

MAX_RESULTS = 8

STOCK_STATUS = {"active": "disponível", "coming_soon": "em breve (ainda não disponível)",
                "discontinued": "descontinuado (fora do catálogo)"}
ORDER_STATUS = {"delivered": "entregue", "shipped": "enviado (em transporte)", "confirmed": "confirmado (em separação)",
                "pending": "pendente (aguardando confirmação do pagamento)", "cancelled": "cancelado"}
PAYMENT = {"pix": "PIX", "debit": "cartão de débito", "boleto": "boleto bancário"}


def today() -> date:
    """Real current date, or AGENT_TODAY=YYYY-MM-DD to demonstrate date-based rules (docs/inconsistencies.md, item 9)."""
    value = os.getenv("AGENT_TODAY")
    return date.fromisoformat(value) if value else date.today()


@dataclass
class Session:
    customer_id: int | None = None
    calls: list = field(default_factory=list)   # (tool name, arguments, result), for --debug and transcripts


# ----------------------------------------------------------------------------------------------- catalogue
def _product_summary(row) -> dict:
    out = {"id": int(row.product_id), "nome": row.name, "categoria": row.category,
           "preco": float(row.price_brl), "estoque": int(row.stock_quantity)}
    if row.status != "active":
        out["situacao"] = STOCK_STATUS[row.status]
    elif row.stock_quantity == 0:
        out["situacao"] = "sem estoque no momento"
    if row.discount_percent:
        out.update(promocao=row.promotion, desconto_percentual=int(row.discount_percent),
                   preco_promocional=float(row.current_price))
    return out


def search_products(query: str = "", category: str = "", max_price: float | None = None,
                    only_available: bool = True) -> dict:
    p = load_store().products
    if category:
        p = p[p.category.map(normalize) == normalize(category)]
    if query:
        tokens = normalize(query).split()
        hits = p[p.search_text.map(lambda t: all(tok in t for tok in tokens))]
        if hits.empty:   # tolerate small typos in a model name ("takamine gd 20")
            close = difflib.get_close_matches(normalize(query), p.name.map(normalize).tolist(), n=3, cutoff=0.6)
            hits = p[p.name.map(normalize).isin(close)]
        p = hits
    if max_price is not None:
        p = p[p.current_price <= max_price]
    if only_available:
        p = p[(p.status == "active") & (p.stock_quantity > 0)]
    p = p.sort_values("current_price")
    return {"total_encontrado": len(p), "produtos": [_product_summary(r) for r in p.head(MAX_RESULTS).itertuples()],
            "observacao": "lista limitada aos mais baratos" if len(p) > MAX_RESULTS else ""}


def get_product(product_id: int) -> dict:
    p = load_store().products
    row = p[p.product_id == int(product_id)]
    if row.empty:
        return {"erro": f"produto {product_id} não encontrado"}
    r = next(row.itertuples())
    return {**_product_summary(r), "descricao": r.description, "especificacoes": r.specs}


def get_policy(section: str) -> dict:
    policies = load_policies()
    if section not in policies:
        return {"erro": f"seção desconhecida; use uma de: {', '.join(policies)}"}
    return {"secao": section, "texto": policies[section]}


# ----------------------------------------------------------------------------------------------- customer
def identify_customer(session: Session, phone: str) -> dict:
    number = digits(phone)
    if number.startswith("55") and len(number) > 11:   # +55 country code
        number = number[2:]
    customers = load_store().customers
    match = customers[customers.phone_digits == number]
    if len(number) < 10 or match.empty:
        return {"identificado": False, "motivo": "telefone não encontrado no cadastro"}
    c = next(match.itertuples())
    session.customer_id = int(c.customer_id)
    return {"identificado": True, "primeiro_nome": c.name.split()[0]}


def get_my_orders(session: Session, order_id: int | None = None) -> dict:
    if session.customer_id is None:
        return {"erro": "cliente não identificado: peça o telefone do cadastro e use identify_customer antes"}
    store = load_store()
    orders = store.orders[store.orders.customer_id == session.customer_id]
    if order_id is not None:
        orders = orders[orders.order_id == int(order_id)]
        if orders.empty:   # same answer whether the order doesn't exist or belongs to someone else
            return {"erro": f"não há pedido {order_id} no cadastro deste cliente"}
    names = store.products.set_index("product_id").name
    ref = today()
    result = []
    for o in orders.sort_values("order_date", ascending=False).itertuples():
        items = store.order_items[store.order_items.order_id == o.order_id]
        payment = PAYMENT.get(o.payment_method) or o.payment_method.replace("credit_", "cartão de crédito em ")
        entry = {"pedido": int(o.order_id), "data_compra": o.order_date, "status": ORDER_STATUS[o.status],
                 "total": float(o.total_brl), "pagamento": payment,
                 "itens": [f"{int(i.quantity)}x {names[i.product_id]}" for i in items.itertuples()],
                 "dias_desde_a_compra": (ref - date.fromisoformat(o.order_date)).days}
        if isinstance(o.tracking_code, str):
            entry["rastreio"] = o.tracking_code
        if isinstance(o.estimated_delivery, str):
            entry["entrega_estimada"] = o.estimated_delivery
            if o.status == "delivered":   # no real receipt date in the data (docs/inconsistencies.md, item 4)
                entry["dias_desde_a_entrega_estimada"] = (ref - date.fromisoformat(o.estimated_delivery)).days
        if isinstance(o.notes, str):
            entry["observacao"] = o.notes
        result.append(entry)
    return {"data_de_hoje": ref.isoformat(), "pedidos": result}


# ----------------------------------------------------------------------------------------------- schemas
CATEGORIES = sorted(load_store().categories.name.tolist())

TOOLS = [
    {"type": "function", "function": {
        "name": "search_products",
        "description": "Busca instrumentos no catálogo da loja, com preço atual (já com promoção ativa) e estoque. "
                       "Use para qualquer pergunta sobre produtos, preços, modelos ou disponibilidade.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "palavras do nome ou modelo, ex.: 'takamine', 'yamaha c40'. "
                                                       "Vazio para listar uma categoria."},
            "category": {"type": "string", "enum": CATEGORIES},
            "max_price": {"type": "number", "description": "preço máximo em R$"},
            "only_available": {"type": "boolean", "description": "só produtos à venda e com estoque (padrão: true)"}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "get_product",
        "description": "Detalhes de um produto (descrição e especificações) pelo id retornado em search_products.",
        "parameters": {"type": "object", "properties": {"product_id": {"type": "integer"}}, "required": ["product_id"]}}},
    {"type": "function", "function": {
        "name": "get_policy",
        "description": "Retorna uma seção do manual de políticas da loja. Use para endereço, contatos, horários, "
                       "pagamento e parcelamento, trocas e devoluções, frete, promoções, garantia e privacidade.",
        "parameters": {"type": "object", "properties": {"section": {"type": "string", "enum": list(SECTIONS.values())}},
                       "required": ["section"]}}},
    {"type": "function", "function": {
        "name": "identify_customer",
        "description": "Identifica o cliente pelo telefone do cadastro. Obrigatório antes de falar de pedidos.",
        "parameters": {"type": "object", "properties": {"phone": {"type": "string", "description": "telefone com DDD"}},
                       "required": ["phone"]}}},
    {"type": "function", "function": {
        "name": "get_my_orders",
        "description": "Pedidos do cliente identificado: status, itens, datas, rastreio. Sem order_id, lista todos.",
        "parameters": {"type": "object", "properties": {"order_id": {"type": "integer"}}, "required": []}}},
]


def run_tool(session: Session, name: str, args: dict) -> dict:
    """Dispatches a tool call from the model. Errors become a message for the model, never a crash."""
    try:
        if name == "identify_customer":
            return identify_customer(session, **args)
        if name == "get_my_orders":
            return get_my_orders(session, **args)
        functions = {"search_products": search_products, "get_product": get_product, "get_policy": get_policy}
        return functions[name](**args)
    except Exception as exc:   # bad arguments from the model
        return {"erro": f"falha ao executar {name}: {exc}"}
