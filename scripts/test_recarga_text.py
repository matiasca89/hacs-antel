import re

card_text = """ZU3367 

Fibra con límite 1

Me quedan

0 GB

Llegaste al límite de tu plan.

Fin de contrato: 26/11/2027

Recarga datos
Me quedan
224,6 GB
Vence el 15 de febrero 2026
"""

# Balance patterns
balance_match = re.search(r"Saldo de recargas[\.:]?\s*([\d.,]+)\s*GB", card_text, re.IGNORECASE)
if not balance_match:
    balance_match = re.search(r"Recarga datos.*?Me quedan\s*([\d.,]+)\s*GB", card_text, re.IGNORECASE | re.DOTALL)

# Expiration patterns
exp_match = re.search(r"Vence el\s*(\d{1,2}/\d{1,2}/\d{4})", card_text, re.IGNORECASE)
if not exp_match:
    exp_match = re.search(r"Vence el\s*(\d{1,2}\s+de\s+\w+(?:\s+\d{4})?)", card_text, re.IGNORECASE)

print("Balance:", balance_match.group(1) if balance_match else None)
print("Expira:", exp_match.group(1) if exp_match else None)
