"""Tests for the rules where a mistake would harm a customer or the store (docs/decisions.md, D11). No LLM calls."""
from emporio.policies import load_policies
from emporio.tools import Session, get_my_orders, get_product, identify_customer, search_products


def test_active_promotion_gives_promotional_price():
    crafter = get_product(90)                       # 18% off, is_active = 1
    assert crafter["preco"] == 2399.0
    assert crafter["desconto_percentual"] == 18
    assert crafter["preco_promocional"] == 1967.18


def test_inactive_promotion_is_ignored():
    takamine = search_products(query="Takamine GD20")["produtos"][0]   # only has an inactive promotion
    assert takamine["preco"] == 2199.0 and "preco_promocional" not in takamine


def test_orders_require_identification():
    assert "erro" in get_my_orders(Session())


def test_customer_only_sees_own_orders():
    session = Session()
    assert identify_customer(session, "(67) 98432-1098")["identificado"]   # customer 3
    assert [o["pedido"] for o in get_my_orders(session)["pedidos"]] == [19, 1]
    assert "erro" in get_my_orders(session, order_id=2)                   # order 2 belongs to customer 7


def test_unknown_phone_is_not_identified():
    session = Session()
    assert not identify_customer(session, "(67) 91111-2222")["identificado"]
    assert session.customer_id is None


def test_policy_manual_has_all_sections():
    policies = load_policies()
    assert len(policies) == 10 and "09:00" in policies["horario"]
