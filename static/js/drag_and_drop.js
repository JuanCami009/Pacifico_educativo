/**
 * drag_and_drop.js - Motor del minijuego "Arrastrar y Soltar"
 * El estudiante arrastra piezas hacia su zona destino correcta.
 * Usa la API nativa de HTML5 Drag & Drop.
 */
class MotorDragDrop {
  /**
   * @param {HTMLElement} area - Contenedor #game-area
   * @param {Object} datos - { piezas: [...], zonas: [...] }
   * @param {Function} onPuntaje - Callback HUD
   */
  constructor(area, datos, onPuntaje) {
    this.area      = area;
    this.piezas    = (datos.piezas || []).map(p => ({ ...p, colocada: false }));
    this.zonas     = (datos.zonas  || []).map(z => ({ ...z, ocupada: false }));
    this.onPuntaje = onPuntaje;
    this.puntaje   = 100;
    this.colocadas = 0;
    this.arrastrandoId = null;

    // Compatibilidad: si vienen en formato pares (tuples) del backend antiguo
    if (!datos.piezas && !datos.zonas && datos instanceof Array) {
      this._convertirPares(datos);
    }

    this._render();
  }

  _convertirPares(pares) {
    this.piezas = pares.map((p, i) => ({ nombre: p[0], zona_destino: `zona_${i}`, colocada: false }));
    this.zonas  = pares.map((p, i) => ({ id: `zona_${i}`, etiqueta: p[1], ocupada: false }));
  }

  _render() {
    this.area.innerHTML = '';
    this.area.style.flexDirection = 'row';
    this.area.style.alignItems = 'flex-start';
    this.area.style.gap = '24px';

    // Columna de piezas (izquierda)
    const colPiezas = document.createElement('div');
    colPiezas.style.cssText = 'display:flex;flex-direction:column;gap:12px;flex:1;align-items:center;';
    colPiezas.innerHTML = '<strong style="opacity:0.7;font-size:0.85rem">ARRASTRA ➜</strong>';

    const mezcladas = [...this.piezas].sort(() => Math.random() - 0.5);
    mezcladas.forEach(pieza => {
      const el = this._crearPieza(pieza);
      colPiezas.appendChild(el);
    });

    // Columna de zonas (derecha)
    const colZonas = document.createElement('div');
    colZonas.style.cssText = 'display:flex;flex-direction:column;gap:12px;flex:1;align-items:center;';
    colZonas.innerHTML = '<strong style="opacity:0.7;font-size:0.85rem">ZONAS DESTINO</strong>';

    this.zonas.forEach(zona => {
      const el = this._crearZona(zona);
      colZonas.appendChild(el);
    });

    this.area.appendChild(colPiezas);
    this.area.appendChild(colZonas);
  }

  _crearPieza(pieza) {
    const el = document.createElement('div');
    el.className = 'pieza-drag';
    el.draggable = true;
    el.dataset.id = pieza.nombre;
    el.dataset.destino = pieza.zona_destino;

    const emoji = this._emoji(pieza.nombre);
    el.innerHTML = `${emoji} ${pieza.nombre}`;

    el.addEventListener('dragstart', e => {
      this.arrastrandoId = pieza.zona_destino;
      el.classList.add('dragging');
      e.dataTransfer.setData('text/plain', pieza.zona_destino);
      e.dataTransfer.effectAllowed = 'move';
    });
    el.addEventListener('dragend', () => el.classList.remove('dragging'));

    return el;
  }

  _crearZona(zona) {
    const el = document.createElement('div');
    el.className = 'zona-drop';
    el.dataset.id = zona.id;
    el.innerHTML = `<span style="opacity:0.6;font-size:0.8rem">Suelta aquí</span><br><strong>${zona.etiqueta}</strong>`;

    el.addEventListener('dragover', e => {
      e.preventDefault();
      if (!zona.ocupada) el.classList.add('hover-active');
    });
    el.addEventListener('dragleave', () => el.classList.remove('hover-active'));
    el.addEventListener('drop', e => {
      e.preventDefault();
      el.classList.remove('hover-active');
      const idDestino = e.dataTransfer.getData('text/plain');
      this._soltar(zona, idDestino, el);
    });

    return el;
  }

  _soltar(zona, idDestino, elZona) {
    if (zona.ocupada) return;

    if (idDestino === zona.id) {
      // Correcto
      zona.ocupada = true;
      elZona.classList.add('completada');
      elZona.innerHTML = `<span style="font-size:1.5rem">✅</span><br><strong>${zona.etiqueta}</strong>`;
      this.colocadas++;

      // Desactivar pieza correspondiente
      document.querySelectorAll('.pieza-drag').forEach(p => {
        if (p.dataset.destino === zona.id) {
          p.style.opacity = '0.4';
          p.draggable = false;
        }
      });

      if (this.colocadas >= this.piezas.length) {
        setTimeout(() => this._completar(), 600);
      }
    } else {
      // Error
      this.puntaje -= 10;
      this.onPuntaje(this.puntaje);
      elZona.style.borderColor = '#f44336';
      setTimeout(() => { elZona.style.borderColor = ''; }, 500);
    }
  }

  _completar() {
    this.area.dispatchEvent(new CustomEvent('nivel_completado', {
      bubbles: true, detail: { puntaje: Math.max(0, this.puntaje) }
    }));
  }

  _emoji(nombre) {
    const m = { pez:'🐟', mono:'🐒', ballena:'🐋', canoa:'🛶', pez_rojo:'🐠',
                rana:'🐸', hoja:'🍃', palma:'🌴', insecto:'🐛', sol:'☀️' };
    return m[nombre] || '📦';
  }
}
