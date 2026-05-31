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
    // Métricas de desempeño (compartidas por ambos modos)
    this.aciertos  = 0;
    this.errores   = 0;
    this._inicio   = Date.now();

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
    
    const board = document.createElement('div');
    board.className = 'puzzle-board';

    // Fila de slots vacíos (orden correcto)
    const filaSlots = document.createElement('div');
    filaSlots.className = 'puzzle-slots-container';
    
    const tituloSlots = document.createElement('div');
    tituloSlots.className = 'panel-titulo';
    tituloSlots.style.width = '100%';
    tituloSlots.style.textAlign = 'center';
    tituloSlots.textContent = 'Orden Correcto';
    filaSlots.appendChild(tituloSlots);

    this.slots = [];
    for (let i = 0; i < this.total; i++) {
      const slot = document.createElement('div');
      slot.className = 'puzzle-slot';
      slot.dataset.idx = i;
      slot.innerHTML = `<span class="puzzle-slot-empty"><i class="fa-solid fa-shapes"></i></span>`;
      this.slots.push(slot);
      filaSlots.appendChild(slot);
    }

    // Fila de tarjetas mezcladas (para hacer clic)
    const filaTarjetas = document.createElement('div');
    filaTarjetas.className = 'puzzle-cards-container';
    
    const tituloTarjetas = document.createElement('div');
    tituloTarjetas.className = 'panel-titulo';
    tituloTarjetas.style.width = '100%';
    tituloTarjetas.style.textAlign = 'center';
    tituloTarjetas.textContent = 'Selecciona en Orden';
    filaTarjetas.appendChild(tituloTarjetas);

    this.tarjetas_mezcladas.forEach((t, i) => {
      const card = document.createElement('div');
      card.className = 'puzzle-tarjeta';
      card.dataset.idxReal = tarjetasOriginales.indexOf(t);
      
      // Icono SVG local del Pacífico (o texto si es palabra/sílaba)
      const nombreIcono = t.texto || t.nombre || '';
      const iconWrap = document.createElement('div');
      iconWrap.className = 'puzzle-card-icon';
      iconWrap.innerHTML = this._renderTarjeta(nombreIcono);
      card.appendChild(iconWrap);

      const txt = document.createElement('span');
      txt.textContent = t.texto || t.nombre || `Item ${i+1}`;
      card.appendChild(txt);

      card.addEventListener('click', () => this._clicarTarjeta(card, parseInt(card.dataset.idxReal)));
      filaTarjetas.appendChild(card);
    });

    board.appendChild(filaSlots);
    board.appendChild(filaTarjetas);
    this.area.appendChild(board);
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
      this.aciertos++;
      
      // Mover el contenido al slot
      slot.innerHTML = `
        <span style="font-size:1rem; color:#4CAF50; margin-bottom:4px;"><i class="fa-solid fa-circle-check"></i></span>
        <span style="font-size:0.8rem; font-weight:800; text-align:center;">${card.querySelector('span').textContent}</span>
      `;
      this.siguienteSlot++;

      if (this.siguienteSlot >= this.total) {
        setTimeout(() => this._completar(), 500);
      }
    } else {
      // Error
      this.puntaje -= 10;
      this.errores++;
      this.onPuntaje(this.puntaje);
      card.style.borderColor = '#f44336';
      card.style.boxShadow = '0 0 15px rgba(244, 67, 54, 0.4)';
      setTimeout(() => {
        card.style.borderColor = '';
        card.style.boxShadow = '';
      }, 400);
    }
  }

  // ── MODO COMPLETAR ────────────────────────────────────────────────────────
  _initCompletar() {
    const piezas = this.datos.piezas || [];
    this.colocadas = 0;
    this.totalPiezas = piezas.length;
    this._renderCompletar(piezas);
  }

  _renderCompletar(piezas) {
    this.area.innerHTML = '';
    
    const board = document.createElement('div');
    board.className = 'drag-board';

    // Panel de piezas sueltas
    const colPiezas = document.createElement('div');
    colPiezas.className = 'panel-piezas';
    
    const tituloPiezas = document.createElement('div');
    tituloPiezas.className = 'panel-titulo';
    tituloPiezas.textContent = 'Piezas';
    colPiezas.appendChild(tituloPiezas);

    // Panel de ranuras (slots)
    const colSlots = document.createElement('div');
    colSlots.className = 'panel-zonas';
    
    const tituloSlots = document.createElement('div');
    tituloSlots.className = 'panel-titulo';
    tituloSlots.textContent = 'Destinos';
    colSlots.appendChild(tituloSlots);

    piezas.forEach((pieza, idx) => {
      const slotId = `slot_${idx}`;

      // Pieza arrastrable
      const el = document.createElement('div');
      el.className = 'pieza-drag';
      el.draggable = true;
      el.dataset.slotId = slotId;

      const icon = document.createElement('div');
      icon.className = 'pieza-drag-icon';
      icon.innerHTML = this._renderTarjeta(pieza.texto || pieza.nombre || '');
      el.appendChild(icon);

      const text = document.createElement('span');
      text.textContent = pieza.texto || pieza.nombre || `Pieza ${idx+1}`;
      el.appendChild(text);

      el.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', slotId);
        el.classList.add('dragging');
      });
      el.addEventListener('dragend', () => el.classList.remove('dragging'));
      colPiezas.appendChild(el);

      // Slot destino
      const slot = document.createElement('div');
      slot.className = 'puzzle-slot';
      slot.dataset.slotId = slotId;
      slot.innerHTML = `<span class="puzzle-slot-empty"><i class="fa-solid fa-shapes"></i></span>`;
      
      slot.addEventListener('dragover', e => { 
        e.preventDefault(); 
        slot.classList.add('hover-ok'); 
      });
      slot.addEventListener('dragleave', () => slot.classList.remove('hover-ok'));
      slot.addEventListener('drop', e => {
        e.preventDefault();
        slot.classList.remove('hover-ok');
        const idRecibido = e.dataTransfer.getData('text/plain');
        if (idRecibido === slotId) {
          // Correcto
          slot.classList.add('ocupado');
          slot.innerHTML = `
            <span style="font-size:1.3rem; color:#4CAF50; margin-bottom:4px;"><i class="fa-solid fa-circle-check"></i></span>
            <strong class="zona-drop-label" style="font-size:0.85rem;">${pieza.texto || pieza.nombre}</strong>
          `;
          el.style.opacity = '0.3';
          el.draggable = false;
          this.colocadas++;
          this.aciertos++;
          if (this.colocadas >= this.totalPiezas) {
            setTimeout(() => this._completar(), 500);
          }
        } else {
          // Error
          this.puntaje -= 10;
          this.errores++;
          this.onPuntaje(this.puntaje);
          slot.style.borderColor = '#f44336';
          slot.style.boxShadow = '0 0 15px rgba(244, 67, 54, 0.4)';
          setTimeout(() => { 
            slot.style.borderColor = ''; 
            slot.style.boxShadow = '';
          }, 400);
        }
      });
      colSlots.appendChild(slot);
    });

    board.appendChild(colPiezas);
    board.appendChild(colSlots);
    this.area.appendChild(board);
  }

  // ── Completar nivel ───────────────────────────────────────────────────────
  _completar() {
    const duracion_seg = Math.round((Date.now() - this._inicio) / 1000);
    this.area.dispatchEvent(new CustomEvent('nivel_completado', {
      bubbles: true,
      detail: {
        puntaje: Math.max(0, this.puntaje),
        metricas: {
          aciertos:    this.aciertos,
          errores:     this.errores,
          intentos:    this.aciertos + this.errores,
          duracion_seg,
        },
      },
    }));
  }

  /**
   * Renderiza el contenido visual de una tarjeta/pieza del puzzle.
   *  - Si el texto es una palabra/sílaba pura (sólo letras) → tipografía grande,
   *    sin ícono (muy útil para Lenguaje "EL RÍO ES VIDA" o sílabas RIM/TA/GLAR).
   *  - Si el texto tiene un número al inicio (ej. "1. Sol") → ícono SVG del
   *    sustantivo + el número visible.
   *  - En cualquier otro caso → ícono SVG del concepto.
   */
  _renderTarjeta(texto) {
    const t = (texto || '').toString().trim();
    if (!t) return PacificIcons.get('brillo');

    // Sólo letras (con tildes/ñ) y espacios → es una palabra a leer
    if (/^[a-záéíóúñ ]+$/i.test(t) && t.length <= 14) {
      return `<span class="puzzle-card-texto">${t}</span>`;
    }
    // Patrón "1. Sol" / "2. Planta" → quita el prefijo numérico para escoger ícono
    const m = t.match(/^\s*\d+\s*[\.\)\-:]\s*(.+)$/);
    const concepto = m ? m[1] : t;
    return PacificIcons.get(concepto);
  }
}
