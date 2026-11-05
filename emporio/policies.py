"""Reads the policy manual (PDF) and splits it into its numbered sections."""
import re
from functools import lru_cache

from pypdf import PdfReader

from emporio.data import DATA_DIR

MANUAL = DATA_DIR / "políticas_da_loja.pdf"

# Section number in the manual -> key used by the get_policy tool
SECTIONS = {
    "1": "sobre_a_loja",          # about the store, address, phone, e-mail
    "2": "horario",               # opening hours
    "3": "pagamento",             # payment methods and instalments
    "4": "trocas_e_devolucoes",   # returns and exchanges
    "5": "frete_e_entregas",      # shipping and delivery
    "6": "promocoes",             # promotions and discounts
    "7": "atendimento",           # service guidelines
    "8": "garantia",              # warranty
    "9": "privacidade",           # privacy (LGPD)
    "10": "disposicoes_finais",
}

# Notes appended to a section to resolve the contradictions in the manual (docs/inconsistencies.md, items 1 to 3)
NOTES = {
    "sobre_a_loja": "Nota da equipe: telefone da loja (67) 3341-4444; canal de WhatsApp (67) 3321-4500 (seção 7). "
                    "E-mail correto: contato@emporiodamusica.com.br.",
    "atendimento": "Nota da equipe: o canal de WhatsApp é o (67) 3321-4500; o telefone da loja é o (67) 3341-4444.",
    "pagamento": "Nota da equipe: quando a tabela e a seção 3.1 divergem, vale a seção 3.1. "
                 "Compras abaixo de R$ 50,00 não podem ser parceladas.",
}

_NOISE = re.compile(r"^\s*(Página \d+|Empório da Música Manual de Políticas e Procedimentos)\s*$", re.M)
_HEADING = re.compile(r"^(\d{1,2})\. (\S.*)$", re.M)   # top-level headings start at column 0, e.g. "4. Política de ..."


def _clean(text: str) -> str:
    text = _NOISE.sub("", text).replace("empóriodamusica", "emporiodamusica")   # inconsistency 2
    text = re.sub(r"[ \t]{3,}", "  ", text)          # table columns: keep a visible gap, drop the padding
    text = re.sub(r"\n\s*\n+", "\n\n", text)         # collapse blank lines
    return text.strip()


@lru_cache(maxsize=1)
def load_policies() -> dict[str, str]:
    """Returns {section key: section text}. The cover page (before section 1) is dropped: section 1 repeats its data."""
    text = "\n".join(page.extract_text(extraction_mode="layout") for page in PdfReader(MANUAL).pages)
    matches = list(_HEADING.finditer(text))
    sections = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        key = SECTIONS[m.group(1)]
        sections[key] = _clean(text[m.start():end]) + (f"\n\n{NOTES[key]}" if key in NOTES else "")
    return sections
