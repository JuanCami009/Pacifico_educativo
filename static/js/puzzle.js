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
      slot.innerHTML = `<span style="opacity:0.4"><i class="fa-solid fa-shapes"></i></span>`;
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
      
      // Icono de la tarjeta con FontAwesome
      const icon = document.createElement('i');
      icon.className = this._iconPorNombre(t.texto || t.nombre || '');
      card.appendChild(icon);

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
      icon.innerHTML = `<i class="${this._iconPorNombre(pieza.texto || pieza.nombre)}"></i>`;
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
      slot.innerHTML = `<span style="opacity:0.4"><i class="fa-solid fa-shapes"></i></span>`;
      
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

  /** Devuelve una clase de FontAwesome representativa según el nombre del elemento */
  _iconPorNombre(nombre) {
    const mapa = {
      // Ciclo mariposa
      huevo: 'fa-solid fa-egg',
      oruga: 'fa-solid fa-bug',
      crisalida: 'fa-solid fa-box',
      crisálida: 'fa-solid fa-box',
      mariposa: 'fa-solid fa-bugs',
      
      // Sombrero / Tejer
      'remojar': 'fa-solid fa-droplet',
      'tinturar': 'fa-solid fa-palette',
      'tejer': 'fa-solid fa-hands',
      
      // Números / Ordinales
      'first': 'fa-solid fa-1',
      'second': 'fa-solid fa-2',
      'third': 'fa-solid fa-3',
      'fourth': 'fa-solid fa-4',
    };

    const normalized = nombre.toLowerCase().trim();
    
    // Buscar coincidencia exacta
    for (const key in mapa) {
      if (normalized.includes(key)) {
        return mapa[key];
      }
    }

    // Fallbacks
    if (normalized.includes('1') || normalized.includes('uno') || normalized.includes('primer')) return 'fa-solid fa-1';
    if (normalized.includes('2') || normalized.includes('dos') || normalized.includes('segund')) return 'fa-solid fa-2';
    if (normalized.includes('3') || normalized.includes('tres') || normalized.includes('tercer')) return 'fa-solid fa-3';
    if (normalized.includes('4') || normalized.includes('cuatro') || normalized.includes('cuart')) return 'fa-solid fa-4';
    if (normalized.includes('5') || normalized.includes('cinco') || normalized.includes('quint')) return 'fa-solid fa-5';
    
    if (normalized.includes('huevo') || normalized.includes('egg')) return 'fa-solid fa-egg';
    if (normalized.includes('oruga') || normalized.includes('insecto') || normalized.includes('bug')) return 'fa-solid fa-bug';
    if (normalized.includes('mariposa') || normalized.includes('butterfly')) return 'fa-solid fa-bugs';
    if (normalized.includes('agua') || normalized.includes('remojar') || normalized.includes('lavar')) return 'fa-solid fa-droplet';
    if (normalized.includes('color') || normalized.includes('tinta') || normalized.includes('pintar')) return 'fa-solid fa-palette';
    
    // Letras/Sílaba corta
    if (normalized.length <= 5) return 'fa-solid fa-font';

    return 'fa-solid fa-square-poll-horizontal';
  }
}
