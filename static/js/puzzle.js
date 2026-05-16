/**
 * puzzle.js - Motor del minijuego "Puzzle"
 * Modo "secuencia": ordenar tarjetas en el orden correcto.
 * Modo "completar": arrastrar piezas a sus ranuras destino.
 */
class MotorPuzzle {
  /**
   * @param {HTMLElement} area  - Contenedor #game-area
   * @param {Object} nivelDatos - Objeto completo del nivel (incluye modo y datos)
   * @param {Function} onPuntaje - Callback HUD
   */
  constructor(area, nivelDatos, onPuntaje) {
    this.area      = area;
    this.modo      = nivelDatos.modo || 'secuencia';
    this.datos     = nivelDatos.datos;
    this.onPuntaje = onPuntaje;
    this.puntaje   = 100;

    if (this.modo === 'secuencia') {
      this._initSecuencia();
    } else {
      this._initCompletar();
    }
  }

  // ── MODO SECUENCIA ────────────────────────────────────────────────────────
  _initSecuencia() {
    const tarjetas = Array.isArray(this.datos) ? this.datos : [];
    // Guardar el orden correcto (índice = posición correcta)
    this.orden_correcto = tarjetas.map((t, i) => i);
    // Mezclar para mostrar
    this.tarjetas_mezcladas = [...tarjetas].sort(() => Math.random() - 0.5);
    this.seleccionadas = []; // Índices en orden correcto de las tarjetas ya colocadas
    this.total = tarjetas.length;

    this._renderSecuencia(tarjetas);
  }

  _renderSecuencia(tarjetasOriginales) {
    this.area.innerHTML = '';
    this.area.style.flexDirection = 'column';
    this.area.style.gap = '20px';

    // Fila de slots vacíos (orden correcto)
    const filaSlots = document.createElement('div');
    filaSlots.style.cssText = 'display:flex;gap:12px;flex-wrap:wrap;justify-content:center;';
    filaSlots.innerHTML = '<div style="width:100%;text-align:center;opacity:0.7;font-size:0.85rem">ORDEN CORRECTO ↓</div>';

    this.slots = [];
    for (let i = 0; i < this.total; i++) {
      const slot = document.createElement('div');
      slot.className = 'puzzle-slot';
      slot.dataset.idx = i;
      slot.innerHTML = `<span style="opacity:0.4">${i + 1}</span>`;
      this.slots.push(slot);
      filaSlots.appendChild(slot);
    }

    // Fila de tarjetas mezcladas (para hacer clic)
    const filaTarjetas = document.createElement('div');
    filaTarjetas.style.cssText = 'display:flex;gap:12px;flex-wrap:wrap;justify-content:center;';
    filaTarjetas.innerHTML = '<div style="width:100%;text-align:center;opacity:0.7;font-size:0.85rem">TARJETAS → HAZ CLIC EN ORDEN</div>';

    this.tarjetas_mezcladas.forEach((t, i) => {
      const card = document.createElement('div');
      card.className = 'puzzle-tarjeta';
      card.dataset.idxReal = tarjetasOriginales.indexOf(t);
      const emoji = t.imagen ? '🖼️' : (t.texto ? '' : '❓');
      card.textContent = `${emoji}${t.texto || t.nombre || `Item ${i+1}`}`;
      card.addEventListener('click', () => this._clicarTarjeta(card, parseInt(card.dataset.idxReal)));
      filaTarjetas.appendChild(card);
    });

    this.area.appendChild(filaSlots);
    this.area.appendChild(filaTarjetas);
    this.siguienteSlot = 0;
  }

  _clicarTarjeta(card, idxReal) {
    if (card.classList.contains('usada')) return;

    // ¿Es la siguiente tarjeta correcta en la secuencia?
    if (idxReal === this.siguienteSlot) {
      // Correcto: llenar slot
      card.classList.add('usada');
      const slot = this.slots[this.siguienteSlot];
      slot.classList.add('ocupado');
      slot.textContent = card.textContent;
      this.siguienteSlot++;

      if (this.siguienteSlot >= this.total) {
        setTimeout(() => this._completar(), 500);
      }
    } else {
      // Error
      this.puntaje -= 10;
      this.onPuntaje(this.puntaje);
      card.style.borderColor = '#f44336';
      setTimeout(() => { card.style.borderColor = ''; }, 400);
    }
  }

  // ── MODO COMPLETAR ────────────────────────────────────────────────────────
  _initCompletar() {
    // Reusa lógica similar a drag_and_drop pero con ranuras fijas
    const piezas = this.datos.piezas || [];
    this.colocadas = 0;
    this.totalPiezas = piezas.length;
    this._renderCompletar(piezas);
  }

  _renderCompletar(piezas) {
    this.area.innerHTML = '';
    this.area.style.flexDirection = 'row';
    this.area.style.gap = '24px';
    this.area.style.alignItems = 'flex-start';

    // Panel de piezas sueltas
    const colPiezas = document.createElement('div');
    colPiezas.style.cssText = 'display:flex;flex-direction:column;gap:12px;align-items:center;flex:1;';
    colPiezas.innerHTML = '<strong style="opacity:0.7;font-size:0.85rem">PIEZAS SUELTAS</strong>';

    // Panel de ranuras (slots)
    const colSlots = document.createElement('div');
    colSlots.style.cssText = 'display:flex;flex-direction:column;gap:12px;align-items:center;flex:1;';
    colSlots.innerHTML = '<strong style="opacity:0.7;font-size:0.85rem">COLOCA AQUÍ</strong>';

    piezas.forEach((pieza, idx) => {
      const slotId = `slot_${idx}`;

      // Pieza arrastrable
      const el = document.createElement('div');
      el.className = 'pieza-drag';
      el.draggable = true;
      el.dataset.slotId = slotId;
      el.textContent = pieza.texto || pieza.nombre || `Pieza ${idx+1}`;
      el.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', slotId);
        el.classList.add('dragging');
      });
      el.addEventListener('dragend', () => el.classList.remove('dragging'));
      colPiezas.appendChild(el);

      // Slot destino
      const slot = document.createElement('div');
      slot.className = 'zona-drop';
      slot.dataset.slotId = slotId;
      slot.innerHTML = `<span style="opacity:0.5">Suelta aquí</span>`;
      slot.addEventListener('dragover', e => { e.preventDefault(); slot.classList.add('hover-ok'); });
      slot.addEventListener('dragleave', () => slot.classList.remove('hover-ok'));
      slot.addEventListener('drop', e => {
        e.preventDefault();
        slot.classList.remove('hover-ok');
        const idRecibido = e.dataTransfer.getData('text/plain');
        if (idRecibido === slotId) {
          // Correcto
          slot.classList.add('completada');
          slot.textContent = el.textContent + ' ✅';
          el.style.opacity = '0.3';
          el.draggable = false;
          this.colocadas++;
          if (this.colocadas >= this.totalPiezas) {
            setTimeout(() => this._completar(), 500);
          }
        } else {
          // Error
          this.puntaje -= 10;
          this.onPuntaje(this.puntaje);
          slot.style.borderColor = '#f44336';
          setTimeout(() => { slot.style.borderColor = ''; }, 400);
        }
      });
      colSlots.appendChild(slot);
    });

    this.area.appendChild(colPiezas);
    this.area.appendChild(colSlots);
  }

  // ── Completar nivel ───────────────────────────────────────────────────────
  _completar() {
    this.area.dispatchEvent(new CustomEvent('nivel_completado', {
      bubbles: true, detail: { puntaje: Math.max(0, this.puntaje) }
    }));
  }
}
