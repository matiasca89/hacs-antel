import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "antel_addon"))

# Import the actual class
try:
    from antel_pkg.antel_scraper import AntelScraper, AntelConsumoData
except ImportError:
    # Fallback for different directory structures
    sys.path.append(os.path.join(os.getcwd(), "antel_addon"))
    from antel_pkg.antel_scraper import AntelScraper, AntelConsumoData

# Sample HTML (The one where "Ciclo actual" is hidden in desktop view)
HTML_SAMPLE = """
<html><body>
<div class="card card-base card-base--dashboard">
  <div class="servicioBox internet">
     <!-- Main data is usually visible -->
     <span class="value-data">145,6</span>
     <span class="value-data">GB</span> <!-- unit mock -->
     <div class="progress-bar__label">Consumidos 104,4 GB</div>
     <div class="progress-bar__label">Incluido 250 GB</div>
     <div class="plan-title">Fibra con límite 1</div>
  </div>

  <!-- This footer is hidden on desktop (d-md-none) but present in HTML -->
  <div class="card-footer-extra">
    <div class="row d-md-none">
        <p class="m-0 text-gray">Ciclo actual: 1 de enero al 31 de enero</p>
        <p class="m-0 text-gray">Quedan 12 días para renovar</p>
    </div>
  </div>
  
  <p>Fin de contrato: 26/11/2027</p>
</div>
</body></html>
"""

class MockLocator:
    """Mock Playwright Locator."""
    def __init__(self, text_content_val=""):
        self._text = text_content_val

    def filter(self, **kwargs): return self
    @property
    def first(self): return self
    
    async def count(self): return 1
    
    async def text_content(self): 
        return self._text

    async def inner_text(self, **kwargs):
        return self._text
        
    def locator(self, selector):
        # Return appropriate mock values based on selector
        if "value-data" in selector and "+" not in selector:
            return MockLocator("145,6")
        if "value-data + small" in selector:
            return MockLocator("GB")
        if "Consumidos" in selector:
            return MockLocator("Consumidos 104,4 GB")
        if "Incluido" in selector:
            return MockLocator("Incluido 250 GB")
        if "plan-title" in selector:
            return MockLocator("Fibra con límite 1")
        return MockLocator("")

class MockPage:
    """Mock Playwright Page."""
    async def wait_for_load_state(self, *args, **kwargs): pass
    async def wait_for_selector(self, *args, **kwargs): pass
    async def route(self, *args, **kwargs): pass
    
    async def content(self):
        return HTML_SAMPLE
        
    async def inner_text(self, selector):
        # Simulate inner_text
        if selector == "body":
            return "Visible text only...\nCiclo actual: 1 de enero al 31 de enero\nFin de contrato: 26/11/2027"
        return ""
        
    def locator(self, selector):
        return MockLocator()

async def run_test():
    print("----------------------------------------------------------------")
    print("Testing AntelScraper._extract_consumption_data Logic (Mocked)")
    print("----------------------------------------------------------------")
    
    # Instantiate scraper
    scraper = AntelScraper("test", "test", service_id="Fibra")
    
    # Mock page
    page = MockPage()
    
    # Run extraction
    # We call the private method directly to test logic
    try:
        data = await scraper._extract_consumption_data(page)
        
        print("\n--- Extraction Results ---")
        print(f"Used Data:      {data.used_data_gb} GB")
        print(f"Total Data:     {data.total_data_gb} GB")
        print(f"Remaining Data: {data.remaining_data_gb} GB")
        print(f"Plan Name:      {data.plan_name}")
        print(f"Billing Period: '{data.billing_period}'")
        
        print("\n--- Validation ---")
        if data.billing_period == "1 de enero al 31 de enero":
            print("✅ Billing Period extracted correctly (from HTML)")
        else:
            print(f"❌ Billing Period FAILED: Got '{data.billing_period}'")

    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
