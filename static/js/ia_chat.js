/**
 * ia_chat.js - Módulo de chat con personajes IA para Pacífico Educativo.
 * Gestiona la pantalla de chat, envío de mensajes a /api/ia/chat
 * y retroalimentación post-nivel vía /api/ia/retroalimentacion.
 * Usa el Estado global y sigue las convenciones del proyecto.
 */

// ── Estado local del chat ────────────────────────────────────────────────────
const EstadoChat = {
  personaje:    null,   // nombre del personaje activo en el chat
  materia:      null,   // materia activa
  nivel:        0,      // nivel activo
  esperando:    false,  // true mientras espera respuesta de la IA
  iaDisponible: null,   // null = no verificado; true/false tras verificación
};

// ── Iconos de personaje ──────────────────────────────────────────────────────
const ICONOS_CHAT = {
  'El Riviel':        { icon: 'fa-solid fa-fire',       color: '#42A5F5' },
  'La Tunda':         { icon: 'fa-solid fa-leaf',        color: '#66BB6A' },
  'El Duende':        { icon: 'fa-solid fa-hat-wizard', color: '#CE93D8' },
  'La Madre de Agua': { icon: 'fa-solid fa-droplet',    color: '#4DD0E1' },
};

// ── Botones rápidos por personaje ────────────────────────────────────────────
const BOTONES_RAPIDOS = {
  'El Riviel': [
    { texto: '🔢 Hazme una pregunta', mensaje: 'Hazme una pregunta de matemáticas' },
    { texto: '📖 Cuéntame una historia', mensaje: 'Cuéntame una historia del río' },
    { texto: '💡 Necesito una pista', mensaje: 'Ayúdame con una pista del nivel' },
  ],
  'La Tunda': [
    { texto: '🔤 Hazme una pregunta', mensaje: 'Hazme una pregunta de lenguaje' },
    { texto: '🌿 Cuéntame una historia', mensaje: 'Cuéntame una historia del bosque' },
    { texto: '💡 Necesito ayuda', mensaje: 'Ayúdame con las palabras del nivel' },
  ],
  'El Duende': [
    { texto: '🇬🇧 Ask me a question', mensaje: 'Hazme una pregunta en inglés' },
    { texto: '📚 Tell me a story', mensaje: 'Cuéntame una historia en inglés' },
    { texto: '💡 I need help', mensaje: 'Help me with the English words' },
  ],
  'La Madre de Agua': [
    { texto: '🌊 Hazme una pregunta', mensaje: 'Hazme una pregunta de biología' },
    { texto: '🐋 Cuéntame una historia', mensaje: 'Cuéntame una historia del manglar' },
    { texto: '💡 Necesito una pista', mensaje: 'Ayúdame con los seres vivos' },
  ],
};

const BOTONES_RAPIDOS_DEFECTO = [
  { texto: '💬 Cuéntame algo', mensaje: 'Cuéntame algo interesante' },
  { texto: '📖 Una historia', mensaje: 'Cuéntame una historia corta' },
  { texto: '💡 Necesito ayuda', mensaje: 'Necesito ayuda con el nivel' },
];

// ── Verificar estado de la IA al cargar ───────────────────────────────────────
async function verificarEstadoIA() {
  try {
    const res = await fetch('/api/ia/estado');
    const datos = await res.json();
    EstadoChat.iaDisponible = datos.disponible;
    _actualizarBadgeIA(datos.disponible);
  } catch (_) {
    EstadoChat.iaDisponible = false;
    _actualizarBadgeIA(false);
  }
}

function _actualizarBadgeIA(disponible) {
  const badge = document.getElementById('ia-estado-badge');
  if (!badge) return;
  if (disponible) {
    badge.textContent = '🟢 IA activa';
    badge.classList.remove('ia-badge-offline');
    badge.classList.add('ia-badge-online');
  } else {
    badge.textContent = '🟡 Modo sin conexión';
    badge.classList.remove('ia-badge-online');
    badge.classList.add('ia-badge-offline');
  }
}

// ── Abrir pantalla de chat ───────────────────────────────────────────────────
/**
 * Abre la pantalla de chat con el personaje de la materia activa.
 * Se integra con el Estado global de app.js.
 */
