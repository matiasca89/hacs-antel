import re

card_text = "Saldo de recargas. 228,0 GB Vence el 15/02/2026"

balance_match = re.search(r"Saldo de recargas[\.:]?\s*([\d.,]+)\s*GB", card_text, re.IGNORECASE)
exp_match = re.search(r"Vence el\s*(\d{1,2}/\d{1,2}/\d{4})", card_text, re.IGNORECASE)

print("Balance:", balance_match.group(1) if balance_match else None)
print("Expira:", exp_match.group(1) if exp_match else None)
