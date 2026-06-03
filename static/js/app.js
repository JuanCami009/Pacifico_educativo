/**
 * app.js - Lógica principal de la SPA Pacífico Educativo.
 * Gestiona el estado global, navegación entre pantallas y llamadas a la API.
 */

// ── Estado global ────────────────────────────────────────────────────────────
const Estado = {
  estudiante:   null,   // { id, nombre }
  progreso:     {},     // { materia: { nivel_maximo, completados, puntajes[] } }
  materiaActiva: null,
  nivelActivo:   1,
  nivelDatos:    null,  // datos completos del nivel actual
  puntajeActual: 100,
  motorActivo:   null,  // instancia del motor de minijuego (legacy)
  destruirMinijuego: null, // callback para detener minijuegos con bucle (ej. cangrejos manglar)
};

// ── Datos de materias ────────────────────────────────────────────────────────
const MATERIAS = [
  { clave: 'matematicas', nombre: 'Matemáticas', icon: 'fa-solid fa-calculator', personaje: 'El Riviel',
    grad: 'linear-gradient(135deg,#2E7D32,#1B5E20)' },
  { clave: 'lenguaje',    nombre: 'Lenguaje',    icon: 'fa-solid fa-book', personaje: 'La Tunda',
    grad: 'linear-gradient(135deg,#BF360C,#E65100)' },
  { clave: 'ingles',      nombre: 'Inglés',       icon: 'fa-solid fa-language', personaje: 'El Duende',
    grad: 'linear-gradient(135deg,#0D47A1,#1565C0)' },
  { clave: 'biologia',   nombre: 'Biología',     icon: 'fa-solid fa-dna', personaje: 'La Madre de Agua',
    grad: 'linear-gradient(135deg,#00695C,#004D40)' },
];

const PERSONAJES = {
  matematicas: { nombre: 'El Riviel',       icon: 'fa-solid fa-fire',  color: '#42A5F5' },
  lenguaje:    { nombre: 'La Tunda',        icon: 'fa-solid fa-leaf',  color: '#66BB6A' },
  ingles:      { nombre: 'El Duende',       icon: 'fa-solid fa-hat-wizard',  color: '#CE93D8' },
  biologia:    { nombre: 'La Madre de Agua',icon: 'fa-solid fa-droplet',  color: '#4DD0E1' },
};

const NOMBRES_NIVEL = [
  'La Orilla del Río','El Manglar Sagrado','La Selva Oscura',
  'El Corazón del Pacífico','El Guardabosques',
];

const ICONOS_UI = {
  matematicas: `<img src="/static/images/ui/matematicas.png" alt="Matemáticas" class="materia-icon-img">`,
  lenguaje:    `<img src="/static/images/ui/lenguaje.png"    alt="Lenguaje"    class="materia-icon-img">`,
  ingles:      `<img src="/static/images/ui/ingles.png"      alt="Inglés"      class="materia-icon-img">`,
  biologia:    `<img src="/static/images/ui/biologia.png"    alt="Biología"    class="materia-icon-img">`
};

// ── Navegación de pantallas ──────────────────────────────────────────────────
function mostrarPantalla(id) {
  Estado.pantallaActual = id;
  if (Estado.estudiante) {
    localStorage.setItem('pacifico_estado_v2', JSON.stringify({
      estudiante: Estado.estudiante,
      materiaActiva: Estado.materiaActiva,
      nivelActivo: Estado.nivelActivo,
      pantallaActual: id
    }));
  }
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
}

/**
 * Cambia la clase del body para actualizar el fondo de pantalla.
 * @param {string} clase - Clase CSS definida en styles.css (.bg-...)
 */
function actualizarFondo(clase) {
  // Remover todas las clases de fondo conocidas
  const fondos = [
    'bg-intro', 'bg-menu', 'bg-victoria',
    'bg-niveles-matematicas', 'bg-niveles-lenguaje', 'bg-niveles-ingles', 'bg-niveles-biologia',
    'bg-juego-matematicas', 'bg-juego-matematicas-2', 'bg-juego-matematicas-3', 'bg-juego-matematicas-4', 'bg-juego-matematicas-5', 
    'bg-juego-lenguaje', 'bg-juego-ingles', 'bg-juego-biologia'
  ];
  document.body.classList.remove(...fondos);
  document.body.classList.add(clase);
}

/**
 * Cierra la pantalla de chat y vuelve a la intro del personaje.
 */
function cerrarChat() {
  if (Estado.materiaActiva) {
    mostrarPersonaje(Estado.nivelActivo);
  } else {
    mostrarMenu();
  }
}

// ── Helpers de API ───────────────────────────────────────────────────────────
async function api(metodo, ruta, cuerpo) {
  const ops = { method: metodo, headers: { 'Content-Type': 'application/json' } };
  if (cuerpo) ops.body = JSON.stringify(cuerpo);
  const res = await fetch(ruta, ops);
  return res.json();
}

// ── PANTALLA 1: Intro / Login ────────────────────────────────────────────────
function irALogin() {
  localStorage.removeItem('pacifico_estado_v2');
  window.location.reload();
}

async function cargarUsuariosGuardados() {
  try {
    const lista = await api('GET', '/api/estudiantes');
    const panel = document.getElementById('usuarios-guardados');
    const contenedor = document.getElementById('usuarios-lista');
    if (!lista || lista.length === 0) { panel.classList.add('hidden'); return; }
    panel.classList.remove('hidden');
    contenedor.innerHTML = '';
    lista.forEach(u => {
      const chip = document.createElement('button');
      chip.className = 'usuario-chip';
      chip.type = 'button';
      const nivelesTotal = u.niveles_completados || 0;
      chip.innerHTML = `
        <i class="fa-solid fa-user-circle" style="color:var(--dorado);"></i>
        <span class="usuario-chip-nombre">${u.nombre}</span>
        <span class="usuario-chip-progreso">${nivelesTotal} nivel${nivelesTotal !== 1 ? 'es' : ''}</span>
      `;
      chip.addEventListener('click', () => {
        document.getElementById('nombre-input').value = u.nombre;
        document.getElementById('btn-entrar').click();
      });
      contenedor.appendChild(chip);
    });
  } catch(e) { /* silencio si falla */ }
}

