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

function initIntro() {
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
          } else if (st.pantallaActual === 'screen-personaje') {
            mostrarPersonaje(st.nivelActivo);
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
}

document.getElementById('btn-puntajes').addEventListener('click', mostrarPuntajes);

// ── PANTALLA 3: Selección de nivel ──────────────────────────────────────────
function seleccionarMateria(clave) {
  Estado.materiaActiva = clave;
  actualizarFondo(`bg-niveles-${clave}`);
  const mat  = MATERIAS.find(m => m.clave === clave);
  const per  = PERSONAJES[clave];
  const prog = Estado.progreso[clave] || { nivel_maximo: 1 };
  const nivelMax = prog.nivel_maximo || 1;

  // Encabezado
  document.getElementById('level-select-titulo').textContent = mat.nombre;
  document.getElementById('personaje-guia-banner').innerHTML =
    `<span style="font-size:2rem"><i class="${per.icon}" style="color:${per.color}"></i></span>
     <div style="margin-left:12px;"><strong>${per.nombre}</strong> te acompaña en esta aventura</div>`;

  // Círculos de nivel
  const camino = document.getElementById('niveles-camino');
  camino.innerHTML = '';
  for (let i = 1; i <= 5; i++) {
    const puntaje    = (prog.puntajes || [])[i - 1] || 0;
    const completado = puntaje > 0;
    const disponible = i === nivelMax && !completado;
    const desbloq    = i <= nivelMax;

    const paso = document.createElement('div');
    paso.className = 'nivel-paso';

    const circulo = document.createElement('div');
    const clase = completado ? 'completado' : (disponible ? 'disponible' : (desbloq ? 'disponible' : 'bloqueado'));
    circulo.className = `nivel-circulo ${clase}`;
    circulo.innerHTML = completado
      ? `<i class="fa-solid fa-star" style="color:#FFD700;"></i><br><small style="font-size:0.6rem; font-weight:800;">${puntaje}pts</small>`
      : (desbloq ? `${i}` : '<i class="fa-solid fa-lock" style="opacity:0.5;"></i>');

    if (desbloq) {
      circulo.style.cursor = 'pointer';
      circulo.addEventListener('click', () => mostrarPersonaje(i));
    }

    const nombre = document.createElement('div');
    nombre.className = 'nivel-nombre';
    nombre.textContent = NOMBRES_NIVEL[i - 1];

    const wrapper = document.createElement('div');
    wrapper.style.display = 'flex';
    wrapper.style.flexDirection = 'column';
    wrapper.style.alignItems = 'center';
    wrapper.appendChild(circulo);
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
}

document.getElementById('btn-volver-menu').addEventListener('click', () => {
  cargarProgreso().then(mostrarMenu);
});

// ── PANTALLA 4: Intro del personaje ─────────────────────────────────────────
async function mostrarPersonaje(nivel) {
  Estado.nivelActivo = nivel;
  const datos = await api('GET', `/api/niveles/${Estado.materiaActiva}/${nivel}`);
  Estado.nivelDatos = datos;

  const per = PERSONAJES[Estado.materiaActiva];
  document.getElementById('pers-emoji').innerHTML = `<i class="${per.icon}" style="color:${per.color}; font-size:4.5rem; text-shadow:0 0 20px rgba(255,255,255,0.2)"></i>`;
  document.getElementById('pers-nombre').textContent = datos.personaje || per.nombre;
  document.getElementById('pers-nivel').textContent  = `Nivel ${nivel}: ${NOMBRES_NIVEL[nivel-1]}`;
  document.getElementById('pers-frase').textContent  = datos.frase_intro || '¡Adelante, aventurero!';

  mostrarPantalla('screen-personaje');
}

document.getElementById('btn-jugar').addEventListener('click', iniciarMinijuego);
document.getElementById('btn-volver-level').addEventListener('click', () => seleccionarMateria(Estado.materiaActiva));

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

// Botón Cambiar usuario (siempre activo)
document.getElementById('btn-cambiar-usuario').addEventListener('click', irALogin);

// ── Inicializar ──────────────────────────────────────────────────────────────
initIntro();
