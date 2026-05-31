/**
 * mate_niveles.js - Motores específicos para los niveles 2-5 de Matemáticas.
 *
 * Cada motor reproduce el contrato de los motores genéricos
 * (game-area + onPuntaje callback + dispatch de 'nivel_completado'),
 * pero con mecánica visual y temática mucho más rica:
 *   - múltiples rondas con dificultad progresiva
 *   - burbujas de diálogo de El Riviel
 *   - SVGs reales del Pacífico (PacificIcons)
 *   - animaciones de celebración (confeti, marea, pop)
 *
 * Exportados: MotorMate2 (suma), MotorMate3 (resta),
 *             MotorMate4 (multiplicación), MotorMate5 (división)
 */

// ────────────────────────────────────────────────────────────────────────
// Utilidades comunes
// ────────────────────────────────────────────────────────────────────────
const RivielFrases = {
  intro:   ['¡Vamos, navegante!', '¡La pesca espera!', 'Demuéstrame tu sabiduría del río.'],
  acierto: ['¡Excelente!', '¡Eso es!', '¡Bien hecho, mi joven amigo!', '¡El río te sonríe!'],
  error:   ['Casi... vuelve a intentarlo.', 'El río pide paciencia.', 'Mira con más calma.'],
  final:   ['¡Eres un verdadero hijo del Pacífico!', '¡Lo lograste!'],
};

function _rivielBurbuja(texto, opcionalRivielSrc) {
  const src = opcionalRivielSrc || '/static/images/level_matematicas/riviel.png';
  return `
    <div class="mate-personaje-burbuja">
      <img class="riviel" src="${src}" alt="El Riviel">
      <div class="burbuja-texto">${texto}</div>
    </div>
  `;
}

function _hudRonda(rondaActual, totalRondas) {
  return `
    <div class="mate-ronda-info">
      <img src="/static/images/icons/trofeo.svg" alt="">
      <span>Ronda ${rondaActual} / ${totalRondas}</span>
    </div>
  `;
}

