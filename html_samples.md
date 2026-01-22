# miAntel HTML samples (internet fijo)

## Dashboard card (servicio internet)

```html
<form id="j_idt160:3:j_idt1488" name="j_idt160:3:j_idt1488" method="post" action="/miAntel/" enctype="application/x-www-form-urlencoded">
<input type="hidden" name="j_idt160:3:j_idt1488" value="j_idt160:3:j_idt1488">
<div class="servicioBox internet servicio-activo">
  <div class="opacidad card card-base card-base--dashboard">
    <div class="row no-gutters">
      <div class="col-md-4 col-xs-12 card-header-container">
        <div class="card-header">
          <div class="header-icon bg-internet">
            <i class="icon-internet align-middle"></i>
          </div>
          <div class="header-top mb-3">
            <div class="tMenu_parent mobile">
              <div class="tMenu_toggle" onclick="$('#subMenuCombo-ZU3367').modal('show'); if ($('#subMenuCombo-ZU3367').parents('.card.card-base.card-base--dashboard').hasClass('servicio-inactivo')){$('#subMenuCombo-ZU3367').parents('.card.card-base.card-base--dashboard').addClass('servicio-inactivo-con-modal-abierto');}">
                <i class="icon-configuracion"></i>
              </div>
            </div>
            <h5 class="font-bold m-0 mobile">ZU3367</h5>
            <h5 class="font-bold m-0">
              <a href="#" class="editarA" id="s-ZU3367" onclick="return false;">
                <span id="alias-ZU3367" style="font-family: 'RobotoCondensed-Bold', Arial, sans-serif;">ZU3367</span>
                <i class="icon-editar"></i>
              </a>
            </h5>
            <p>
              Fibra con límite 1<span class="text-orange"></span>
            </p>
          </div>
          <div style="display:" class="header-bottom  text-blue-light   ">
            <p class="m-0 font-light">Me quedan</p>
            <div class="mb-2 font-light">
              <span class="value-data">145,6</span>
              <small class="align-self-end sign-data order-first order-last">GB</small>
            </div>
          </div>
          <p class="mt-3">Fin de contrato: <span class="text-orange">26/11/2027</span></p>
        </div>
      </div>
      <div class="col-md-8 col-xs-12">
        <div class="card-body">
          <div class="row d-none d-md-block">
            <div class="tMenu_parent text-primary">
              <div class="tMenu_toggle">
                <i class="icon-configuracion"></i>
                <div class="tMenu_close"><i class="icon-close"></i></div>
              </div>
              <div class="tMenu_menu" style="display: none;">
                <ul class="ul-menu-contextual">
                  <li class="menu-contextual-padre-li"><div class="menu-contextual-padre consumos-padre">Consumos<i class="icon icon-flecha_abajo icono-menu-contextual"></i></div></li>
                  <li class="menu-contextual-hijo consumos-hijo" style="display: none;">
                    <a href="#" onclick="jsf.util.chain(this,event,'$('#panelLoadingMenu').css('display', 'block')','mojarra.jsfcljs(document.getElementById('j_idt160:3:j_idt1488'),{'j_idt160:3:j_idt1560':'j_idt160:3:j_idt1560'},'')');return false" class="card_ver_detalle_mobile">Detalle de consumo</a>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</form>
```

## Detalle consumo internet

```html
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
```

## Labels (para selectores directos)

```html
<span class="progress-bar__label right top text-success progress-bar__label--short">Consumidos 104,4 GB</span>
<span class="progress-bar__label left bottom text-warning">Incluido 250 GB </span>
<span class="value-data">145,6</span>
```