async function mostrarModalProgreso(estudiante, progreso) {
  const totalNiveles = Object.values(progreso).reduce((acc, m) => acc + (m.completados || 0), 0);
  document.getElementById('modal-progreso-nombre').textContent = `¡Hola, ${estudiante.nombre}!`;
  document.getElementById('modal-progreso-desc').textContent =
    `Tienes ${totalNiveles} nivel${totalNiveles !== 1 ? 'es' : ''} completado${totalNiveles !== 1 ? 's' : ''} en tu aventura. ¿Quieres continuar o empezar desde cero?`;

  const modal = document.getElementById('modal-progreso');
  modal.classList.remove('hidden');

  return new Promise((resolve) => {
    const btnContinuar = document.getElementById('modal-btn-continuar');
    const btnReiniciar = document.getElementById('modal-btn-reiniciar');

    const limpiar = () => {
      modal.classList.add('hidden');
      btnContinuar.replaceWith(btnContinuar.cloneNode(true));
      btnReiniciar.replaceWith(btnReiniciar.cloneNode(true));
    };

    document.getElementById('modal-btn-continuar').addEventListener('click', () => {
      limpiar(); resolve('continuar');
    }, { once: true });

    document.getElementById('modal-btn-reiniciar').addEventListener('click', () => {
      limpiar(); resolve('reiniciar');
    }, { once: true });
  });
}

// ── Preferencia global: IA encendida/apagada ───────────────────────────────
function leerPrefIA() {
  try { return localStorage.getItem('pacifico_ia_on') === '1'; } catch(e) { return false; }
}
function guardarPrefIA(activa) {
  try { localStorage.setItem('pacifico_ia_on', activa ? '1' : '0'); } catch(e) {}
}
function _ajustarTextoToggleIA(activa) {
  const desc = document.getElementById('ia-toggle-desc');
  if (!desc) return;
  desc.textContent = activa
    ? 'Encendida · Chat y reportes con Ollama. Las historias siguen siendo las predefinidas.'
    : 'Apagada · Todo predefinido (rápido, sin internet). Ideal sin conexión.';
}
function initToggleIA() {
  const chk = document.getElementById('ia-toggle-input');
  if (!chk) return;
  chk.checked = leerPrefIA();
  _ajustarTextoToggleIA(chk.checked);
  _ajustarVisibilidadSelectorModelo(chk.checked);
  chk.addEventListener('change', () => {
    guardarPrefIA(chk.checked);
    _ajustarTextoToggleIA(chk.checked);
    _ajustarVisibilidadSelectorModelo(chk.checked);
    // Avisar al servidor de la nueva preferencia
    api('POST', '/api/configuracion/ia', { activa: chk.checked }).catch(() => {});
  });
  // Sincronizar al servidor al iniciar
  api('POST', '/api/configuracion/ia', { activa: chk.checked }).catch(() => {});

  // Selector de modelo
  initSelectorModeloIA();
}

function _ajustarVisibilidadSelectorModelo(iaActiva) {
  const row = document.getElementById('ia-modelo-row');
  if (!row) return;
  row.classList.toggle('hidden', !iaActiva);
}

async function initSelectorModeloIA() {
  const select = document.getElementById('ia-modelo-select');
  const estado = document.getElementById('ia-modelo-estado');
  if (!select) return;

  // Cargar lista de modelos disponibles
  try {
    const data = await api('GET', '/api/ia/modelos');
    if (!data.ollama_ok || !data.modelos || !data.modelos.length) {
      select.innerHTML = '<option value="">Ollama no está corriendo</option>';
      select.disabled = true;
      if (estado) {
        estado.textContent = '⚠️ No se detecta Ollama. Inicialo con: ollama serve';
        estado.className = 'ia-modelo-estado error';
      }
      return;
    }
    select.innerHTML = '';
    // Recuperar modelo preferido del localStorage si existe
    let preferido = '';
    try { preferido = localStorage.getItem('pacifico_ia_modelo') || ''; } catch(e) {}
    const activo = preferido || data.activo;
    data.modelos.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m + (m === data.activo ? '  (activo)' : '');
      if (m === activo) opt.selected = true;
      select.appendChild(opt);
    });
    if (estado) {
      estado.textContent = `${data.modelos.length} modelo(s) disponible(s) · activo: ${data.activo}`;
      estado.className = 'ia-modelo-estado ok';
    }
    // Si el modelo preferido no coincide con el activo del servidor, cambiarlo silenciosamente
    if (preferido && preferido !== data.activo && data.modelos.includes(preferido)) {
      _aplicarCambioModelo(preferido, estado);
    }
  } catch(e) {
    select.innerHTML = '<option value="">Error de red</option>';
    select.disabled = true;
    if (estado) { estado.textContent = '⚠️ Error consultando modelos.'; estado.className = 'ia-modelo-estado error'; }
    return;
  }

  // Listener de cambio
  select.addEventListener('change', () => {
    const nuevo = select.value;
    if (!nuevo) return;
    try { localStorage.setItem('pacifico_ia_modelo', nuevo); } catch(e) {}
    _aplicarCambioModelo(nuevo, estado);
  });
}