function _aleatoria(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function _lanzarConfeti(area, n = 30) {
  const colores = ['#ffd54f', '#66bb6a', '#42a5f5', '#ef5350', '#ab47bc', '#ffa726'];
  for (let i = 0; i < n; i++) {
    const c = document.createElement('div');
    c.className = 'mate-confetti';
    c.style.left = `${Math.random() * 100}%`;
    c.style.top = '-20px';
    c.style.background = colores[i % colores.length];
    c.style.borderRadius = Math.random() > 0.5 ? '50%' : '4px';
    c.style.animationDelay = `${Math.random() * 0.6}s`;
    area.appendChild(c);
    setTimeout(() => c.remove(), 2400);
  }
}

function _shuffle(a) { return [...a].sort(() => Math.random() - 0.5); }

// ════════════════════════════════════════════════════════════════════════
// MATE NIVEL 2 — Pesca Abundante (Suma)
// Arrastra el grupo de N peces a la canoa cuya suma valga N.
// ════════════════════════════════════════════════════════════════════════
class MotorMate2 {
  constructor(area, datos, onPuntaje) {
    this.area = area;
    this.onPuntaje = onPuntaje;
    this.cfg = datos.configuracion || {};
    this.rondas = this.cfg.rondas || this._rondasPorDefecto();
    this.rondaIdx = 0;
    this.puntaje = 100;
    this.aciertos = 0;
    this.errores = 0;
    this._inicio = Date.now();
    this._render();
  }

  _rondasPorDefecto() {
    return [
      { grupos: [3, 5, 2], canoas: ['2+1', '3+2', '1+1'] },
      { grupos: [4, 6, 5], canoas: ['2+2', '3+3', '4+1'] },
      { grupos: [7, 8, 9], canoas: ['3+4', '5+3', '6+3'] },
    ];
  }

  _sumaDe(formula) {
    return formula.split('+').reduce((acc, x) => acc + parseInt(x.trim(), 10), 0);
  }

  _render() {
    this.area.innerHTML = '';
    const ronda = this.rondas[this.rondaIdx];

    const cont = document.createElement('div');
    cont.className = 'mate-game';
    cont.innerHTML = `
      ${_hudRonda(this.rondaIdx + 1, this.rondas.length)}
      ${_rivielBurbuja('¡Reparte la pesca! Arrastra cada grupo a la canoa cuya suma da esa cantidad.')}
      <div class="mate2-tablero">
        <div class="mate2-grupos" id="m2-grupos"></div>
        <div class="mate2-igual">=</div>
        <div class="mate2-canoas" id="m2-canoas"></div>
      </div>
    `;
    this.area.appendChild(cont);

    const grupos = _shuffle(ronda.grupos);
    const canoas = _shuffle(ronda.canoas);

    const colG = cont.querySelector('#m2-grupos');
    grupos.forEach(n => {
      const el = document.createElement('div');
      el.className = 'mate2-grupo';
      el.draggable = true;
      el.dataset.valor = n;
      el.innerHTML = PacificIcons.getGroup('pez', n);
      el.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', String(n));
        el.classList.add('dragging');
      });
      el.addEventListener('dragend', () => el.classList.remove('dragging'));
      colG.appendChild(el);
    });

    const colC = cont.querySelector('#m2-canoas');
    canoas.forEach(formula => {
      const el = document.createElement('div');
      el.className = 'mate2-canoa';
      el.dataset.formula = formula;
      el.dataset.suma = this._sumaDe(formula);
      el.textContent = formula;
      el.addEventListener('dragover', e => { e.preventDefault(); el.classList.add('hover-active'); });
      el.addEventListener('dragleave', () => el.classList.remove('hover-active'));
      el.addEventListener('drop', e => this._soltar(e, el));
      colC.appendChild(el);
    });

    this.completadasEnRonda = 0;
    this.totalEnRonda = canoas.length;
  }

  _soltar(e, canoaEl) {
    e.preventDefault();
    canoaEl.classList.remove('hover-active');
    if (canoaEl.classList.contains('completada')) return;

    const valor = parseInt(e.dataTransfer.getData('text/plain'), 10);
    const suma = parseInt(canoaEl.dataset.suma, 10);

    if (valor === suma) {
      canoaEl.classList.add('completada');
      canoaEl.innerHTML = `${canoaEl.dataset.formula} = <b>${suma}</b>`;
      this.aciertos++;
      this.completadasEnRonda++;

      const grupo = this.area.querySelector(`.mate2-grupo[data-valor="${valor}"]:not(.usada)`);
      if (grupo) { grupo.classList.add('usada'); grupo.style.opacity = '0.25'; grupo.draggable = false; }

      this._actualizarBurbuja(_aleatoria(RivielFrases.acierto));

      if (this.completadasEnRonda >= this.totalEnRonda) {
        setTimeout(() => this._siguienteRonda(), 700);
      }
    } else {
      this.puntaje = Math.max(0, this.puntaje - 5);
      this.errores++;
      this.onPuntaje(this.puntaje);
      canoaEl.classList.add('error');
      setTimeout(() => canoaEl.classList.remove('error'), 400);
      this._actualizarBurbuja(_aleatoria(RivielFrases.error));
    }
  }

  _actualizarBurbuja(texto) {
    const b = this.area.querySelector('.mate-personaje-burbuja .burbuja-texto');
    if (b) b.textContent = texto;
  }

  _siguienteRonda() {
    this.rondaIdx++;
    if (this.rondaIdx >= this.rondas.length) {
      _lanzarConfeti(this.area);
      setTimeout(() => this._completar(), 800);
    } else {
      this._render();
    }
  }

  _completar() {
    const duracion_seg = Math.round((Date.now() - this._inicio) / 1000);
    this.area.dispatchEvent(new CustomEvent('nivel_completado', {
      bubbles: true,
      detail: {
        puntaje: this.puntaje,
        metricas: { aciertos: this.aciertos, errores: this.errores, intentos: this.aciertos + this.errores, duracion_seg },
      },
    }));
  }
}

