import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "antel_addon"))

try:
    from antel_pkg.antel_scraper import AntelScraper
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), "antel_addon"))
    from antel_pkg.antel_scraper import AntelScraper

# Messy HTML with nested tags, newlines, and hidden classes
HTML_MESSY = """
<html>
<body class="dashboard">
  <div class="header">...</div>
  
  <!-- Service Card with extra nesting -->
  <div class="servicioBox internet active">
     <div class="inner-box">
         <span class="value-data">
            145,6
         </span>
         <span class="value-data">GB</span>
         
         <!-- Progress bars with extra whitespace -->
         <div class="progress-bar__label">
             Consumidos 
             104,4 
             GB
         </div>
         <div class="progress-bar__label">
             Incluido 250 GB
         </div>
         
         <div class="plan-title">
             Fibra con límite 1
         </div>
     </div>
  </div>

  <!-- Mobile footer with deep nesting and attributes -->
  <div class="card-footer-extra">
    <div class="row d-md-none" style="display:none;">
        <div class="col">
            <p class="m-0 text-gray">
               Ciclo actual: <span>1 de enero</span> al <span>31 de enero</span>
            </p>
            <p class="m-0 text-gray">
               Quedan <strong>12</strong> días para renovar
            </p>
        </div>
    </div>
  </div>
  
  <!-- Contract end with random tags -->
  <footer>
     <p>Fin de contrato: <span class="highlight">26/11/2027</span></p>
  </footer>
</body>
</html>
"""

class MockLocator:
    def __init__(self, text_val=""):
        self._text = text_val
    def filter(self, **kwargs): return self
    @property
    def first(self): return self
    async def count(self): return 1
    async def text_content(self): return self._text
    
    def locator(self, selector):
        # Simulate whitespace in extraction
        if "value-data" in selector and "+" not in selector:
            return MockLocator("145,6")
        if "value-data + small" in selector:
            return MockLocator("GB")
        if "Consumidos" in selector:
            # Simulate multiline text return
            return MockLocator("Consumidos \n 104,4 \n GB")
        if "Incluido" in selector:
            return MockLocator("Incluido 250 GB")
        if "plan-title" in selector:
            return MockLocator("Fibra con límite 1")
        return MockLocator("")

class MockPage:
    async def wait_for_load_state(self, *args, **kwargs): pass
    async def content(self): return HTML_MESSY
    def locator(self, selector): return MockLocator()
    async def title(self): return "Mi Antel - Dashboard"
    @property
    def url(self): return "https://antel.com.uy/dashboard"

async def run_advanced_test():
    print("Running ADVANCED Extraction Test (Messy HTML)...")
    scraper = AntelScraper("test", "test", service_id="Fibra")
    page = MockPage()
    
    try:
        data = await scraper._extract_consumption_data(page)
        
        print(f"\nResults:")
        print(f"Used: {data.used_data_gb} GB")
        print(f"Total: {data.total_data_gb} GB")
        print(f"Renewal Days: {data.days_until_renewal}")
        print(f"Contract End: {data.contract_end_date}")
        
        # Validation logic
        if data.used_data_gb == 104.4:
            print("✅ Used Data handled whitespace correctly")
        else:
            print(f"❌ Used Data failed: {data.used_data_gb}")

        # The regex for renewal days might fail with <strong> tags if not robust
        if data.days_until_renewal == 12:
            print("✅ Renewal Days extracted despite <strong> tags")
        else:
            print(f"❌ Renewal Days failed: {data.days_until_renewal}")
            
        if data.contract_end_date == "26/11/2027":
            print("✅ Contract End extracted despite <span> tags")
        else:
             print(f"❌ Contract End failed: {data.contract_end_date}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(run_advanced_test())
