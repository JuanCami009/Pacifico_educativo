/**
 * ia_chat.js - Chat con personajes IA para Pacifico Educativo.
 * Usa /api/ia/chat, /api/ia/estado y /api/ia/retroalimentacion.
 */

const EstadoChat = {
  personaje: null,
  materia: null,
  nivel: 0,
  esperando: false,
  iaDisponible: null,
  modelo: null,
  fuente: null,
};

const ICONOS_CHAT = {
  'El Riviel':        { icon: 'fa-solid fa-fire',       color: '#42A5F5' },
  'La Tunda':         { icon: 'fa-solid fa-leaf',       color: '#66BB6A' },
  'El Duende':        { icon: 'fa-solid fa-hat-wizard', color: '#CE93D8' },
  'La Madre de Agua': { icon: 'fa-solid fa-droplet',    color: '#4DD0E1' },
};

const BOTONES_RAPIDOS = {
  'El Riviel': [
    { texto: 'Hazme una pregunta', mensaje: 'Hazme una pregunta de matematicas' },
    { texto: 'Cuentame una historia', mensaje: 'Cuentame una historia del rio' },
    { texto: 'Necesito una pista', mensaje: 'Ayudame con una pista del nivel' },
  ],
  'La Tunda': [
    { texto: 'Hazme una pregunta', mensaje: 'Hazme una pregunta de lenguaje' },
    { texto: 'Cuentame una historia', mensaje: 'Cuentame una historia del bosque' },
    { texto: 'Necesito ayuda', mensaje: 'Ayudame con las palabras del nivel' },
  ],
  'El Duende': [
    { texto: 'Ask me a question', mensaje: 'Hazme una pregunta en ingles' },
    { texto: 'Tell me a story', mensaje: 'Cuentame una historia en ingles' },
    { texto: 'I need help', mensaje: 'Help me with the English words' },
  ],
  'La Madre de Agua': [
    { texto: 'Hazme una pregunta', mensaje: 'Hazme una pregunta de biologia' },
    { texto: 'Cuentame una historia', mensaje: 'Cuentame una historia del manglar' },
    { texto: 'Necesito una pista', mensaje: 'Ayudame con los seres vivos' },
  ],
};

const BOTONES_RAPIDOS_DEFECTO = [
  { texto: 'Cuentame algo', mensaje: 'Cuentame algo interesante' },
  { texto: 'Una historia', mensaje: 'Cuentame una historia corta' },
  { texto: 'Necesito ayuda', mensaje: 'Necesito ayuda con el nivel' },
];

async function verificarEstadoIA() {
  try {
    const res = await fetch('/api/ia/estado');
    const datos = await res.json();
    EstadoChat.iaDisponible = datos.disponible;
    EstadoChat.modelo = datos.modelo || '';
    EstadoChat.fuente = datos.fuente || (datos.disponible ? 'ollama' : 'fallback');
    _actualizarBadgeIA(datos.disponible, EstadoChat.modelo);
  } catch (_) {
    EstadoChat.iaDisponible = false;
    EstadoChat.modelo = '';
    EstadoChat.fuente = 'fallback';
    _actualizarBadgeIA(false, '');
  }
}

function _actualizarBadgeIA(disponible, modelo) {
  const badge = document.getElementById('ia-estado-badge');
  if (!badge) return;
  if (disponible) {
    badge.textContent = `IA local activa${modelo ? ` · ${modelo}` : ''}`;
    badge.classList.remove('ia-badge-offline');
    badge.classList.add('ia-badge-online');
  } else {
    badge.textContent = modelo ? `Fallback offline · ${modelo}` : 'Fallback offline';
    badge.classList.remove('ia-badge-online');
    badge.classList.add('ia-badge-offline');
  }
}

function abrirChat() {
  const materia = Estado.materiaActiva;
  const nivelDatos = Estado.nivelDatos;
  const mapPersonaje = {
    matematicas: 'El Riviel',
    lenguaje: 'La Tunda',
    ingles: 'El Duende',
    biologia: 'La Madre de Agua',
  };
  const nombrePersonaje = (nivelDatos && nivelDatos.personaje)
    ? nivelDatos.personaje
    : (mapPersonaje[materia] || 'El Riviel');

  EstadoChat.personaje = nombrePersonaje;
  EstadoChat.materia = materia;
  EstadoChat.nivel = Estado.nivelActivo || 0;

  _renderizarCabeceraChat(nombrePersonaje);
  _renderizarBotonesRapidos(nombrePersonaje);
  _limpiarMensajes();
  _agregarMensajePersonaje(_mensajeBienvenida(nombrePersonaje));

  verificarEstadoIA();
  mostrarPantalla('screen-ia-chat');
  actualizarFondo(`bg-juego-${materia || 'matematicas'}`);

  setTimeout(() => {
    const inp = document.getElementById('chat-input');
    if (inp) inp.focus();
  }, 300);
}