async function _aplicarCambioModelo(modelo, estadoEl) {
  if (estadoEl) {
    estadoEl.textContent = `Cambiando a ${modelo}…`;
    estadoEl.className = 'ia-modelo-estado';
  }
  try {
    const res = await fetch('/api/ia/modelo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ modelo }),
    });
    const data = await res.json();
    if (res.ok && data.ok) {
      if (estadoEl) {
        estadoEl.textContent = `✅ Modelo activo: ${data.modelo}`;
        estadoEl.className = 'ia-modelo-estado ok';
      }
    } else {
      if (estadoEl) {
        estadoEl.textContent = `⚠️ ${data.error || 'No se pudo cambiar el modelo.'}`;
        estadoEl.className = 'ia-modelo-estado error';
      }
    }
  } catch(e) {
    if (estadoEl) { estadoEl.textContent = '⚠️ Error de red al cambiar modelo.'; estadoEl.className = 'ia-modelo-estado error'; }
  }
}

function initIntro() {
  initToggleIA();
  const guardado = localStorage.getItem('pacifico_estado_v2');
  if (guardado) {
    try {
      const st = JSON.parse(guardado);
      if (st.estudiante) {
        Estado.estudiante = st.estudiante;
        Estado.materiaActiva = st.materiaActiva;
        Estado.nivelActivo = st.nivelActivo;
        Estado.pantallaActual = st.pantallaActual;
        
        cargarProgreso().then(async () => {
          if (st.pantallaActual === 'screen-minijuego') {
            await mostrarPersonaje(st.nivelActivo);
            iniciarMinijuego();
          } else if (st.pantallaActual === 'screen-personaje' || st.pantallaActual === 'screen-mision') {
            mostrarMision(st.nivelActivo);
          } else if (st.pantallaActual === 'screen-level-select') {
            seleccionarMateria(st.materiaActiva);
          } else if (st.pantallaActual === 'screen-puntajes') {
            mostrarPuntajes();
          } else {
            mostrarMenu();
          }
        });
        return;
      }
    } catch(e) { console.error('Error restaurando estado:', e); }
  }

  actualizarFondo('bg-intro');
  cargarUsuariosGuardados();
  const input  = document.getElementById('nombre-input');
  const btnOk  = document.getElementById('btn-entrar');
  const errMsg = document.getElementById('intro-error');

  async function entrar() {
    const nombre = input.value.trim();
    if (!nombre) { errMsg.textContent = 'Escribe tu nombre para continuar.'; errMsg.classList.remove('hidden'); return; }
    errMsg.classList.add('hidden');
    const datos = await api('POST', '/api/estudiante/login', { nombre });
    if (datos.error) { errMsg.textContent = datos.error; errMsg.classList.remove('hidden'); return; }
    Estado.estudiante = datos;
    await cargarProgreso();

    // Comprobar si ya tiene niveles completados
    const totalNiveles = Object.values(Estado.progreso).reduce((acc, m) => acc + (m.completados || 0), 0);
    if (totalNiveles > 0) {
      const decision = await mostrarModalProgreso(datos, Estado.progreso);
      if (decision === 'reiniciar') {
        await api('POST', '/api/progreso/reset', { estudiante_id: datos.id });
        await cargarProgreso();
      }
    }
    mostrarMenu();
  }

  btnOk.addEventListener('click', entrar);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') entrar(); });
}


// ── Cargar progreso del estudiante ──────────────────────────────────────────
async function cargarProgreso() {
  Estado.progreso = await api('GET', `/api/progreso/${Estado.estudiante.id}`);
}

// ── PANTALLA 2: Menú de materias ────────────────────────────────────────────
function mostrarMenu() {
  actualizarFondo('bg-menu');
  document.getElementById('saludo-header').textContent = `¡Hola, ${Estado.estudiante.nombre}!`;
  const grid = document.getElementById('materias-grid');
  grid.innerHTML = '';

  MATERIAS.forEach(mat => {
    const prog     = Estado.progreso[mat.clave] || { completados: 0 };
    const completados = prog.completados || 0;
    const fraccion = (completados / 5) * 100;

    const card = document.createElement('div');
    card.className = 'materia-card';
    card.innerHTML = `
      <div class="materia-emoji-container">${ICONOS_UI[mat.clave]}</div>
      <div class="materia-nombre">${mat.nombre}</div>
      <div class="materia-sub">${completados}/5 niveles</div>
      <div class="materia-personaje">Guía: ${mat.personaje}</div>
      <div class="barra-container"><div class="barra-progreso" style="width:${fraccion}%"></div></div>`;
    card.addEventListener('click', () => seleccionarMateria(mat.clave));
    grid.appendChild(card);
  });

  mostrarPantalla('screen-menu');

  // ── Precarga AGRESIVA: nivel 1 de cada materia desde el menú ──────────────
  // Así, cuando el estudiante elige una materia y luego un nivel, la historia
  // del nivel 1 ya está lista. Los demás niveles se precargan al entrar al selector.
  _precargarNivel1DeCadaMateria();
  // Precarga de imágenes pesadas (backgrounds de selector + explicaciones de misión)
  _precargarImagenesPesadas();
}

// Pone en caché del navegador todas las imágenes grandes que se van a usar
// en las próximas pantallas, para que al cambiar de vista aparezcan instantáneas.
function _precargarImagenesPesadas() {
  const urls = [
    // Backgrounds de selectores de niveles
    '/static/images/backgrounds/nivelesMatematicas.png',
    '/static/images/backgrounds/nivelesLenguaje.png',
    '/static/images/backgrounds/nivelesIngles.png',
    '/static/images/backgrounds/nivelesBiologia.png',
    // Imágenes explicativas de misión
    '/static/images/level_matematicas/explicaNiv2-5Mat.png',
    '/static/images/level_lenguaje/explicaNivLen.png',
    '/static/images/level_ingles/explicaNivIng.png',
    '/static/images/level_biologia/explicaNivBio.png',
    // Nodos de nivel de matemáticas
    '/static/images/level_matematicas/level1Mat.png',
    '/static/images/level_matematicas/level2Mat.png',
    '/static/images/level_matematicas/level3Mat.png',
    '/static/images/level_matematicas/level4Mat.png',
    '/static/images/level_matematicas/level5Mat.png',
    // Personaje
    '/static/images/level_matematicas/riviel.png',
  ];
  urls.forEach(u => { const img = new Image(); img.src = u; });
}

