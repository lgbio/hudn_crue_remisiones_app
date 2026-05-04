/**
 * filtros.js — Lógica de controles de filtro en la vista principal.
 *
 * Requisitos: 3.12, 3.13, 3.14, 3.15, 3.16
 *
 * Responsabilidades:
 *  1. Exclusividad de filtros: al seleccionar un radio button, mostrar el
 *     panel de controles correspondiente y ocultar los demás.
 *  2. Validación en cliente antes de enviar el formulario:
 *     - "Por mes": mes futuro → mensaje de error, cancelar envío.
 *     - "Por rango": desde > hasta → mensaje; hasta futura → mensaje; cancelar envío.
 *     - "Documento": sin validación de fecha.
 *  3. Envío del filtro activo al servidor mediante submit GET del formulario.
 *     Los parámetros (filtro, mes, anio, desde, hasta, doc, page) son enviados
 *     automáticamente por el formulario con method="get".
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {

  // ── Referencias a elementos del DOM ──────────────────────────────────────
  const radios      = document.querySelectorAll('.filtro-radio');
  const ctrlMes     = document.getElementById('ctrl-mes');
  const ctrlRango   = document.getElementById('ctrl-rango');
  const ctrlDoc     = document.getElementById('ctrl-documento');
  const errorMes    = document.getElementById('filtro-error');   // bajo ctrl-mes
  const errorRango  = document.getElementById('error-rango');    // dentro de ctrl-rango
  const formFiltros = document.getElementById('form-filtros');

  // ── 1. Exclusividad de filtros ────────────────────────────────────────────

  /**
   * Muestra únicamente el panel de controles correspondiente al filtro
   * seleccionado y oculta los demás. También limpia los mensajes de error.
   *
   * @param {string} valor - Valor del radio button seleccionado ('mes', 'rango', 'documento').
   */
  function mostrarCtrl(valor) {
    // Ocultar todos los paneles
    [ctrlMes, ctrlRango, ctrlDoc].forEach(function (el) {
      if (el) el.classList.add('d-none');
    });

    // Mostrar el panel activo
    if (valor === 'mes'       && ctrlMes)   ctrlMes.classList.remove('d-none');
    if (valor === 'rango'     && ctrlRango) ctrlRango.classList.remove('d-none');
    if (valor === 'documento' && ctrlDoc)   ctrlDoc.classList.remove('d-none');

    // Limpiar mensajes de error al cambiar de filtro
    limpiarErrores();
  }

  /** Borra todos los mensajes de validación inline. */
  function limpiarErrores() {
    if (errorMes)   errorMes.textContent   = '';
    if (errorRango) errorRango.textContent = '';
  }

  // Inicializar estado al cargar la página (refuerza lo que ya hace el template)
  var radioChecked = document.querySelector('.filtro-radio:checked');
  if (radioChecked) {
    mostrarCtrl(radioChecked.value);
  }

  // Escuchar cambios en los radio buttons
  radios.forEach(function (radio) {
    radio.addEventListener('change', function () {
      mostrarCtrl(this.value);
    });
  });

  // ── 2. Auto-submit on month/year change ─────────────────────────────────

  var selectMes = document.getElementById('select-mes');
  var inputAnio = document.getElementById('input-anio');

  /** Disable future months when the selected year is the current year. */
  function actualizarMesesDisponibles() {
    if (!selectMes || !inputAnio) return;
    var anioVal = parseInt(inputAnio.value, 10);
    var hoy = new Date();
    var anioHoy = hoy.getFullYear();
    var mesHoy = hoy.getMonth() + 1;

    Array.from(selectMes.options).forEach(function (opt) {
      var mesVal = parseInt(opt.value, 10);
      if (anioVal === anioHoy && mesVal > mesHoy) {
        opt.disabled = true;
      } else {
        opt.disabled = false;
      }
    });

    // If the currently selected month is now disabled, select the latest valid month
    var selOpt = selectMes.options[selectMes.selectedIndex];
    if (selOpt && selOpt.disabled) {
      // Find the last enabled option
      for (var i = selectMes.options.length - 1; i >= 0; i--) {
        if (!selectMes.options[i].disabled) {
          selectMes.selectedIndex = i;
          break;
        }
      }
    }
  }

  // Auto-submit when month changes
  if (selectMes && formFiltros) {
    selectMes.addEventListener('change', function () {
      formFiltros.submit();
    });
  }

  // When year changes, update disabled months and auto-submit
  if (inputAnio && formFiltros) {
    inputAnio.addEventListener('change', function () {
      actualizarMesesDisponibles();
      formFiltros.submit();
    });
  }

  // ── 3. Ordering toggle ────────────────────────────────────────────────────

  var btnOrden = document.getElementById('btn-orden');
  var inputOrden = document.getElementById('input-orden');
  var ordenLabel = document.getElementById('orden-label');

  if (btnOrden && inputOrden && formFiltros) {
    btnOrden.addEventListener('click', function () {
      var esDesc = inputOrden.value === 'desc';
      inputOrden.value = esDesc ? 'asc' : 'desc';

      // Update button visual immediately
      var icon = btnOrden.querySelector('i');
      if (icon) {
        icon.className = esDesc ? 'bi bi-sort-up me-1' : 'bi bi-sort-down me-1';
      }
      if (ordenLabel) {
        ordenLabel.textContent = esDesc ? 'Antiguos' : 'Recientes';
      }
      btnOrden.title = esDesc ? 'Más antiguos primero' : 'Más recientes primero';

      formFiltros.submit();
    });
  }

  // ── 4. Validación en cliente antes de enviar ──────────────────────────────

  if (formFiltros) {
    formFiltros.addEventListener('submit', function (e) {
      limpiarErrores();

      var filtroActivo = document.querySelector('.filtro-radio:checked');
      if (!filtroActivo) return; // Sin filtro seleccionado, dejar pasar

      var valor = filtroActivo.value;

      // ── Validación "Por mes" (Requisito 3.14) ──────────────────────────
      if (valor === 'mes') {
        var mesSelect  = formFiltros.querySelector('[name="mes"]');
        var anioInput  = formFiltros.querySelector('[name="anio"]');

        if (mesSelect && anioInput) {
          var mesVal  = parseInt(mesSelect.value, 10);
          var anioVal = parseInt(anioInput.value, 10);
          var hoy     = new Date();
          var anioHoy = hoy.getFullYear();
          var mesHoy  = hoy.getMonth() + 1; // getMonth() es 0-based

          var esFuturo = (anioVal > anioHoy) ||
                         (anioVal === anioHoy && mesVal > mesHoy);

          if (esFuturo) {
            e.preventDefault();
            if (errorMes) {
              errorMes.textContent =
                'Solo se permiten meses anteriores o el mes actual.';
            }
            return;
          }
        }
      }

      // ── Validación "Por rango" (Requisitos 3.15, 3.16) ────────────────
      if (valor === 'rango') {
        var desdeInput = document.getElementById('input-desde');
        var hastaInput = document.getElementById('input-hasta');

        if (desdeInput && hastaInput) {
          var desde = desdeInput.value;
          var hasta = hastaInput.value;
          var hoyStr = new Date().toISOString().slice(0, 10); // 'YYYY-MM-DD'

          // Requisito 3.15: desde > hasta
          if (desde && hasta && desde > hasta) {
            e.preventDefault();
            if (errorRango) {
              errorRango.textContent =
                'La fecha "Desde" no puede ser posterior a "Hasta".';
            }
            return;
          }

          // Requisito 3.16: hasta futura
          if (hasta && hasta > hoyStr) {
            e.preventDefault();
            if (errorRango) {
              errorRango.textContent =
                'No se permiten fechas futuras en el campo "Hasta".';
            }
            return;
          }
        }
      }

      // "Documento": sin validación de fecha — el formulario se envía normalmente.
    });
  }

});
