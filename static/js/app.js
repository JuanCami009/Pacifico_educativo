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
  { clave: 'matematicas', nombre: 'Matemáticas', emoji: '🛶', personaje: 'El Riviel',
    grad: 'linear-gradient(135deg,#2E7D32,#1B5E20)' },
  { clave: 'lenguaje',    nombre: 'Lenguaje',    emoji: '🍃', personaje: 'La Tunda',
    grad: 'linear-gradient(135deg,#BF360C,#E65100)' },
  { clave: 'ingles',      nombre: 'Inglés',       emoji: '⭐', personaje: 'El Duende',
    grad: 'linear-gradient(135deg,#0D47A1,#1565C0)' },
  { clave: 'biologia',   nombre: 'Biología',     emoji: '🌿', personaje: 'La Madre de Agua',
    grad: 'linear-gradient(135deg,#00695C,#004D40)' },
];

const PERSONAJES = {
  matematicas: { nombre: 'El Riviel',       emoji: '🕯️',  color: '#42A5F5' },
  lenguaje:    { nombre: 'La Tunda',        emoji: '🌿',  color: '#66BB6A' },
  ingles:      { nombre: 'El Duende',       emoji: '🎩',  color: '#CE93D8' },
  biologia:    { nombre: 'La Madre de Agua',emoji: '💧',  color: '#4DD0E1' },
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
    'bg-juego-matematicas', 'bg-juego-lenguaje', 'bg-juego-ingles', 'bg-juego-biologia'
  ];
  document.body.classList.remove(...fondos);
  document.body.classList.add(clase);
}

// ── Helpers de API ───────────────────────────────────────────────────────────
async function api(metodo, ruta, cuerpo) {
  const ops = { method: metodo, headers: { 'Content-Type': 'application/json' } };
  if (cuerpo) ops.body = JSON.stringify(cuerpo);
  const res = await fetch(ruta, ops);
  return res.json();
}

// ── PANTALLA 1: Intro / Login ────────────────────────────────────────────────
function initIntro() {
  actualizarFondo('bg-intro');
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
    `<span style="font-size:2rem">${per.emoji}</span>
     <div><strong>${per.nombre}</strong> te acompaña en esta aventura</div>`;

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
      ? `⭐<br><small style="font-size:0.6rem">${puntaje}pts</small>`
      : (desbloq ? `${i}` : '🔒');

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
  document.getElementById('pers-emoji').textContent  = per.emoji;
  document.getElementById('pers-nombre').textContent = datos.personaje || per.nombre;
  document.getElementById('pers-nivel').textContent  = `Nivel ${nivel}: ${NOMBRES_NIVEL[nivel-1]}`;
  document.getElementById('pers-frase').textContent  = datos.frase_intro || '¡Adelante, aventurero!';

  mostrarPantalla('screen-personaje');
}

document.getElementById('btn-jugar').addEventListener('click', iniciarMinijuego);
document.getElementById('btn-volver-level').addEventListener('click', () => seleccionarMateria(Estado.materiaActiva));

// ── PANTALLA 5: Minijuego ────────────────────────────────────────────────────
async function iniciarMinijuego() {
  actualizarFondo(`bg-juego-${Estado.materiaActiva}`);
  const datos = Estado.nivelDatos;
  const area = document.getElementById('game-area');
  const minijuego = datos.minijuego;
  const screenMg = document.getElementById('screen-minijuego');

  if (typeof Estado.destruirMinijuego === 'function') {
    Estado.destruirMinijuego();
    Estado.destruirMinijuego = null;
  }

  screenMg.classList.toggle('modo-atrapa-ranas', minijuego === 'atrapa_ranas');

  if (minijuego === 'atrapa_ranas') {
    document.getElementById('instruccion-texto').textContent = datos.instruccion || '';
    Estado.puntajeActual = 0;
    actualizarPuntajeHUD(0);
    area.innerHTML = '';
    mostrarPantalla('screen-minijuego');
    Estado.destruirMinijuego = iniciarNivel(area, datos, (puntaje) => {
      Estado.destruirMinijuego = null;
      screenMg.classList.remove('modo-atrapa-ranas');
      manejarNivelCompletado(puntaje);
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
  }

  area.addEventListener('nivel_completado', e => manejarNivelCompletado(e.detail.puntaje), { once: true });
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

// ── PANTALLA 6: Resultado ────────────────────────────────────────────────────
async function manejarNivelCompletado(puntaje) {
  actualizarFondo('bg-victoria');
  const pts = Math.max(0, puntaje);

  // Guardar puntaje en el servidor
  await api('POST', '/api/progreso/guardar', {
    estudiante_id: Estado.estudiante.id,
    materia: Estado.materiaActiva,
    nivel: Estado.nivelActivo,
    puntaje: pts,
  });

  await cargarProgreso();

  // Estrellas según puntaje
  const estrellas = pts >= 90 ? '⭐⭐⭐' : pts >= 60 ? '⭐⭐' : '⭐';
  const titulo    = pts >= 90 ? '¡Increíble!' : pts >= 60 ? '¡Muy bien!' : '¡Buen intento!';

  document.getElementById('resultado-emoji').textContent         = pts >= 60 ? '🎉' : '💪';
  document.getElementById('resultado-titulo').textContent        = titulo;
  document.getElementById('resultado-sub').textContent           = `Nivel ${Estado.nivelActivo}: ${NOMBRES_NIVEL[Estado.nivelActivo-1]}`;
  document.getElementById('puntaje-resultado-display').textContent = `${pts} pts`;
  document.getElementById('resultado-estrellas').textContent     = estrellas;

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

  container.innerHTML = `
    <table class="tabla-puntajes">
      <thead>
        <tr>
          <th>Materia</th>
          ${[1,2,3,4,5].map(i => `<th>N${i}</th>`).join('')}
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
        ${MATERIAS.map(mat => {
          const p = prog[mat.clave] || { puntajes: [0,0,0,0,0] };
          const puntajes = p.puntajes || [0,0,0,0,0];
          const total = puntajes.reduce((a,b) => a+b, 0);
          const celdas = puntajes.map(pts =>
            `<td>${pts > 0 ? `<span class="pts-badge">${pts}</span>` : '<span class="pts-vacio">—</span>'}</td>`
          ).join('');
          return `<tr>
            <td>${mat.emoji} ${mat.nombre}</td>
            ${celdas}
            <td><strong>${total}</strong></td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>`;

  mostrarPantalla('screen-puntajes');
}

document.getElementById('btn-volver-menu-scores').addEventListener('click', mostrarMenu);

// ── Inicializar ──────────────────────────────────────────────────────────────
initIntro();