// ════════════════════════════════════════════════════════════════════════
// MATE NIVEL 3 — El Misterio de la Marea (Resta)
// La marea se lleva caracoles del manglar; el estudiante elige cuántos
// quedan tocando el número correcto.
// ════════════════════════════════════════════════════════════════════════
class MotorMate3 {
  constructor(area, datos, onPuntaje) {
    this.area = area;
    this.onPuntaje = onPuntaje;
    this.cfg = datos.configuracion || {};
    this.rondas = this.cfg.rondas || this._rondasPorDefecto();
    this.rondaIdx = 0;
    this.puntaje = 100;
    this.aciertos = 0;
    this.errores = 0;
    this._inicio = Date.now();
    this._render();
  }

  _rondasPorDefecto() {
    // Cada ronda: { inicial: N, marea: K }. Respuesta = inicial - marea
    return [
      { inicial: 5, marea: 2 },
      { inicial: 7, marea: 3 },
      { inicial: 9, marea: 4 },
      { inicial: 8, marea: 5 },
    ];
  }

  _opcionesPara(respuesta) {
    const set = new Set([respuesta]);
    while (set.size < 3) {
      const delta = (Math.random() < 0.5 ? -1 : 1) * (Math.floor(Math.random() * 3) + 1);
      const candidato = respuesta + delta;
      if (candidato >= 0 && candidato <= 9) set.add(candidato);
    }
    return _shuffle([...set]);
  }

  _render() {
    this.area.innerHTML = '';
    const ronda = this.rondas[this.rondaIdx];
    const respuesta = ronda.inicial - ronda.marea;

    const cont = document.createElement('div');
    cont.className = 'mate-game';
    cont.innerHTML = `
      ${_hudRonda(this.rondaIdx + 1, this.rondas.length)}
      ${_rivielBurbuja(`Había <b>${ronda.inicial}</b> caracoles en la arena. La marea se llevó <b>${ronda.marea}</b>. ¿Cuántos quedan?`)}
      <div class="mate3-escena">
        <div class="mate3-pregunta">${ronda.inicial} − ${ronda.marea} = ?</div>
        <div class="mate3-opciones" id="m3-opciones"></div>
        <div class="mate3-arena" id="m3-arena"></div>
        <div class="mate3-ola"></div>
      </div>
    `;
    this.area.appendChild(cont);

    // Pintar caracoles
    const arena = cont.querySelector('#m3-arena');
    for (let i = 0; i < ronda.inicial; i++) {
      const img = document.createElement('img');
      img.className = 'mate3-caracol';
      img.src = '/static/images/icons/caracol.png';
      img.alt = '';
      arena.appendChild(img);
    }

    // Animación: tras 800ms la marea barre K caracoles
    setTimeout(() => {
      const caracoles = arena.querySelectorAll('.mate3-caracol');
      const aBarrer = _shuffle([...caracoles]).slice(0, ronda.marea);
      aBarrer.forEach((c, i) => {
        setTimeout(() => c.classList.add('barrido'), i * 120);
      });
    }, 800);

    // Pintar opciones
    const opcs = cont.querySelector('#m3-opciones');
    const opciones = this._opcionesPara(respuesta);
    opciones.forEach(v => {
      const b = document.createElement('button');
      b.className = 'mate3-opcion';
      b.textContent = v;
      b.dataset.valor = v;
      b.addEventListener('click', () => this._elegir(b, v, respuesta));
      opcs.appendChild(b);
    });
  }

  _elegir(btn, valor, respuesta) {
    if (btn.classList.contains('correcta') || btn.disabled) return;
    if (valor === respuesta) {
      btn.classList.add('correcta');
      this.aciertos++;
      this.area.querySelectorAll('.mate3-opcion').forEach(b => b.disabled = true);
      this._actualizarBurbuja(_aleatoria(RivielFrases.acierto));
      setTimeout(() => this._siguienteRonda(), 900);
    } else {
      btn.classList.add('incorrecta');
      this.puntaje = Math.max(0, this.puntaje - 8);
      this.errores++;
      this.onPuntaje(this.puntaje);
      this._actualizarBurbuja(_aleatoria(RivielFrases.error));
      setTimeout(() => { btn.classList.remove('incorrecta'); btn.disabled = true; btn.style.opacity = '0.4'; }, 500);
    }
  }

  _actualizarBurbuja(texto) {
    const b = this.area.querySelector('.mate-personaje-burbuja .burbuja-texto');
    if (b) b.innerHTML = texto;
  }