function _mensajeBienvenida(personaje) {
  const bienvenidas = {
    'El Riviel': 'Hola, aventurero. Soy El Riviel. ¿En que te puedo ayudar hoy?',
    'La Tunda': 'Bienvenido, pequeno. Soy La Tunda. ¿Que quieres saber?',
    'El Duende': 'Hello, friend. Soy El Duende. Preguntame lo que quieras.',
    'La Madre de Agua': 'Bienvenido, guardian. Soy la Madre de Agua. ¿Como puedo ayudarte?',
  };
  return bienvenidas[personaje] || 'Hola. ¿En que te puedo ayudar?';
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

async function enviarMensajeChat() {
  if (EstadoChat.esperando) return;

  const input = document.getElementById('chat-input');
  const texto = (input.value || '').trim();
  if (!texto) return;

  input.value = '';
  _agregarMensajeUsuario(texto);
  await _pedirRespuestaIA(texto);
}

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
        mensaje,
        personaje: EstadoChat.personaje,
        materia: EstadoChat.materia,
        nivel: EstadoChat.nivel,
      }),
    });

    _quitarEscribiendo(idEscribiendo);
    if (!res.ok) throw new Error('Error de red');

    const datos = await res.json();
    if (datos.modelo) _actualizarBadgeIA(datos.fuente === 'ollama' || datos.fuente === 'cache', datos.modelo);
    _agregarMensajePersonaje(datos.respuesta, datos.fuente);
  } catch (err) {
    _quitarEscribiendo(idEscribiendo);
    _agregarMensajePersonaje(
      'Estoy en modo offline, pero puedo ayudarte: lee la instruccion con calma y prueba paso a paso.',
      'fallback'
    );
    console.warn('[Chat IA] Error:', err);
  } finally {
    EstadoChat.esperando = false;
    _deshabilitarInput(false);
  }
}

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
    const texto = datos.respuesta || 'Buen trabajo. Sigue practicando paso a paso.';
    if (datos.modelo) _actualizarBadgeIA(datos.fuente === 'ollama' || datos.fuente === 'cache', datos.modelo);
    const icData = ICONOS_CHAT[personaje] || { icon: 'fa-solid fa-robot', color: '#FFD700' };
    contenedor.innerHTML = `
      <div class="ia-retro-burbuja">
        <i class="${icData.icon}" style="color:${icData.color};font-size:1.4rem;flex-shrink:0;"></i>
        <p class="ia-retro-texto">${_escaparHtml(texto)}</p>
      </div>`;
  } catch (_) {
    contenedor.innerHTML = `
      <div class="ia-retro-burbuja">
        <i class="fa-solid fa-robot" style="color:#FFD700;font-size:1.4rem;flex-shrink:0;"></i>
        <p class="ia-retro-texto">Buen trabajo. Sigue practicando paso a paso.</p>
      </div>`;
  }
}

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
  const fuenteTxt = fuente === 'ollama' ? 'IA local' : (fuente === 'cache' ? 'IA local · cache' : (fuente === 'fallback' ? 'modo offline' : ''));

  const div = document.createElement('div');
  div.className = 'chat-burbuja chat-burbuja-personaje';
  div.innerHTML = `
    <div class="chat-avatar">
      <i class="${icData.icon}" style="color:${icData.color};"></i>
    </div>
    <div>
      <span class="chat-burbuja-nombre">${_escaparHtml(personaje)}</span>
      <span class="chat-burbuja-texto">${_escaparHtml(texto || 'Lee la instruccion con calma y prueba paso a paso.')}</span>
      ${fuenteTxt ? `<span class="chat-fuente">${fuenteTxt}</span>` : ''}
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
    <div>
      <span class="chat-burbuja-nombre">${_escaparHtml(personaje)}</span>
      <div class="chat-puntos"><span></span><span></span><span></span></div>
      <span class="chat-espera-texto">Pensando una respuesta corta...</span>
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
  const btn = document.getElementById('chat-btn-enviar');
  if (input) input.disabled = deshabilitar;
  if (btn) btn.disabled = deshabilitar;
}

function _escaparHtml(texto) {
  return String(texto)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/\n/g, '<br>');
}
