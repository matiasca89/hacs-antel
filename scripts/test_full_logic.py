import asyncio
import sys
import os
import re
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.getcwd())

# Mock homeassistant for CC imports
sys.modules["homeassistant"] = MagicMock()
sys.modules["homeassistant.config_entries"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()

# Import the actual classes
from antel_addon.antel_pkg.antel_scraper import AntelScraper as ScraperAddon, AntelConsumoData
from custom_components.antel_consumo.antel_scraper import AntelScraper as ScraperCC

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

# Plain text version for inner_text
PLAIN_TEXT_SAMPLE = """
145,6 GB
Consumidos 104,4 GB
Incluido 250 GB
Fibra con límite 1
Ciclo actual: 1 de enero al 31 de enero
Quedan 12 días para renovar
Fin de contrato: 26/11/2027
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

    async def inner_text(self, timeout=None):
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
        return MockLocator(self._text)

class MockPage:
    """Mock Playwright Page."""
    async def wait_for_load_state(self, *args, **kwargs): pass
    
    async def content(self):
        return HTML_SAMPLE
        
    async def inner_text(self, selector):
        if selector == "body":
            return PLAIN_TEXT_SAMPLE
        return ""
        
    def locator(self, selector):
        return MockLocator()

async def test_scraper(name, scraper_class):
    print(f"\n--- Testing {name} ---")
    
    # Instantiate scraper
    scraper = scraper_class("test", "test", service_id="Fibra")
    
    # Mock page
    page = MockPage()
    
    # Run extraction
    try:
        data = await scraper._extract_consumption_data(page)
        
        print(f"Used Data:      {data.used_data_gb} GB")
        print(f"Total Data:     {data.total_data_gb} GB")
        print(f"Remaining Data: {data.remaining_data_gb} GB")
        print(f"Plan Name:      {data.plan_name}")
        print(f"Billing Period: '{data.billing_period}'")
        
        # Validation
        errors = []
        if data.used_data_gb != 104.4:
            errors.append(f"Used Data mismatch: expected 104.4, got {data.used_data_gb}")
        if data.total_data_gb != 250.0:
            errors.append(f"Total Data mismatch: expected 250.0, got {data.total_data_gb}")
        if data.remaining_data_gb != 145.6:
            errors.append(f"Remaining Data mismatch: expected 145.6, got {data.remaining_data_gb}")
        if data.plan_name != "Fibra con límite 1":
            errors.append(f"Plan Name mismatch: expected 'Fibra con límite 1', got '{data.plan_name}'")
        if data.billing_period != "1 de enero al 31 de enero":
            errors.append(f"Billing Period mismatch: expected '1 de enero al 31 de enero', got '{data.billing_period}'")

        if not errors:
            print(f"✅ {name} extraction passed")
            return True
        else:
            for err in errors:
                print(f"❌ {err}")
            return False

    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_tests():
    print("----------------------------------------------------------------")
    print("Testing AntelScraper._extract_consumption_data Logic (Mocked)")
    print("----------------------------------------------------------------")

    s1 = await test_scraper("Addon Scraper", ScraperAddon)
    s2 = await test_scraper("Custom Component Scraper", ScraperCC)

    if s1 and s2:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_tests())