  _siguienteRonda() {
    this.rondaIdx++;
    if (this.rondaIdx >= this.rondas.length) {
      _lanzarConfeti(this.area);
      setTimeout(() => this._completar(), 800);
    } else {
      this._render();
    }
  }

  _completar() {
    const duracion_seg = Math.round((Date.now() - this._inicio) / 1000);
    this.area.dispatchEvent(new CustomEvent('nivel_completado', {
      bubbles: true,
      detail: {
        puntaje: this.puntaje,
        metricas: { aciertos: this.aciertos, errores: this.errores, intentos: this.aciertos + this.errores, duracion_seg },
      },
    }));
  }
}

// ════════════════════════════════════════════════════════════════════════
// MATE NIVEL 4 — El Tesoro Multiplicado (Multiplicación)
// Toca los grupos de conchas cuyo número total coincide con el objetivo
// (ej. "encuentra los grupos de 6 = 2×3").
// ════════════════════════════════════════════════════════════════════════
class MotorMate4 {
  constructor(area, datos, onPuntaje) {
    this.area = area;
    this.onPuntaje = onPuntaje;
    this.cfg = datos.configuracion || {};
    this.rondas = this.cfg.rondas || this._rondasPorDefecto();
    this.rondaIdx = 0;
    this.puntaje = 100;
    this.aciertos = 0;
    this.errores = 0;
    this._inicio = Date.now();
    this._render();
  }

  _rondasPorDefecto() {
    // a x b = objetivo; el motor genera grupos correctos + distractores
    return [
      { a: 2, b: 3, distractores: [4, 5, 8] },
      { a: 2, b: 4, distractores: [6, 7, 9] },
      { a: 3, b: 3, distractores: [6, 8, 7] },
    ];
  }

  _render() {
    this.area.innerHTML = '';
    const r = this.rondas[this.rondaIdx];
    const objetivo = r.a * r.b;

    const cont = document.createElement('div');
    cont.className = 'mate-game';
    cont.innerHTML = `
      ${_hudRonda(this.rondaIdx + 1, this.rondas.length)}
      ${_rivielBurbuja(`¿Cuánto es <b>${r.a} × ${r.b}</b>? Toca los cofres con la respuesta.`)}
      <div class="mate4-objetivo">Pregunta: <b>${r.a}</b> × <b>${r.b}</b> = <b>?</b></div>
      <div class="mate4-grid" id="m4-grid"></div>
    `;
    this.area.appendChild(cont);

    // Construir lista: 1 correcto + 3 distractores
    const items = [
      { n: objetivo, ok: true },
      ...r.distractores.slice(0, 3).map(n => ({ n, ok: false })),
    ];
    this.correctos = items.filter(i => i.ok).length;
    this.encontrados = 0;

    const grid = cont.querySelector('#m4-grid');
    _shuffle(items).forEach(item => {
      const el = document.createElement('div');
      el.className = 'mate4-grupo';
      el.dataset.ok = item.ok;
      el.innerHTML = `
        ${PacificIcons.getGroup('concha', item.n)}
        <div class="mate4-formula">${item.n}</div>
      `;
      el.addEventListener('click', () => this._clic(el, item.ok));
      grid.appendChild(el);
    });
  }

  _etiquetaFalsa(n) {
    if (n === 4) return '2 × 2';
    if (n === 5) return '5 × 1';
    if (n === 6) return '6 × 1';
    if (n === 7) return '7 × 1';
    if (n === 8) return '2 × 4';
    if (n === 9) return '3 × 3';
    return `${n} conchas`;
  }

  _clic(el, ok) {
    if (el.classList.contains('correcto') || el.classList.contains('incorrecto')) return;
    if (ok) {
      el.classList.add('correcto');
      const b = document.createElement('div');
      b.className = 'mate4-badge ok';
      b.innerHTML = '<i class="fa-solid fa-check"></i>';
      el.appendChild(b);
      this.aciertos++;
      this.encontrados++;
      this._actualizarBurbuja(_aleatoria(RivielFrases.acierto));
      if (this.encontrados >= this.correctos) {
        setTimeout(() => this._siguienteRonda(), 700);
      }
    } else {
      el.classList.add('incorrecto');
      const b = document.createElement('div');
      b.className = 'mate4-badge err';
      b.innerHTML = '<i class="fa-solid fa-xmark"></i>';
      el.appendChild(b);
      this.puntaje = Math.max(0, this.puntaje - 8);
      this.errores++;
      this.onPuntaje(this.puntaje);
      this._actualizarBurbuja(_aleatoria(RivielFrases.error));
      setTimeout(() => { el.style.pointerEvents = 'none'; el.style.opacity = '0.45'; }, 500);
    }
  }