function abrirChat() {
  const materia   = Estado.materiaActiva;
  const nivelDatos = Estado.nivelDatos;

  // Determinar personaje: del nivel cargado o del mapa de materias
  const mapPersonaje = {
    matematicas: 'El Riviel',
    lenguaje:    'La Tunda',
    ingles:      'El Duende',
    biologia:    'La Madre de Agua',
  };
  const nombrePersonaje = (nivelDatos && nivelDatos.personaje)
    ? nivelDatos.personaje
    : (mapPersonaje[materia] || 'El Riviel');

  EstadoChat.personaje = nombrePersonaje;
  EstadoChat.materia   = materia;
  EstadoChat.nivel     = Estado.nivelActivo || 0;

  _renderizarCabeceraChat(nombrePersonaje);
  _renderizarBotonesRapidos(nombrePersonaje);
  _limpiarMensajes();
  _agregarMensajePersonaje(_mensajeBienvenida(nombrePersonaje));

  verificarEstadoIA();
  mostrarPantalla('screen-ia-chat');
  actualizarFondo(`bg-juego-${materia || 'matematicas'}`);

  // Foco en el input
  setTimeout(() => {
    const inp = document.getElementById('chat-input');
    if (inp) inp.focus();
  }, 300);
}

function _mensajeBienvenida(personaje) {
  const bienvenidas = {
    'El Riviel':        '¡Hola, aventurero! Soy El Riviel 🌊 ¿En qué te puedo ayudar hoy?',
    'La Tunda':         '¡Bienvenido, pequeño! Soy La Tunda 🌿 ¿Qué quieres saber?',
    'El Duende':        '¡Hello, friend! Soy El Duende 🎩 ¡Pregúntame lo que quieras!',
    'La Madre de Agua': '¡Bienvenido, guardián! Soy la Madre de Agua 💧 ¿Cómo puedo ayudarte?',
  };
  return bienvenidas[personaje] || '¡Hola! ¿En qué te puedo ayudar? 🌟';
}

function _renderizarCabeceraChat(personaje) {
  const iconData = ICONOS_CHAT[personaje] || { icon: 'fa-solid fa-robot', color: '#FFD700' };
  const el = document.getElementById('chat-personaje-nombre');
  const ic = document.getElementById('chat-personaje-icon');
  if (el) el.textContent = personaje;
  if (ic) {
    ic.className = iconData.icon;
    ic.style.color = iconData.color;
  }
}

function _renderizarBotonesRapidos(personaje) {
  const contenedor = document.getElementById('chat-acciones-rapidas');
  if (!contenedor) return;
  const botones = BOTONES_RAPIDOS[personaje] || BOTONES_RAPIDOS_DEFECTO;
  contenedor.innerHTML = botones.map(b =>
    `<button class="chat-btn-rapido btn btn-ghost btn-sm"
             onclick="enviarMensajeRapido('${b.mensaje.replace(/'/g, "\\'")}')"
     >${b.texto}</button>`
  ).join('');
}

// ── Enviar mensajes ──────────────────────────────────────────────────────────
/**
 * Envía el mensaje del input del chat al endpoint de la IA.
 */
async function enviarMensajeChat() {
  if (EstadoChat.esperando) return;

  const input = document.getElementById('chat-input');
  const texto = (input.value || '').trim();
  if (!texto) return;

  input.value = '';
  _agregarMensajeUsuario(texto);
  await _pedirRespuestaIA(texto);
}

/**
 * Envía un mensaje predefinido (botón rápido) al chat.
 * @param {string} mensaje - Texto del mensaje a enviar.
 */
async function enviarMensajeRapido(mensaje) {
  if (EstadoChat.esperando) return;
  _agregarMensajeUsuario(mensaje);
  await _pedirRespuestaIA(mensaje);
}

async function _pedirRespuestaIA(mensaje) {
  EstadoChat.esperando = true;
  _deshabilitarInput(true);
  const idEscribiendo = _mostrarEscribiendo();

  try {
    const res = await fetch('/api/ia/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mensaje:   mensaje,
        personaje: EstadoChat.personaje,
        materia:   EstadoChat.materia,
        nivel:     EstadoChat.nivel,
      }),
    });

    _quitarEscribiendo(idEscribiendo);

    if (!res.ok) throw new Error('Error de red');

    const datos = await res.json();
    if (datos.error) throw new Error(datos.error);

    _agregarMensajePersonaje(datos.respuesta, datos.fuente);

  } catch (err) {
    _quitarEscribiendo(idEscribiendo);
    _agregarMensajePersonaje(
      '¡Ups! No pude responder ahora mismo. ¡Intenta de nuevo! 😅',
      'error'
    );
    console.warn('[Chat IA] Error:', err);
  } finally {
    EstadoChat.esperando = false;
    _deshabilitarInput(false);
  }
}

