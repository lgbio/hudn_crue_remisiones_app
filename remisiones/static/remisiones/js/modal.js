/**
 * modal.js — Lógica del modal de creación / edición / clonación de remisiones.
 *
 * Requisitos: 5.2, 5.3, 6.1, 8.1, 8.2, 8.3, 8.4
 */

'use strict';

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Devuelve la fecha/hora actual en formato datetime-local (YYYY-MM-DDTHH:MM). */
function ahora() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Limpia todos los errores inline del formulario. */
function limpiarErrores() {
  document.querySelectorAll('#form-remision .invalid-feedback').forEach(el => {
    el.textContent = '';
  });
  document.querySelectorAll('#form-remision .is-invalid').forEach(el => {
    el.classList.remove('is-invalid');
  });
  const alertaErrores = document.getElementById('modal-errores');
  if (alertaErrores) {
    alertaErrores.classList.add('d-none');
    alertaErrores.textContent = '';
  }
}

/** Muestra errores de validación del servidor en los campos correspondientes. */
function mostrarErrores(errors) {
  const alertaErrores = document.getElementById('modal-errores');
  const mensajes = [];

  for (const [campo, lista] of Object.entries(errors)) {
    const errMsg = Array.isArray(lista) ? lista.join(' ') : String(lista);
    const inputEl = document.getElementById('id_' + campo);
    const errEl = document.getElementById('err-' + campo);
    if (inputEl) inputEl.classList.add('is-invalid');
    if (errEl) {
      errEl.textContent = errMsg;
    } else {
      mensajes.push(`${campo}: ${errMsg}`);
    }
  }

  if (mensajes.length && alertaErrores) {
    alertaErrores.textContent = mensajes.join(' | ');
    alertaErrores.classList.remove('d-none');
  }
}

/** Establece el modo del modal: 'crear', 'editar' o 'ver' (solo lectura). */
function setModoModal(modo) {
  const titulo = document.getElementById('modal-titulo');
  const btnGuardar = document.getElementById('btn-guardar-remision');
  const badge = document.getElementById('modal-readonly-badge');
  const campos = document.querySelectorAll('#form-remision input, #form-remision select, #form-remision textarea');

  const soloLectura = (modo === 'ver');

  campos.forEach(el => {
    if (el.id === 'modal-remision-id') return; // campo oculto, siempre habilitado
    el.disabled = soloLectura;
  });

  if (btnGuardar) btnGuardar.disabled = soloLectura;
  if (badge) badge.classList.toggle('d-none', !soloLectura);

  if (titulo) {
    if (modo === 'crear') titulo.textContent = 'Nueva Remisión';
    else if (modo === 'editar') titulo.textContent = 'Editar Remisión';
    else titulo.textContent = 'Ver Remisión (solo lectura)';
  }
}

/** Rellena el formulario del modal con los datos de una remisión. */
function rellenarFormulario(data) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val !== null && val !== undefined ? val : '';
  };

  // fecha: actualizar usando el nuevo widget
  datetimeWidget.setValue(data.fecha || '', 'id_fecha_date', 'id_fecha_time', 'id_fecha');

  set('id_nombre', data.nombre || '');
  set('id_tipo_doc', data.tipo_doc || 'CC');
  set('id_doc', data.doc || '');
  set('id_sexo', data.sexo || 'M');
  set('id_edad', data.edad || '');
  set('id_gest', data.gest || 'NO');
  set('id_diagnostico', data.diagnostico || '');
  set('id_ta', data.ta || '');
  set('id_fc', data.fc || '');
  set('id_fr', data.fr || '');
  set('id_tm', data.tm || '');
  set('id_spo2', data.spo2 || '');
  set('id_glasg', data.glasg || '15/15');
  set('id_eps', data.eps || '');
  set('id_institucion_reporta', data.institucion_reporta || '');
  set('id_municipio', data.municipio || '');
  set('id_medico_refiere', data.medico_refiere || '');
  set('id_medico_hudn', data.medico_hudn || '');
  set('id_radio_operador', data.radio_operador || '');
  set('id_observacion', data.observacion || '');
  set('id_aceptado', data.aceptado || 'NO');

  // fecha_res: actualizar usando el nuevo widget
  datetimeWidget.setValue(data.fecha_res || '', 'id_fecha_res_date', 'id_fecha_res_time', 'id_fecha_res');

  set('modal-oportunidad', data.oportunidad || '');

  // Aplicar lógica GEST → SEXO
  const gestVal = data.gest || 'NO';
  const sexoCampo = document.getElementById('id_sexo');
  if (sexoCampo) {
    sexoCampo.disabled = (gestVal === 'SI');
  }
}