  _actualizarBurbuja(texto) {
    const b = this.area.querySelector('.mate-personaje-burbuja .burbuja-texto');
    if (b) b.innerHTML = texto;
  }

  _siguienteRonda() {
    this.rondaIdx++;
    if (this.rondaIdx >= this.rondas.length) {
      _lanzarConfeti(this.area);
      setTimeout(() => this._completar(), 800);
    } else {
      this._render();
    }
  }

  _completar() {
    const duracion_seg = Math.round((Date.now() - this._inicio) / 1000);
    this.area.dispatchEvent(new CustomEvent('nivel_completado', {
      bubbles: true,
      detail: {
        puntaje: this.puntaje,
        metricas: { aciertos: this.aciertos, errores: this.errores, intentos: this.aciertos + this.errores, duracion_seg },
      },
    }));
  }
}

// ════════════════════════════════════════════════════════════════════════
// MATE NIVEL 5 — El Reparto en el Pueblo (División)
// Arrastra los peces a las canastas; cada canasta debe terminar con N peces.
// ════════════════════════════════════════════════════════════════════════
class MotorMate5 {
  constructor(area, datos, onPuntaje) {
    this.area = area;
    this.onPuntaje = onPuntaje;
    this.cfg = datos.configuracion || {};
    this.rondas = this.cfg.rondas || this._rondasPorDefecto();
    this.rondaIdx = 0;
    this.puntaje = 100;
    this.aciertos = 0;
    this.errores = 0;
    this._inicio = Date.now();
    this._render();
  }

  _rondasPorDefecto() {
    // total / canastas = porCanasta
    return [
      { total: 6,  canastas: 3, porCanasta: 2 },
      { total: 12, canastas: 3, porCanasta: 4 },
      { total: 10, canastas: 2, porCanasta: 5 },
    ];
  }

