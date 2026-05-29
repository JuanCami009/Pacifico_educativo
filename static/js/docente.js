/**
 * docente.js - Panel administrativo del docente para Pacífico Educativo.
 *
 * Flujo:
 *   1. Botón "Soy docente" en la pantalla de inicio -> pantalla de PIN
 *   2. PIN válido -> panel con lista de estudiantes y reportes de clase
 *   3. Reportes generados por IA local (Ollama) o fallback determinista offline
 *
 * Requiere: mostrarPantalla() definida en app.js (cargado antes)
 * Seguridad: no usa innerHTML con datos del servidor; todo via DOM methods.
 */

(function () {
  'use strict';

  var _pin = '';
  var _estudianteActivo = null;

  // ── Inicialización ─────────────────────────────────────────────────────────

  function init() {
    bindId('btn-soy-docente',       'click', function () { mostrarPantalla('screen-docente-pin'); });
    bindId('btn-docente-volver',    'click', function () { mostrarPantalla('screen-intro'); });
    bindId('btn-docente-ingresar',  'click', loginDocente);
    bindId('btn-docente-salir',     'click', salirPanel);
    bindId('btn-reporte-clase',     'click', function () { generarReporte('clase', null, false); });
    bindId('btn-regenerar-reporte', 'click', function () {
      if (_estudianteActivo) generarReporte('estudiante', _estudianteActivo, true);
    });

    var pinInput = document.getElementById('docente-pin-input');
    if (pinInput) {
      pinInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') loginDocente();
      });
    }
  }

  function bindId(id, evento, fn) {
    var el = document.getElementById(id);
    if (el) el.addEventListener(evento, fn);
  }

  // ── Login ──────────────────────────────────────────────────────────────────

  function loginDocente() {
    var input = document.getElementById('docente-pin-input');
    var errEl = document.getElementById('docente-pin-error');
    var pin   = input ? input.value.trim() : '';

    if (!pin) { mostrarError(errEl, 'Ingresa el PIN.'); return; }

    fetch('/api/docente/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'X-Docente-Pin': pin },
      body:    JSON.stringify({ pin: pin }),
    })
    .then(function (res) {
      if (!res.ok) {
        mostrarError(errEl, 'PIN incorrecto.');
        if (input) input.value = '';
        return;
      }
      _pin = pin;
      if (errEl) errEl.classList.add('hidden');
      if (input) input.value = '';
      cargarPanel().then(function () { mostrarPantalla('screen-docente-panel'); });
    })
    .catch(function () {
      mostrarError(errEl, 'Error de conexión con el servidor local.');
    });
  }

  // ── Panel ──────────────────────────────────────────────────────────────────

  function cargarPanel() {
    verificarIA();
    return cargarEstudiantes();
  }

  function verificarIA() {
    var badge = document.getElementById('docente-ia-badge');
    if (!badge) return;

    fetch('/api/ia/estado')
      .then(function (r) { return r.json(); })
      .then(function (datos) {
        if (datos.disponible) {
          badge.className   = 'ia-badge ia-badge-online';
          badge.textContent = '🟢 IA local activa';
        } else {
          badge.className   = 'ia-badge ia-badge-offline';
          badge.textContent = '🔴 Modo sin conexión';
        }
      })
      .catch(function () {
        badge.className   = 'ia-badge ia-badge-offline';
        badge.textContent = '🔴 Sin servidor';
      });
  }

  function cargarEstudiantes() {
    var container = document.getElementById('lista-estudiantes');
    if (!container) return Promise.resolve();

    setLoading(container, 'Cargando estudiantes...');

    return fetch('/api/docente/estudiantes', { headers: { 'X-Docente-Pin': _pin } })
      .then(function (res) {
        if (!res.ok) { setError(container, 'Error al cargar estudiantes.'); return; }
        return res.json();
      })
      .then(function (data) {
        if (!data) return;
        var estudiantes = data.estudiantes || [];

        clearEl(container);

        if (!estudiantes.length) {
          var msg = makeEl('p', { style: 'opacity:0.6; text-align:center; padding:1rem;' });
          msg.textContent = 'No hay estudiantes registrados aún. Que los estudiantes inicien sesión para verlos aquí.';
          container.appendChild(msg);
          return;
        }

        estudiantes.forEach(function (est) {
          var prom    = est.promedio_global !== null ? est.promedio_global + '/100' : '—';
          var nivs    = est.niveles_completados || 0;
          var row     = makeEl('div', { className: 'estudiante-row' });
          var info    = makeEl('div', { className: 'estudiante-info' });
          var nombre  = makeEl('strong');
          nombre.textContent  = est.nombre;
          var detalle = makeEl('small');
          detalle.textContent = nivs + ' nivel(es) completado(s) · promedio ' + prom;
          info.appendChild(nombre);
          info.appendChild(detalle);

          var btn = makeEl('button', { className: 'btn btn-outline btn-sm' });
          btn.textContent = 'Ver reporte';
          btn.addEventListener('click', function () { seleccionarEstudiante(est); });

          row.appendChild(info);
          row.appendChild(btn);
          container.appendChild(row);
        });
      })
      .catch(function () {
        setError(container, 'Error de conexión.');
      });
  }

  function seleccionarEstudiante(est) {
    _estudianteActivo = est;
    var seccion  = document.getElementById('reporte-individual-seccion');
    var nombreEl = document.getElementById('reporte-alumno-nombre');
    if (nombreEl) nombreEl.textContent = est.nombre;
    if (seccion) seccion.classList.remove('hidden');
    generarReporte('estudiante', est, false);
    if (seccion) seccion.scrollIntoView({ behavior: 'smooth' });
  }

  // ── Reportes ───────────────────────────────────────────────────────────────

  function generarReporte(tipo, est, regenerar) {
    var boxId   = tipo === 'clase' ? 'reporte-clase-box' : 'reporte-individual-box';
    var box     = document.getElementById(boxId);
    var btnClase = document.getElementById('btn-reporte-clase');
    if (!box) return;

    box.classList.remove('hidden');
    var nombreMostrar = tipo === 'clase' ? 'la clase' : (est ? est.nombre : '');
    setLoading(box, 'Generando reporte de ' + nombreMostrar + '...');
    if (tipo === 'clase' && btnClase) btnClase.disabled = true;

    var qs  = regenerar ? '?regenerar=1' : '';
    var url = tipo === 'clase'
      ? '/api/docente/reporte/clase' + qs
      : '/api/docente/reporte/estudiante/' + est.id + qs;

    fetch(url, { method: 'POST', headers: { 'X-Docente-Pin': _pin } })
      .then(function (res) { return res.json().then(function (d) { return { ok: res.ok, datos: d }; }); })
      .then(function (r) {
        if (!r.ok) { setError(box, r.datos.error || 'No se pudo generar el reporte.'); return; }
        renderReporte(box, r.datos);
      })
      .catch(function () {
        setError(box, 'Error de conexión. Verifica que el servidor esté activo.');
      })
      .finally(function () {
        if (tipo === 'clase' && btnClase) btnClase.disabled = false;
      });
  }

  function renderReporte(box, datos) {
    var esIA       = datos.fuente === 'ollama';
    var badgeClass = esIA ? 'ia-fuente-online' : 'ia-fuente-offline';
    var badgeText  = esIA ? '🟢 IA local' : '🔴 Modo sin conexión';
    var texto      = datos.reporte || 'Sin datos suficientes para generar reporte.';
    var fecha      = datos.fecha   || '';

    clearEl(box);

    var badge = makeEl('span', { className: 'reporte-fuente-badge ' + badgeClass });
    badge.textContent = badgeText;
    box.appendChild(badge);

    var pre = makeEl('pre', { className: 'reporte-texto' });
    pre.textContent = texto;
    box.appendChild(pre);

    if (fecha) {
      var fechaEl = makeEl('small', { className: 'reporte-fecha' });
      fechaEl.textContent = 'Generado: ' + fecha;
      box.appendChild(fechaEl);
    }
  }

  // ── Salir ──────────────────────────────────────────────────────────────────

  function salirPanel() {
    _pin              = '';
    _estudianteActivo = null;

    var claseBox = document.getElementById('reporte-clase-box');
    if (claseBox) { claseBox.classList.add('hidden'); clearEl(claseBox); }

    var indivSeccion = document.getElementById('reporte-individual-seccion');
    if (indivSeccion) indivSeccion.classList.add('hidden');

    var indivBox = document.getElementById('reporte-individual-box');
    if (indivBox) clearEl(indivBox);

    mostrarPantalla('screen-intro');
  }

  // ── DOM helpers ────────────────────────────────────────────────────────────

  function makeEl(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === 'className') { el.className = attrs[k]; }
        else if (k === 'style') { el.setAttribute('style', attrs[k]); }
        else { el[k] = attrs[k]; }
      });
    }
    return el;
  }

  function clearEl(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  function setLoading(container, msg) {
    clearEl(container);
    var p   = makeEl('p', { className: 'docente-loading' });
    var ico = makeEl('i', { className: 'fa-solid fa-spinner fa-spin' });
    p.appendChild(ico);
    p.append(' ' + msg);
    container.appendChild(p);
  }

  function setError(container, msg) {
    clearEl(container);
    var p = makeEl('p', { className: 'error-msg' });
    p.textContent = msg;
    container.appendChild(p);
  }

  function mostrarError(el, msg) {
    if (!el) return;
    el.textContent = msg;
    el.classList.remove('hidden');
  }

  // Arrancar cuando el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