// Precarga solo el nivel 1 de cada materia (texto rápido + audio en background)
async function _precargarNivel1DeCadaMateria() {
  const materias = MATERIAS.map(m => m.clave);
  for (const mat of materias) {
    const k = `${mat}-1`;
    if (_historiaCache.has(k)) continue;
    _historiaCache.set(k, 'loading');
    await _precargarTexto(mat, 1, k);
  }
  // Calentar audios del nivel 1 en background
  for (const mat of materias) _calentarAudioNivel(`${mat}-1`);
}

// Función global accesible desde el onclick inline (más confiable que addEventListener)
window.__verPuntajes = function() {
  console.log('[Puntajes] Click detectado');
  mostrarPuntajes();
};
document.getElementById('btn-puntajes').addEventListener('click', window.__verPuntajes);

// ── PANTALLA 3: Selección de nivel ──────────────────────────────────────────
function seleccionarMateria(clave) {
  Estado.materiaActiva = clave;
  actualizarFondo(`bg-niveles-${clave}`);
  const mat  = MATERIAS.find(m => m.clave === clave);
  const per  = PERSONAJES[clave];
  const prog = Estado.progreso[clave] || { nivel_maximo: 1 };
  const nivelMax = prog.nivel_maximo || 1;

  // Encabezado: si la materia tiene imagen del personaje, mostrarla; si no, icono de FontAwesome
  document.getElementById('level-select-titulo').textContent = mat.nombre;
  const imgPersonaje = _imagenPersonaje(clave);
  const visualPersonaje = imgPersonaje
    ? `<img src="${imgPersonaje}" alt="${per.nombre}" class="personaje-banner-img">`
    : `<span style="font-size:2rem"><i class="${per.icon}" style="color:${per.color}"></i></span>`;
  document.getElementById('personaje-guia-banner').innerHTML =
    `${visualPersonaje}
     <div style="margin-left:14px;"><strong>${per.nombre}</strong> te acompaña en esta aventura</div>`;

  // Nodos de nivel con imágenes por materia
  const camino = document.getElementById('niveles-camino');
  camino.innerHTML = '';
  for (let i = 1; i <= 5; i++) {
    const puntaje    = (prog.puntajes || [])[i - 1] || 0;
    const completado = puntaje > 0;
    const desbloq    = i <= nivelMax;
    const esCurrent  = i === nivelMax && !completado;

    const paso = document.createElement('div');
    paso.className = 'nivel-paso';

    // ── Nodo imagen ──────────────────────────────────────────────────
    const nodo = document.createElement('div');
    const claseEstado = completado ? 'completado' : (esCurrent ? 'disponible' : (desbloq ? 'disponible' : 'bloqueado'));
    nodo.className = `nivel-nodo ${claseEstado}`;

    // Imagen del nivel (si existe para esta materia)
    const imgSrc = _imagenNivel(clave, i);
    if (imgSrc) {
      const img = document.createElement('img');
      img.src = imgSrc;
      img.alt = `Nivel ${i}`;
      img.className = 'nivel-nodo-img';
      nodo.appendChild(img);
    } else {
      // Fallback: número
      nodo.innerHTML = `<span class="nivel-nodo-num">${i}</span>`;
    }

    // Overlay: bloqueado / completado
    if (!desbloq) {
      const lock = document.createElement('div');
      lock.className = 'nivel-nodo-overlay locked';
      lock.innerHTML = '<i class="fa-solid fa-lock"></i>';
      nodo.appendChild(lock);
    } else if (completado) {
      const check = document.createElement('div');
      check.className = 'nivel-nodo-overlay completed';
      check.innerHTML = `<i class="fa-solid fa-star"></i><span>${puntaje}</span>`;
      nodo.appendChild(check);
    }

    if (desbloq) {
      nodo.style.cursor = 'pointer';
      nodo.addEventListener('click', () => mostrarMision(i));
    }

    const nombre = document.createElement('div');
    nombre.className = 'nivel-nombre';
    nombre.textContent = NOMBRES_NIVEL[i - 1];

    const wrapper = document.createElement('div');
    wrapper.style.display = 'flex';
    wrapper.style.flexDirection = 'column';
    wrapper.style.alignItems = 'center';
    wrapper.appendChild(nodo);
    wrapper.appendChild(nombre);
    paso.appendChild(wrapper);

    // Línea conectora
    if (i < 5) {
      const linea = document.createElement('div');
      linea.className = `nivel-linea${desbloq ? ' activa' : ''}`;
      paso.appendChild(linea);
    }
    camino.appendChild(paso);
  }

  mostrarPantalla('screen-level-select');

  // ── Precarga de historias + audio en background ───────────────────────────
  _precargarHistorias(clave);
}

/**
 * Devuelve la ruta de imagen del nodo de nivel para una materia dada.
 * Si no hay imagen específica devuelve null (usa fallback numérico).
 */
function _imagenNivel(materia, nivel) {
  const mapas = {
    matematicas: {
      1: '/static/images/level_matematicas/level1Mat.png',
      2: '/static/images/level_matematicas/level2Mat.png',
      3: '/static/images/level_matematicas/level3Mat.png',
      4: '/static/images/level_matematicas/level4Mat.png',
      5: '/static/images/level_matematicas/level5Mat.png',
    },
  };
  return (mapas[materia] || {})[nivel] || null;
}

/**
 * Devuelve la imagen de fondo de la pantalla "¡Nueva Misión!" para una materia y nivel.
 */
function _imagenMision(materia, nivel) {
  const mapa = {
    matematicas: '/static/images/level_matematicas/explicaNiv2-5Mat.png',
    lenguaje:    '/static/images/level_lenguaje/explicaNivLen.png',
    ingles:      '/static/images/level_ingles/explicaNivIng.png',
    biologia:    '/static/images/level_biologia/explicaNivBio.png',
  };
  return mapa[materia] || null;
}