/** Rellena los valores por defecto para un nuevo registro. */
function rellenarDefectos() {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val;
  };

  // Establecer fecha actual usando el nuevo widget
  const ahoraIso = ahora();
  datetimeWidget.setValue(ahoraIso, 'id_fecha_date', 'id_fecha_time', 'id_fecha');

  set('id_tipo_doc', 'CC');
  set('id_sexo', 'M');
  set('id_gest', 'NO');
  set('id_glasg', '15/15');
  set('id_aceptado', 'NO');
  set('modal-oportunidad', '');

  // Limpiar campos clínicos y de resultado
  ['id_nombre','id_doc','id_edad','id_diagnostico','id_ta','id_fc',
   'id_fr','id_tm','id_spo2','id_eps','id_institucion_reporta','id_municipio',
   'id_medico_refiere','id_medico_hudn','id_radio_operador','id_observacion'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });

  // Limpiar campos de fecha_res usando el nuevo widget
  datetimeWidget.setValue('', 'id_fecha_res_date', 'id_fecha_res_time', 'id_fecha_res');

  // Habilitar SEXO
  const sexoCampo = document.getElementById('id_sexo');
  if (sexoCampo) sexoCampo.disabled = false;

  // Prellenar radio_operador con el nombre del usuario autenticado
  if (typeof USUARIO_NOMBRE_COMPLETO !== 'undefined' && USUARIO_NOMBRE_COMPLETO !== '') {
    const radioOperadorEl = document.getElementById('id_radio_operador');
    if (radioOperadorEl) radioOperadorEl.value = USUARIO_NOMBRE_COMPLETO;
  }

  document.getElementById('modal-remision-id').value = '';
}

// ─── Apertura del modal ──────────────────────────────────────────────────────

/** Abre el modal en modo creación. */
function abrirModalNuevo() {
  limpiarErrores();
  rellenarDefectos();
  setModoModal('crear');
  const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modal-remision'));
  modal.show();
}

/** Abre el modal en modo edición o solo lectura según editabilidad. */
function abrirModalEdicion(id) {
  const url = URLS.remisionDetalle.replace('__ID__', id);
  fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
      limpiarErrores();
      rellenarFormulario(data);
      document.getElementById('modal-remision-id').value = id;
      setModoModal(data.es_editable ? 'editar' : 'ver');
      const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modal-remision'));
      modal.show();
    })
    .catch(() => alert('Error al cargar los datos del registro.'));
}

/** Abre el modal en modo clonación: copia identificación, limpia campos clínicos. */
function abrirModalClonacion(id) {
  const url = URLS.remisionDetalle.replace('__ID__', id);
  fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
      limpiarErrores();
      rellenarDefectos();

      // Copiar campos de identificación del paciente
      const set = (fieldId, val) => {
        const el = document.getElementById(fieldId);
        if (el) el.value = val || '';
      };
      set('id_nombre', data.nombre);
      set('id_tipo_doc', data.tipo_doc);
      set('id_doc', data.doc);
      set('id_sexo', data.sexo);
      set('id_edad', data.edad);
      set('id_gest', data.gest);
      set('id_eps', data.eps);
      set('id_municipio', data.municipio);
      set('id_medico_refiere', data.medico_refiere);

      // fecha = ahora (ya establecido por rellenarDefectos)
      document.getElementById('modal-remision-id').value = '';

      // Sobrescribir radio_operador con el nombre del usuario autenticado
      if (typeof USUARIO_NOMBRE_COMPLETO !== 'undefined' && USUARIO_NOMBRE_COMPLETO !== '') {
        const radioOperadorEl = document.getElementById('id_radio_operador');
        if (radioOperadorEl) radioOperadorEl.value = USUARIO_NOMBRE_COMPLETO;
      }

      // Aplicar lógica GEST → SEXO
      const sexoCampo = document.getElementById('id_sexo');
      if (sexoCampo) sexoCampo.disabled = (data.gest === 'SI');

      setModoModal('crear');
      const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modal-remision'));
      modal.show();
    })
    .catch(() => alert('Error al cargar los datos para clonar.'));
}

// ─── Guardado ────────────────────────────────────────────────────────────────

/** Recoge los datos del formulario como objeto plano. */
function recogerDatosFormulario() {
  const ids = [
    'fecha','nombre','tipo_doc','doc','sexo','edad','gest',
    'diagnostico','ta','fc','fr','tm','spo2','glasg','eps',
    'institucion_reporta','municipio','medico_refiere','medico_hudn',
    'radio_operador','observacion','aceptado','fecha_res',
  ];
  // Campos que NO se convierten a mayúsculas (fechas, selects, campos calculados)
  const noUppercase = new Set(['fecha', 'fecha_res', 'tipo_doc', 'sexo', 'gest', 'aceptado']);
  const data = {};
  ids.forEach(name => {
    const el = document.getElementById('id_' + name);
    let val = el ? el.value : '';
    if (val && !noUppercase.has(name)) {
      val = val.toUpperCase();
    }
    data[name] = val;
  });
  return data;
}

