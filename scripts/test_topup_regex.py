import re

HTML = """
<p class="m-0 text-gray">Saldo de recargas: 231,3 GB</p>
"""

match = re.search(r"Saldo de recargas[:\s]*([^\n<]+)", HTML, re.IGNORECASE)
print("Match:", match.group(1).strip() if match else None)