// Función global accesible desde el onclick inline del botón (más confiable que addEventListener)
window.__volverAlMenu = function() {
  console.log('[Menú] Click detectado, navegando…');
  // Navegar inmediatamente — no esperar nada.
  mostrarMenu();
  // Actualizar progreso en background, sin bloquear nada.
  cargarProgreso().then(mostrarMenu).catch(() => {});
};
// Mantener el listener anterior como respaldo
document.getElementById('btn-volver-menu').addEventListener('click', window.__volverAlMenu);

// ── PANTALLA 4: Nueva Misión ─────────────────────────────────────────────────
async function mostrarMision(nivel) {
  Estado.nivelActivo = nivel;

  const per    = PERSONAJES[Estado.materiaActiva];
  const screen = document.getElementById('screen-mision');
  const textoEl = document.getElementById('mision-historia-texto');

  // ── Fondo de la pantalla ──────────────────────────────────────────
  const bgEl  = document.getElementById('mision-bg');
  const bgImg = _imagenMision(Estado.materiaActiva, nivel);
  if (bgImg) {
    bgEl.style.backgroundImage = `url('${bgImg}')`;
    bgEl.style.backgroundSize  = 'cover';
    bgEl.style.backgroundPosition = 'center center';
    screen.classList.add('mision-con-imagen');
  } else {
    bgEl.style.backgroundImage = '';
    screen.classList.remove('mision-con-imagen');
  }

  // Spinner mientras esperamos
  textoEl.innerHTML = `<span class="mision-loading"><i class="fa-solid fa-spinner fa-spin"></i> ${per.nombre} prepara tu misión...</span>`;
  _ttsOcultarBtn();
  mostrarPantalla('screen-mision');

  // ── Intentar usar cache precargado, o esperar la precarga en curso ────────
  const cacheKey = `${Estado.materiaActiva}-${nivel}`;
  let cached = _historiaCache.get(cacheKey);

  if (cached === 'loading') {
    // Ya está en camino — esperar hasta 35 segundos (Ollama puede tardar ~20-30s)
    for (let i = 0; i < 175 && cached === 'loading'; i++) {
      await new Promise(r => setTimeout(r, 200));
      cached = _historiaCache.get(cacheKey);
    }
  }

  if (cached && cached !== 'loading' && cached.historia) {
    // ✅ Cache hit: el texto aparece de inmediato
    Estado.nivelDatos = cached.datos || Estado.nivelDatos;
    textoEl.innerHTML = '';
    await _escribirTexto(textoEl, cached.historia);
    // El audio se carga aparte (no bloquea el texto)
    _prepararAudioMision(cached.historia, cached.audioUrl, cacheKey);
    return;
  }

  // ── Fallback: fetch directo si el cache no está listo ────────────────────
  try {
    const datos = await api('GET', `/api/niveles/${Estado.materiaActiva}/${nivel}`);
    Estado.nivelDatos = datos;
    const res = await api('POST', '/api/ia/historia_nivel', {
      materia:      Estado.materiaActiva,
      nivel,
      personaje:    datos.personaje || per.nombre,
      instruccion:  datos.instruccion || '',
      nombre_nivel: NOMBRES_NIVEL[nivel - 1] || '',
      minijuego:    datos.minijuego || '',
    });
    const historia = res.historia || res.respuesta || datos.frase_intro || '¡Adelante, aventurero!';
    // Guardar texto en caché de inmediato
    _historiaCache.set(cacheKey, { historia, audioUrl: res.audioUrl || null, datos });
    textoEl.innerHTML = '';
    await _escribirTexto(textoEl, historia);
    // Cargar audio aparte (no bloquea el texto)
    _prepararAudioMision(historia, res.audioUrl, cacheKey);
  } catch (_) {
    const datos = Estado.nivelDatos || {};
    const fallback = datos.frase_intro || '¡Adelante, aventurero del Pacífico!';
    textoEl.textContent = fallback;
    _ttsOcultarBtn();
  }
}

/**
 * Prepara el audio de la misión SIN bloquear el texto.
 * Si ya hay URL cacheada la usa; si no, la pide al servidor mostrando el botón
 * en estado "cargando" y lo habilita cuando el audio esté listo.
 */
async function _prepararAudioMision(texto, audioUrlCacheado, cacheKey) {
  _ttsAudioUrl = null;
  const btn = document.getElementById('btn-tts-mision');

  if (audioUrlCacheado) {
    _ttsAudioUrl = audioUrlCacheado;
    _ttsMostrarBtn();
    return;
  }

  // Mostrar botón en estado "cargando audio…"
  if (btn) {
    btn.classList.remove('hidden', 'tts-hablando');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    btn.setAttribute('disabled', 'disabled');
    btn.title = 'Preparando audio…';
  }

  try {
    const res = await api('POST', '/api/ia/tts', { texto });
    if (res && res.audioUrl) {
      _ttsAudioUrl = res.audioUrl;
      // Actualizar la entrada de caché para que la próxima vez sea instantánea
      if (cacheKey) {
        const entry = _historiaCache.get(cacheKey);
        if (entry && typeof entry === 'object') { entry.audioUrl = res.audioUrl; _historiaCache.set(cacheKey, entry); }
      }
      if (btn) { btn.removeAttribute('disabled'); btn.title = 'Escuchar historia'; }
      _ttsMostrarBtn();
    } else {
      if (btn) btn.classList.add('hidden');
    }
  } catch (_) {
    if (btn) btn.classList.add('hidden');
  }
}

