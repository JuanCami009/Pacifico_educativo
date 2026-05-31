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
    // Métricas de desempeño
    this.aciertos  = 0;
    this.errores   = 0;
    this._inicio   = Date.now();

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
    
    // Contenedor principal del tablero de arrastre (usa estilos definidos en styles.css)
    const board = document.createElement('div');
    board.className = 'drag-board';

    // Columna de piezas (izquierda)
    const colPiezas = document.createElement('div');
    colPiezas.className = 'panel-piezas';
    
    const tituloPiezas = document.createElement('div');
    tituloPiezas.className = 'panel-titulo';
    tituloPiezas.textContent = 'Elementos';
    colPiezas.appendChild(tituloPiezas);

    const mezcladas = [...this.piezas].sort(() => Math.random() - 0.5);
    mezcladas.forEach(pieza => {
      const el = this._crearPieza(pieza);
      colPiezas.appendChild(el);
    });

    // Columna de zonas (derecha)
    const colZonas = document.createElement('div');
    colZonas.className = 'panel-zonas';
    
    const tituloZonas = document.createElement('div');
    tituloZonas.className = 'panel-titulo';
    tituloZonas.textContent = 'Destinos';
    colZonas.appendChild(tituloZonas);

    this.zonas.forEach(zona => {
      const el = this._crearZona(zona);
      colZonas.appendChild(el);
    });

    board.appendChild(colPiezas);
    board.appendChild(colZonas);
    this.area.appendChild(board);
  }

  _crearPieza(pieza) {
    const el = document.createElement('div');
    el.className = 'pieza-drag';
    el.draggable = true;
    el.dataset.id = pieza.nombre;
    el.dataset.destino = pieza.zona_destino;

    // Ícono SVG local del Pacífico
    const icon = document.createElement('div');
    icon.className = 'pieza-drag-icon';
    icon.innerHTML = PacificIcons.get(pieza.nombre);
    el.appendChild(icon);

    const text = document.createElement('span');
    text.textContent = pieza.nombre;
    el.appendChild(text);

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
    
    const indicator = document.createElement('span');
    indicator.className = 'zona-drop-indicator';
    indicator.textContent = 'Arrastra aquí';
    el.appendChild(indicator);

    const label = document.createElement('strong');
    label.className = 'zona-drop-label';
    label.textContent = zona.etiqueta;
    el.appendChild(label);

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
      elZona.innerHTML = `
        <span style="font-size:1.5rem; color:#4CAF50; margin-bottom:6px;"><i class="fa-solid fa-circle-check"></i></span>
        <strong class="zona-drop-label">${zona.etiqueta}</strong>
      `;
      this.colocadas++;
      this.aciertos++;

      // Desactivar pieza correspondiente
      document.querySelectorAll('.pieza-drag').forEach(p => {
        if (p.dataset.destino === zona.id) {
          p.style.opacity = '0.3';
          p.draggable = false;
        }
      });

      if (this.colocadas >= this.piezas.length) {
        setTimeout(() => this._completar(), 600);
      }
    } else {
      // Error
      this.puntaje -= 10;
      this.errores++;
      this.onPuntaje(this.puntaje);
      elZona.style.borderColor = '#f44336';
      elZona.style.boxShadow = '0 0 20px rgba(244, 67, 54, 0.4)';
      setTimeout(() => { 
        elZona.style.borderColor = ''; 
        elZona.style.boxShadow = '';
      }, 500);
    }
  }

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

}
