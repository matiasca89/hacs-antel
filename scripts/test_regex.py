import re

# Sample HTML from html_samples.md (approximated based on what we saw)
HTML_SAMPLE = """
<div class="card card-base card-base--dashboard"><div id="consumoGeneral" class="ui-outputpanel ui-widget">
  <div class="row no-gutters   d-flex">
    <div class="col-md-4 col-xs-12 card-header-container ">
      <div class="card-header">
        <div class="header-bottom   text-blue-light  ">
          <p class="m-0 font-light">Me quedan</p>
          <div class="mb-2 font-light">
            <span class="value-data">145,6</span>
            <small class="align-self-end sign-data order-first order-last">GB</small>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-8 col-xs-12">
      <div class="card-body">
        <div class="pbContainer">
          <div class="progress ">
            <div class="progress-bar  bg-success green" role="progressbar" style="width:41.7769919231534%;">
              <span class="progress-bar__label right top text-success progress-bar__label--short">Consumidos 104,4 GB</span>
            </div>
            <div class="progress-bar bg-info orange" role="progressbar" style="width:58.2230080768466%">
              <span class="progress-bar__label left bottom text-warning">Incluido 250 GB </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="row no-gutters">
    <div class="col-md-12 alt_text_info_mobile">
      <div class="card-footer-extra">
        <div class="row d-md-none justify-content-left mb-3">
          <div class="col col-auto" style="max-width: 100% !important;">
            <div class="media">
              <i class="icon-recargar text-green align-self-center mr-2"></i>
              <div class="media-body">
                <p class="m-0 text-gray">Ciclo actual: 1 de enero al 31 de enero</p>
                <p class="m-0 text-gray font-light-italic lh-12 fs-12">Quedan 12 días para renovar</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div></div>
"""

def test_extraction():
    print("Testing Regex on Sample HTML...")
    
    # 1. Billing Period
    match = re.search(r"Ciclo actual:\s*([^<\n]+)", HTML_SAMPLE)
    if match:
        print(f"✅ Billing Period: '{match.group(1).strip()}'")
    else:
        print("❌ Billing Period: Not found")

    # 2. Days until renewal
    renewal_match = re.search(r"Quedan?\s*(\d+)\s*d[íi]as?\s*(para\s*)?renovar", HTML_SAMPLE, re.IGNORECASE)
    if renewal_match:
        print(f"✅ Days until renewal: {renewal_match.group(1)}")
    else:
        print("❌ Days until renewal: Not found")

    # 3. Contract End (Mocking sample as it was in dashboard card not consumption detail)
    HTML_DASHBOARD = """
    <p class="mt-3">Fin de contrato: <span class="text-orange">26/11/2027</span></p>
    """
    contract_match = re.search(r"Fin de contrato[:\s]*<[^>]+>\s*(\d{1,2}/\d{1,2}/\d{4})", HTML_DASHBOARD, re.IGNORECASE)
    if not contract_match:
         contract_match = re.search(r"Fin de contrato[:\s]*(\d{1,2}/\d{1,2}/\d{4})", HTML_DASHBOARD, re.IGNORECASE)
         
    if contract_match:
        print(f"✅ Contract End: {contract_match.group(1)}")
    else:
        print("❌ Contract End: Not found")

if __name__ == "__main__":
    test_extraction()