/** Efecto de escritura carácter a carácter. Cancela cualquier animación previa. */
let _escribirIntervalId = null;
function _escribirTexto(el, texto, velMs = 18) {
  // Cancelar animación anterior si existe
  if (_escribirIntervalId !== null) {
    clearInterval(_escribirIntervalId);
    _escribirIntervalId = null;
  }
  return new Promise(resolve => {
    let i = 0;
    el.textContent = '';
    _escribirIntervalId = setInterval(() => {
      if (i < texto.length) {
        el.textContent += texto[i++];
      } else {
        clearInterval(_escribirIntervalId);
        _escribirIntervalId = null;
        resolve();
      }
    }, velMs);
  });
}

/** Ruta de imagen del personaje si existe como PNG */
function _imagenPersonaje(materia) {
  const map = {
    matematicas: '/static/images/level_matematicas/riviel.png',
  };
  return map[materia] || null;
}

// Compatibilidad: alias para el flujo de restauración de estado
async function mostrarPersonaje(nivel) { return mostrarMision(nivel); }

// ── Precarga de historias + audio (background, al abrir selector de niveles) ──
const _historiaCache = new Map(); // clave: `${materia}-${nivel}` → {historia, audioUrl, datos} | 'loading'

async function _precargarHistorias(materia) {
  // FASE 1: precargar TODOS los textos primero (rápido, curado). Así cualquier
  // nivel que el usuario toque ya tiene su texto listo de inmediato.
  for (let nivel = 1; nivel <= 5; nivel++) {
    const k = `${materia}-${nivel}`;
    if (_historiaCache.has(k)) continue; // ya en caché o cargando
    _historiaCache.set(k, 'loading');
    await _precargarTexto(materia, nivel, k);
  }
  // FASE 2: calentar los audios en background (sin bloquear). Cuando termina,
  // el botón de audio del nivel ya estará instantáneo.
  for (let nivel = 1; nivel <= 5; nivel++) {
    _calentarAudioNivel(`${materia}-${nivel}`);
  }
}

async function _precargarTexto(materia, nivel, cacheKey) {
  try {
    const datos = await api('GET', `/api/niveles/${materia}/${nivel}`);
    const per   = PERSONAJES[materia] || {};
    const res   = await api('POST', '/api/ia/historia_nivel', {
      materia, nivel,
      personaje:    datos.personaje || per.nombre || '',
      instruccion:  datos.instruccion || '',
      nombre_nivel: NOMBRES_NIVEL[nivel - 1] || '',
      minijuego:    datos.minijuego || '',
    });
    const historia = res.historia || res.respuesta || datos.frase_intro || '';
    _historiaCache.set(cacheKey, { historia, audioUrl: res.audioUrl || null, datos });
    console.log(`[Precarga] Texto listo: ${cacheKey}`);
  } catch (e) {
    _historiaCache.delete(cacheKey); // permitir reintento
    console.warn(`[Precarga] Error: ${cacheKey}`, e);
  }
}

// Cola simple para no disparar 5 generaciones de audio a la vez
let _colaAudioPromise = Promise.resolve();
function _calentarAudioNivel(cacheKey) {
  const entry = _historiaCache.get(cacheKey);
  if (!entry || typeof entry !== 'object' || !entry.historia || entry.audioUrl) return;
  // Encadenar para que los audios se generen de uno en uno
  _colaAudioPromise = _colaAudioPromise.then(async () => {
    const e = _historiaCache.get(cacheKey);
    if (!e || typeof e !== 'object' || !e.historia || e.audioUrl) return;
    try {
      const tts = await api('POST', '/api/ia/tts', { texto: e.historia });
      if (tts && tts.audioUrl) {
        e.audioUrl = tts.audioUrl;
        _historiaCache.set(cacheKey, e);
        console.log(`[Precarga] Audio listo: ${cacheKey}`);
      }
    } catch (_) { /* se generará bajo demanda */ }
  });
}

// ── TTS offline usando elemento <audio> (el audio lo genera el servidor) ─────
let _ttsAudioUrl = null;

function _ttsGuardarAudio(audioUrl) { _ttsAudioUrl = audioUrl || null; }
// mantener alias por compat con código anterior
function _ttsGuardarTexto() {}

function _ttsMostrarBtn() {
  const btn = document.getElementById('btn-tts-mision');
  if (!btn) return;
  // Mostrar solo si hay URL de audio disponible
  if (_ttsAudioUrl) {
    btn.classList.remove('hidden');
    btn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
    btn.classList.remove('tts-hablando');
  } else {
    btn.classList.add('hidden');
  }
}

function _ttsOcultarBtn() {
  const btn = document.getElementById('btn-tts-mision');
  if (btn) btn.classList.add('hidden');
  _ttsDetener();
}

function _ttsDetener() {
  const audio = document.getElementById('mision-audio');
  if (audio && !audio.paused) {
    audio.pause();
    audio.currentTime = 0;
  }
  const btn = document.getElementById('btn-tts-mision');
  if (btn) {
    btn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
    btn.classList.remove('tts-hablando');
  }
}

function toggleTTS() {
  const audio = document.getElementById('mision-audio');
  if (!audio) return;

  if (!audio.paused) {
    // Detener
    _ttsDetener();
    return;
  }

  if (!_ttsAudioUrl) return;

  audio.src = _ttsAudioUrl;
  audio.load();
  audio.play()
    .then(() => {
      const btn = document.getElementById('btn-tts-mision');
      if (btn) { btn.innerHTML = '<i class="fa-solid fa-stop"></i>'; btn.classList.add('tts-hablando'); }
    })
    .catch(e => console.warn('[TTS] play error:', e));

  // Al terminar, restaurar icono
  audio.onended = _ttsDetener;
  audio.onerror = _ttsDetener;
}

document.getElementById('btn-jugar').addEventListener('click', () => { _ttsDetener(); iniciarMinijuego(); });
document.getElementById('btn-volver-level').addEventListener('click', () => { _ttsDetener(); seleccionarMateria(Estado.materiaActiva); });