  _render() {
    this.area.innerHTML = '';
    const r = this.rondas[this.rondaIdx];

    const cont = document.createElement('div');
    cont.className = 'mate-game';
    cont.innerHTML = `
      ${_hudRonda(this.rondaIdx + 1, this.rondas.length)}
      ${_rivielBurbuja(`Hoy hubo gran pesca: <b>${r.total}</b> peces para <b>${r.canastas}</b> canastas. ¡Repártelos por igual!`)}
      <div class="mate5-pila">
        <span class="mate5-pila-label">Pregunta: ${r.total} ÷ ${r.canastas} = ?</span>
        <div class="mate5-peces-pila" id="m5-pila"></div>
      </div>
      <div class="mate5-canastas" id="m5-canastas"></div>
      <div style="text-align: center; margin-top: 25px;">
        <button class="btn btn-primary btn-grande" id="m5-validar" style="width: auto; padding: 12px 40px; font-size: 1.8rem; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">¡Listo! <i class="fa-solid fa-check"></i></button>
      </div>
    `;
    this.area.appendChild(cont);
    
    const btnValidar = cont.querySelector('#m5-validar');
    btnValidar.addEventListener('click', () => this._validar());

    // Pila de peces arrastrables
    const pila = cont.querySelector('#m5-pila');
    for (let i = 0; i < r.total; i++) {
      const pezId = Math.floor(Math.random() * 5) + 1;
      const img = document.createElement('img');
      img.src = `/static/images/icons/pez${pezId}.png`;
      img.alt = '';
      img.draggable = true;
      img.dataset.id = `pez-${i}`;
      img.dataset.pezSrc = img.src;
      img.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', img.dataset.id);
        img.classList.add('dragging');
      });
      img.addEventListener('dragend', () => img.classList.remove('dragging'));
      pila.appendChild(img);
    }

    // Canastas
    const cont2 = cont.querySelector('#m5-canastas');
    this.canastas = [];
    for (let i = 0; i < r.canastas; i++) {
      const c = document.createElement('div');
      c.className = 'mate5-canasta';
      c.dataset.idx = i;
      c.dataset.cuenta = 0;
      c.innerHTML = `
        <div class="mate5-canasta-label">Canasta ${i + 1} &nbsp;|&nbsp; <span class="cuenta" style="color: #ffd54f;">0</span></div>
        <div class="mate5-canasta-peces"></div>
      `;
      c.addEventListener('dragover', e => { e.preventDefault(); c.classList.add('hover-active'); });
      c.addEventListener('dragleave', () => c.classList.remove('hover-active'));
      c.addEventListener('drop', e => this._soltar(e, c));
      cont2.appendChild(c);
      this.canastas.push(c);
    }
  }

  _soltar(e, canasta) {
    e.preventDefault();
    canasta.classList.remove('hover-active');
    const cuenta = parseInt(canasta.dataset.cuenta, 10);
    const id = e.dataTransfer.getData('text/plain');
    const pez = this.area.querySelector(`#m5-pila img[data-id="${id}"]`);
    if (!pez || pez.classList.contains('usada')) return;

    pez.classList.add('usada');
    pez.draggable = false;
    pez.style.opacity = '0.3';

    const nuevoPez = document.createElement('img');
    nuevoPez.src = pez.dataset.pezSrc || pez.src;
    canasta.querySelector('.mate5-canasta-peces').appendChild(nuevoPez);
    const nueva = cuenta + 1;
    canasta.dataset.cuenta = nueva;
    canasta.querySelector('.cuenta').textContent = `${nueva}`;
  }

  _validar() {
    const r = this.rondas[this.rondaIdx];
    const todosEnCanastas = Array.from(this.area.querySelectorAll('#m5-pila img')).every(img => img.classList.contains('usada'));
    const todasLlenas = this.canastas.every(c => parseInt(c.dataset.cuenta, 10) === r.porCanasta);

    if (todasLlenas && todosEnCanastas) {
      this.canastas.forEach(c => c.classList.add('completada'));
      this.aciertos++;
      this._actualizarBurbuja(_aleatoria(RivielFrases.acierto));
      setTimeout(() => this._siguienteRonda(), 1000);
    } else {
      this.errores++;
      this.puntaje = Math.max(0, this.puntaje - 10);
      this.onPuntaje(this.puntaje);
      this._actualizarBurbuja('Hmm, las cantidades no son correctas. ¡Inténtalo de nuevo!');
      this.canastas.forEach(c => c.classList.add('error'));
      setTimeout(() => {
        this.canastas.forEach(c => {
          c.classList.remove('error');
          c.dataset.cuenta = 0;
          c.querySelector('.cuenta').textContent = '0';
          c.querySelector('.mate5-canasta-peces').innerHTML = '';
        });
        const peces = this.area.querySelectorAll('#m5-pila img');
        peces.forEach(p => {
          p.classList.remove('usada');
          p.draggable = true;
          p.style.opacity = '1';
        });
      }, 1500);
    }
  }

  _actualizarBurbuja(texto) {
    const b = this.area.querySelector('.mate-personaje-burbuja .burbuja-texto');
    if (b) b.innerHTML = texto;
  }

  _siguienteRonda() {
    this.rondaIdx++;
    if (this.rondaIdx >= this.rondas.length) {
      _lanzarConfeti(this.area);
      setTimeout(() => this._completar(), 800);
    } else {
      this._render();
    }
  }

  _completar() {
    const duracion_seg = Math.round((Date.now() - this._inicio) / 1000);
    this.area.dispatchEvent(new CustomEvent('nivel_completado', {
      bubbles: true,
      detail: {
        puntaje: this.puntaje,
        metricas: { aciertos: this.aciertos, errores: this.errores, intentos: this.aciertos + this.errores, duracion_seg },
      },
    }));
  }
}

// Hacer disponibles globalmente
window.MotorMate2 = MotorMate2;
window.MotorMate3 = MotorMate3;
window.MotorMate4 = MotorMate4;
window.MotorMate5 = MotorMate5;