// ── Retroalimentación post-nivel ─────────────────────────────────────────────
/**
 * Pide retroalimentación IA al terminar un nivel y la agrega a la
 * pantalla de resultado. Se llama desde manejarNivelCompletado en app.js.
 */
async function pedirRetroalimentacionIA(materia, nivel, puntaje, personaje) {
  const contenedor = document.getElementById('ia-retroalimentacion-box');
  if (!contenedor) return;

  contenedor.classList.remove('hidden');
  contenedor.innerHTML = `
    <div class="ia-retro-escribiendo">
      <i class="fa-solid fa-robot" style="color:var(--dorado);margin-right:8px;"></i>
      <span class="chat-puntos"><span></span><span></span><span></span></span>
    </div>`;

  try {
    const res = await fetch('/api/ia/retroalimentacion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ personaje, materia, nivel, puntaje }),
    });
    const datos = await res.json();
    const texto = datos.respuesta || '¡Buen trabajo! 🌟';
    const icData = ICONOS_CHAT[personaje] || { icon: 'fa-solid fa-robot', color: '#FFD700' };
    contenedor.innerHTML = `
      <div class="ia-retro-burbuja">
        <i class="${icData.icon}" style="color:${icData.color};font-size:1.4rem;flex-shrink:0;"></i>
        <p class="ia-retro-texto">${_escaparHtml(texto)}</p>
      </div>`;
  } catch (_) {
    contenedor.classList.add('hidden');
  }
}

// ── Helpers de UI ────────────────────────────────────────────────────────────

function _limpiarMensajes() {
  const cont = document.getElementById('chat-mensajes');
  if (cont) cont.innerHTML = '';
}

function _agregarMensajeUsuario(texto) {
  const cont = document.getElementById('chat-mensajes');
  if (!cont) return;
  const div = document.createElement('div');
  div.className = 'chat-burbuja chat-burbuja-usuario';
  div.innerHTML = `<span class="chat-burbuja-texto">${_escaparHtml(texto)}</span>`;
  cont.appendChild(div);
  _scrollAbajo(cont);
}

function _agregarMensajePersonaje(texto, fuente = 'ia') {
  const cont = document.getElementById('chat-mensajes');
  if (!cont) return;
  const personaje = EstadoChat.personaje || 'IA';
  const icData = ICONOS_CHAT[personaje] || { icon: 'fa-solid fa-robot', color: '#FFD700' };

  const div = document.createElement('div');
  div.className = 'chat-burbuja chat-burbuja-personaje';
  div.innerHTML = `
    <div class="chat-avatar">
      <i class="${icData.icon}" style="color:${icData.color};"></i>
    </div>
    <div>
      <span class="chat-burbuja-nombre">${_escaparHtml(personaje)}</span>
      <span class="chat-burbuja-texto">${_escaparHtml(texto)}</span>
    </div>`;
  cont.appendChild(div);
  _scrollAbajo(cont);
}

function _mostrarEscribiendo() {
  const cont = document.getElementById('chat-mensajes');
  if (!cont) return null;
  const id = 'chat-escribiendo-' + Date.now();
  const div = document.createElement('div');
  div.id = id;
  div.className = 'chat-burbuja chat-burbuja-personaje chat-escribiendo-wrapper';
  const personaje = EstadoChat.personaje || 'IA';
  const icData = ICONOS_CHAT[personaje] || { icon: 'fa-solid fa-robot', color: '#FFD700' };
  div.innerHTML = `
    <div class="chat-avatar">
      <i class="${icData.icon}" style="color:${icData.color};"></i>
    </div>
    <div class="chat-puntos">
      <span></span><span></span><span></span>
    </div>`;
  cont.appendChild(div);
  _scrollAbajo(cont);
  return id;
}

function _quitarEscribiendo(id) {
  if (!id) return;
  const el = document.getElementById(id);
  if (el) el.remove();
}

function _scrollAbajo(contenedor) {
  requestAnimationFrame(() => {
    contenedor.scrollTop = contenedor.scrollHeight;
  });
}

function _deshabilitarInput(deshabilitar) {
  const input = document.getElementById('chat-input');
  const btn   = document.getElementById('chat-btn-enviar');
  if (input) input.disabled = deshabilitar;
  if (btn)   btn.disabled   = deshabilitar;
}

function _escaparHtml(texto) {
  return String(texto)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/\n/g, '<br>');
}