// ── PANTALLA 5: Minijuego ────────────────────────────────────────────────────
async function iniciarMinijuego() {
  let claseFondo = `bg-juego-${Estado.materiaActiva}`;
  if (Estado.materiaActiva === 'matematicas' && Estado.nivelActivo > 1) {
    claseFondo = `bg-juego-matematicas-${Estado.nivelActivo}`;
  }
  actualizarFondo(claseFondo);
  const datos = Estado.nivelDatos;
  const area = document.getElementById('game-area');
  const minijuego = datos.minijuego;
  const screenMg = document.getElementById('screen-minijuego');
  const pistaBox = document.getElementById('ia-pista-box');

  if (typeof Estado.destruirMinijuego === 'function') {
    Estado.destruirMinijuego();
    Estado.destruirMinijuego = null;
  }

  screenMg.setAttribute('data-materia', Estado.materiaActiva);
  screenMg.classList.toggle('modo-atrapa-ranas', minijuego === 'atrapa_ranas');
  if (pistaBox) {
    pistaBox.classList.add('hidden');
    pistaBox.textContent = '';
  }

  if (minijuego === 'atrapa_ranas') {
    document.getElementById('instruccion-texto').textContent = datos.instruccion || '';
    Estado.puntajeActual = 0;
    actualizarPuntajeHUD(0);
    area.innerHTML = '';
    mostrarPantalla('screen-minijuego');
    Estado.destruirMinijuego = iniciarNivel(area, datos, (puntaje, metricas) => {
      Estado.destruirMinijuego = null;
      screenMg.classList.remove('modo-atrapa-ranas');
      manejarNivelCompletado(puntaje, metricas);
    });
    return;
  }

  Estado.puntajeActual = 100;
  actualizarPuntajeHUD(100);

  document.getElementById('instruccion-texto').textContent = datos.instruccion || '';
  area.innerHTML = '';

  mostrarPantalla('screen-minijuego');

  if (minijuego === 'point_and_click') {
    Estado.motorActivo = new MotorPointClick(area, datos.datos, actualizarPuntajeHUD);
  } else if (minijuego === 'drag_and_drop') {
    Estado.motorActivo = new MotorDragDrop(area, datos.datos, actualizarPuntajeHUD);
  } else if (minijuego === 'puzzle') {
    Estado.motorActivo = new MotorPuzzle(area, datos, actualizarPuntajeHUD);
  } else if (minijuego === 'mate2_pesca') {
    Estado.motorActivo = new MotorMate2(area, datos, actualizarPuntajeHUD);
  } else if (minijuego === 'mate3_marea') {
    Estado.motorActivo = new MotorMate3(area, datos, actualizarPuntajeHUD);
  } else if (minijuego === 'mate4_tesoro') {
    Estado.motorActivo = new MotorMate4(area, datos, actualizarPuntajeHUD);
  } else if (minijuego === 'mate5_reparto') {
    Estado.motorActivo = new MotorMate5(area, datos, actualizarPuntajeHUD);
  }

  area.addEventListener('nivel_completado', e => manejarNivelCompletado(e.detail.puntaje, e.detail.metricas), { once: true });
}

function actualizarPuntajeHUD(pts) {
  Estado.puntajeActual = Math.max(0, pts);
  document.getElementById('puntaje-display').textContent = Estado.puntajeActual;
}

document.getElementById('btn-salir-juego').addEventListener('click', () => {
  if (typeof Estado.destruirMinijuego === 'function') {
    Estado.destruirMinijuego();
    Estado.destruirMinijuego = null;
  }
  document.getElementById('screen-minijuego').classList.remove('modo-atrapa-ranas');
  seleccionarMateria(Estado.materiaActiva);
});

document.getElementById('btn-pedir-pista').addEventListener('click', pedirPistaIA);

async function pedirPistaIA() {
  const btn = document.getElementById('btn-pedir-pista');
  const box = document.getElementById('ia-pista-box');
  if (!Estado.nivelDatos || !box || !btn) return;

  const perName = PERSONAJES[Estado.materiaActiva]?.nombre || Estado.nivelDatos.personaje || '';
  box.classList.remove('hidden');
  box.innerHTML = '<i class="fa-solid fa-lightbulb"></i> Pensando una pista corta...';
  btn.disabled = true;

  try {
    const datos = await api('POST', '/api/ia/pista', {
      materia: Estado.materiaActiva,
      nivel: Estado.nivelActivo,
      personaje: perName,
      instruccion: Estado.nivelDatos.instruccion || '',
      minijuego: Estado.nivelDatos.minijuego || '',
    });
    const texto = datos.respuesta || 'Lee la instrucción con calma y prueba paso a paso.';
    const fuente = datos.fuente === 'ollama' || datos.fuente === 'cache' ? 'IA local' : 'modo offline';
    box.innerHTML = `<i class="fa-solid fa-lightbulb"></i><span>${texto}</span><small>${fuente}</small>`;
  } catch (_) {
    box.innerHTML = '<i class="fa-solid fa-lightbulb"></i><span>Lee la instrucción con calma y prueba paso a paso.</span><small>modo offline</small>';
  } finally {
    btn.disabled = false;
  }
}

