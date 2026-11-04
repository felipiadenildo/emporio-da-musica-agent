# Inconsistencies in the store material

While checking the data ([data.md](data.md)) and reading the policy manual, I found contradictions and gaps. I treat
them as **errors in how the problem material was put together**: the kind of thing a real store would fix in its own
systems, not something the agent should try to repair. The statement asks to "assume a reasonable interpretation,
document it and move on", so each item below has the simplest handling that keeps the agent's answers correct and
honest, at the lowest cost to the project.

The handling follows three rules:
1. **The CSV tables are the source of truth** for prices, stock, promotions and orders. **The manual is the source of
   truth** for rules.
2. When two sources disagree and one is more specific, **use the more specific one**.
3. When a question can't be answered with certainty, the agent **says what it knows and hands over to the team**
   instead of guessing.

## Summary

| # | Where | Inconsistency | Handling |
|---|---|---|---|
| 1 | Manual | two phone numbers | both shown, each for its channel |
| 2 | Manual | two spellings of the e-mail | spelling without the accent |
| 3 | Manual | instalment rules contradict | section 3.1 (more detailed) is applied |
| 4 | Manual × data | return window counts from receipt, data has no receipt date | estimated delivery used as a reference, final check by the team |
| 5 | Manual × data | manual lists categories the catalogue doesn't have | catalogue wins: "no products in this category right now" |
| 6 | Data | order totals differ from the sum of their items | the order total (what was charged) is shown; not explained to the customer |
| 7 | Data | two customers share an e-mail | identification needs e-mail **and** phone |
| 8 | Data | orders with a product still marked `coming_soon` | order status is reported as it is; product status only affects the catalogue |
| 9 | Data | dates in the data end in March 2026 | the agent uses the real current date |
| 10 | Manual | "suggest partner stores" for accessories, but none is named | no store is suggested; the agent just explains the store only sells instruments |

## Details

### 1. Two phone numbers
The cover and section 1.2 ("Telefone / WhatsApp") give **(67) 3341-4444**. Section 7 says the WhatsApp channel is
**(67) 3321-4500**.
**Handling:** each source names a channel, so both can be right. The agent gives (67) 3341-4444 as the store phone and
(67) 3321-4500 as the WhatsApp channel. Cost: none.

### 2. Two spellings of the e-mail
The cover has `contato@emporiodamusica.com.br`; section 1.2 has `contato@empóriodamusica.com.br` (with an accent, which is
unusual in a domain and most likely a typo).
**Handling:** the spelling without the accent is used.

### 3. Instalment rules contradict
The table in section 3 says "credit card up to 12x, minimum instalment R$ 100". Section 3.1 gives three tiers: up to 3x
with no minimum ("except below R$ 50", which is itself unclear), 4x to 6x with a minimum of R$ 80, and 7x to 12x with a
minimum of R$ 100.
**Handling:** section 3.1 is applied because it is the detailed rule. "Except below R$ 50" is read as "purchases below
R$ 50 can't be split". When a customer asks, the agent states the tier that applies, and if the case is borderline it
suggests confirming with the team.

### 4. Return window and delivery date
The right of withdrawal (section 4.1) counts 7 days **from receipt**. The orders table only has `estimated_delivery`,
not the actual delivery date.
**Handling:** for delivered orders, the estimated delivery date is used as the reference, and the agent says so. It
explains the rule and the estimated deadline, and the request itself is confirmed by the team, which knows the real
receipt date. The same applies to the 30-day defect exchange, which counts from the purchase date (`order_date`).

### 5. Categories in the manual that the catalogue doesn't have
The manual says the store has "more than 300 instruments", including wind instruments and orchestral strings. The
catalogue has 65 products and none in categories 6, 7 and 8 (woodwind, brass, orchestral strings).
**Handling:** the catalogue is the source of truth. If a customer asks for a saxophone, the agent says there are no
products in that category right now and offers to pass the request to the team. It never invents a product.

### 6. Order totals that don't match the items
Order 3 (delivered) has a total of R$ 3,450.00, but its items add up to R$ 3,498.00. Order 20 (cancelled) has R$ 1,400.00
against R$ 1,488.00. A discount not recorded in the data is a likely explanation, but there is no evidence of it.
**Handling:** the agent shows `total_brl`, which is what the customer was charged, and the item list without unit
prices. The difference is documented here and not explained to the customer, because any explanation would be invented.

### 7. Two customers share an e-mail
Customers 11 and 43 have the same e-mail address (`bruno.martins@jmail.com`) and different phones.
**Handling:** an e-mail alone can't identify a customer. Before showing any personal data, the agent asks for the
**e-mail and the phone**, and both must belong to the same customer. This finding shapes how the agent identifies a
customer.

### 8. Orders with a product marked `coming_soon`
Orders 3 (delivered) and 14 (pending) contain product 130, whose status is `coming_soon`.
**Handling:** the order status is reported as it is in the orders table. The product status only matters in catalogue
answers (the product is not offered as available).

### 9. Dates
The orders go from October 2025 to March 2026, while the agent runs later.
**Handling:** the agent uses the real current date. As a result, every delivered order is past the 7-day and 30-day
windows, and that is the correct answer to give. The date can be fixed with an environment variable to demonstrate other
cases.

### 10. Partner stores
Section 7.1 asks to "suggest partner stores when possible" for accessories, but the manual names none.
**Handling:** the agent doesn't suggest any store. It explains, politely, that the store only sells instruments.