/** Envía el formulario al servidor vía AJAX. */
function guardarRemision() {
  const remisionId = document.getElementById('modal-remision-id').value;
  const esEdicion = !!remisionId;

  limpiarErrores();

  // Validación cliente: fecha_res debe ser posterior a fecha (si ambas están presentes)
  const fechaVal = document.getElementById('id_fecha').value;
  const fechaResVal = document.getElementById('id_fecha_res').value;
  if (fechaVal && fechaResVal) {
    const fecha = new Date(fechaVal);
    const fechaRes = new Date(fechaResVal);
    if (fechaRes <= fecha) {
      const msg = 'La fecha de respuesta debe ser posterior a la fecha de ingreso.';
      const alertaErrores = document.getElementById('modal-errores');
      if (alertaErrores) {
        alertaErrores.textContent = msg;
        alertaErrores.classList.remove('d-none');
      }
      const fechaResDateEl = document.getElementById('id_fecha_res_date');
      if (fechaResDateEl) fechaResDateEl.classList.add('is-invalid');
      return; // No enviar al servidor
    }
  }

  const url = esEdicion
    ? URLS.remisionEditar.replace('__ID__', remisionId)
    : URLS.remisionNueva;

  const body = new URLSearchParams(recogerDatosFormulario());
  body.append('csrfmiddlewaretoken', CSRF_TOKEN);

  limpiarErrores();

  fetch(url, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: body.toString(),
  })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        // Cerrar modal y recargar la página para reflejar cambios
        const modal = bootstrap.Modal.getInstance(document.getElementById('modal-remision'));
        if (modal) modal.hide();
        window.location.reload();
      } else {
        if (data.errors) {
          mostrarErrores(data.errors);
        } else if (data.error) {
          const alertaErrores = document.getElementById('modal-errores');
          if (alertaErrores) {
            alertaErrores.textContent = data.error;
            alertaErrores.classList.remove('d-none');
          }
        }
      }
    })
    .catch(() => alert('Error de red al guardar el registro.'));
}

// ─── Inicialización ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {

  // Botón "Nuevo Registro"
  const btnNuevo = document.getElementById('btn-nuevo-registro');
  if (btnNuevo) btnNuevo.addEventListener('click', abrirModalNuevo);

  // Botón "Guardar" del modal
  const btnGuardar = document.getElementById('btn-guardar-remision');
  if (btnGuardar) btnGuardar.addEventListener('click', guardarRemision);

  // Calcular OPORTUNIDAD en tiempo real cuando se confirma fecha_res
  const fechaResHidden = document.getElementById('id_fecha_res');
  if (fechaResHidden) {
    fechaResHidden.addEventListener('datetimeChanged', function () {
      const fechaVal = document.getElementById('id_fecha').value;
      const fechaResVal = this.value;
      const oportunidadEl = document.getElementById('modal-oportunidad');

      // Limpiar error previo de fecha_res
      const alertaErroresRT = document.getElementById('modal-errores');
      if (alertaErroresRT) { alertaErroresRT.classList.add('d-none'); alertaErroresRT.textContent = ''; }
      const fechaResDateEl = document.getElementById('id_fecha_res_date');
      if (fechaResDateEl) fechaResDateEl.classList.remove('is-invalid');

      if (fechaVal && fechaResVal) {
        const fecha = new Date(fechaVal);
        const fechaRes = new Date(fechaResVal);
        if (fechaRes > fecha) {
          const diffMin = Math.floor((fechaRes - fecha) / 60000);
          const hh = String(Math.floor(diffMin / 60)).padStart(2, '0');
          const mm = String(diffMin % 60).padStart(2, '0');
          if (oportunidadEl) oportunidadEl.value = `${hh}:${mm}`;
        } else {
          if (oportunidadEl) oportunidadEl.value = '';
          // Mostrar error en la alerta del modal (visible siempre)
          const alertaErrores = document.getElementById('modal-errores');
          if (alertaErrores) {
            alertaErrores.textContent = 'La fecha de respuesta debe ser posterior a la fecha de ingreso.';
            alertaErrores.classList.remove('d-none');
          }
          if (fechaResDateEl) fechaResDateEl.classList.add('is-invalid');
        }
      } else {
        if (oportunidadEl) oportunidadEl.value = '';
      }
    });
  }

  // Importar Excel — manejar respuesta AJAX
  const formImportar = document.getElementById('form-importar');
  if (formImportar) {
    formImportar.addEventListener('submit', function (e) {
      e.preventDefault();
      const formData = new FormData(this);
      const resultadoDiv = document.getElementById('importar-resultado');

      fetch(this.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
      })
        .then(r => r.json())
        .then(data => {
          if (resultadoDiv) {
            if (data.ok) {
              resultadoDiv.className = 'mt-1 small text-success sidebar-text';
              resultadoDiv.textContent = `✓ ${data.importados} registros importados.`;
              setTimeout(() => window.location.reload(), 1500);
            } else {
              resultadoDiv.className = 'mt-1 small text-danger sidebar-text';
              resultadoDiv.textContent = data.error || 'Error al importar.';
            }
          }
        })
        .catch(() => {
          if (resultadoDiv) {
            resultadoDiv.className = 'mt-1 small text-danger sidebar-text';
            resultadoDiv.textContent = 'Error de red.';
          }
        });
    });
  }

});

// Exponer funciones para uso desde tabla.js
window.abrirModalEdicion = abrirModalEdicion;
window.abrirModalClonacion = abrirModalClonacion;