// ── PANTALLA 6: Resultado ────────────────────────────────────────────────────
async function manejarNivelCompletado(puntaje, metricas) {
  actualizarFondo('bg-victoria');
  const pts = Math.max(0, puntaje);

  // Guardar puntaje y métricas en el servidor
  await api('POST', '/api/progreso/guardar', {
    estudiante_id: Estado.estudiante.id,
    materia: Estado.materiaActiva,
    nivel: Estado.nivelActivo,
    puntaje: pts,
    metricas: metricas || {},
  });

  await cargarProgreso();

  // Estrellas según puntaje
  let estrellasHtml = '';
  const numEstrellas = pts >= 90 ? 3 : (pts >= 60 ? 2 : 1);
  for (let i = 0; i < 3; i++) {
    if (i < numEstrellas) {
      estrellasHtml += '<i class="fa-solid fa-star" style="color:#FFD700; margin:0 4px;"></i>';
    } else {
      estrellasHtml += '<i class="fa-regular fa-star" style="color:rgba(255,255,255,0.25); margin:0 4px;"></i>';
    }
  }
  const titulo    = pts >= 90 ? '¡Increíble!' : (pts >= 60 ? '¡Muy bien!' : '¡Buen intento!');

  document.getElementById('resultado-emoji').innerHTML = pts >= 60
    ? '<i class="fa-solid fa-trophy" style="color:#FFD700;"></i>'
    : '<i class="fa-solid fa-award" style="color:#FFD700;"></i>';
  document.getElementById('resultado-titulo').textContent        = titulo;
  document.getElementById('resultado-sub').textContent           = `Nivel ${Estado.nivelActivo}: ${NOMBRES_NIVEL[Estado.nivelActivo-1]}`;
  document.getElementById('puntaje-resultado-display').textContent = `${pts} pts`;
  document.getElementById('resultado-estrellas').innerHTML     = estrellasHtml;

  // Retroalimentación IA (no bloquea la pantalla)
  const perName = PERSONAJES[Estado.materiaActiva]?.nombre || '';
  pedirRetroalimentacionIA(Estado.materiaActiva, Estado.nivelActivo, pts, perName);

  // Botón siguiente nivel
  const hayMas = Estado.nivelActivo < 5;
  const btnSig = document.getElementById('btn-siguiente-nivel');
  btnSig.style.display = hayMas ? 'block' : 'none';

  mostrarPantalla('screen-resultado');
}

document.getElementById('btn-siguiente-nivel').addEventListener('click', () => mostrarPersonaje(Estado.nivelActivo + 1));
document.getElementById('btn-volver-mapa').addEventListener('click', () => seleccionarMateria(Estado.materiaActiva));

// ── PANTALLA 7: Puntajes ─────────────────────────────────────────────────────
async function mostrarPuntajes() {
  const prog = Estado.progreso;
  const container = document.getElementById('tabla-puntajes');

  // Intentar obtener métricas detalladas
  let desempeno = null;
  try {
    desempeno = await api('GET', `/api/docente/estudiante/${Estado.estudiante.id}`);
  } catch(_) {}

  const ESTRELLAS = (pts) => {
    const n = pts >= 90 ? 3 : pts >= 60 ? 2 : pts > 0 ? 1 : 0;
    return [1,2,3].map(i =>
      `<i class="fa-${i <= n ? 'solid' : 'regular'} fa-star" style="color:${i <= n ? '#FFD700' : 'rgba(255,255,255,0.2)'}; font-size:0.9rem;"></i>`
    ).join('');
  };

  const filasMaterias = MATERIAS.map(mat => {
    const p = prog[mat.clave] || { puntajes: [0,0,0,0,0], completados: 0 };
    const puntajes = p.puntajes || [0,0,0,0,0];
    const total = puntajes.reduce((a,b) => a+b, 0);
    const dm = desempeno?.por_materia?.[mat.clave];

    const celdas = puntajes.map(pts =>
      `<td>${pts > 0
        ? `<div class="pts-cell"><span class="pts-badge">${pts}</span><div style="font-size:0.7rem;">${ESTRELLAS(pts)}</div></div>`
        : '<span class="pts-vacio">—</span>'
      }</td>`
    ).join('');

    const metricasFila = dm ? `
      <div class="pts-metricas">
        <span class="pts-met-item pts-ok"><i class="fa-solid fa-check"></i> ${dm.total_aciertos || 0}</span>
        <span class="pts-met-item pts-err"><i class="fa-solid fa-xmark"></i> ${dm.total_errores || 0}</span>
      </div>` : '';

    return `<tr>
      <td>
        <i class="${mat.icon}" style="margin-right:8px; color:var(--dorado);"></i>
        <strong>${mat.nombre}</strong>
        ${metricasFila}
      </td>
      ${celdas}
      <td><strong>${total > 0 ? total : '—'}</strong></td>
    </tr>`;
  }).join('');

  const totalGlobal = MATERIAS.reduce((acc, mat) => {
    const p = prog[mat.clave] || { puntajes: [0,0,0,0,0] };
    return acc + (p.puntajes || []).reduce((a,b) => a+b, 0);
  }, 0);

  container.innerHTML = `
    <div class="pts-resumen-header">
      <div class="pts-resumen-nombre">
        <i class="fa-solid fa-user-circle" style="color:var(--dorado); font-size:2rem;"></i>
        <span>${Estado.estudiante.nombre}</span>
      </div>
      <div class="pts-resumen-total">
        <i class="fa-solid fa-trophy" style="color:var(--dorado);"></i>
        <span>${totalGlobal} pts totales</span>
      </div>
    </div>
    <table class="tabla-puntajes">
      <thead>
        <tr>
          <th>Materia</th>
          ${[1,2,3,4,5].map(i => `<th>Niv. ${i}</th>`).join('')}
          <th>Total</th>
        </tr>
      </thead>
      <tbody>${filasMaterias}</tbody>
    </table>
    <p class="pts-leyenda"><i class="fa-solid fa-circle-info"></i> ✔ aciertos &nbsp;✖ errores por materia</p>`;

  mostrarPantalla('screen-puntajes');
}


document.getElementById('btn-volver-menu-scores').addEventListener('click', mostrarMenu);

// Botón Cambiar usuario (siempre activo) — función global accesible desde onclick inline
window.__cambiarUsuario = function() {
  console.log('[CambiarUsuario] Click detectado');
  try { localStorage.removeItem('pacifico_estado_v2'); } catch(e) {}
  // irALogin reinicia el flujo limpio
  irALogin();
};
document.getElementById('btn-cambiar-usuario').addEventListener('click', window.__cambiarUsuario);

// ── Inicializar ──────────────────────────────────────────────────────────────
initIntro();
