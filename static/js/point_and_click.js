/**
 * point_and_click.js - Motor del minijuego "Señalar y Tocar"
 * El estudiante hace clic en los elementos correctos según la instrucción.
 * Puntaje máximo: 100. Se resta 10 por cada error. Mínimo: 0.
 */
class MotorPointClick {
  /**
   * @param {HTMLElement} area - Contenedor #game-area
   * @param {Object} datos - { items: [{imagen, es_correcto, nombre}] }
   * @param {Function} onPuntaje - Callback para actualizar el HUD
   */
  constructor(area, datos, onPuntaje) {
    this.area      = area;
    this.items     = datos.items || [];
    this.onPuntaje = onPuntaje;
    this.puntaje   = 100;
    this.encontrados    = 0;
    this.totalCorrectos = this.items.filter(i => i.es_correcto).length;
    // Métricas de desempeño
    this.aciertos  = 0;
    this.errores   = 0;
    this._inicio   = Date.now();

    this._render();
  }

  _render() {
    this.area.innerHTML = '';

    // Mezclar orden de los items
    const mezclados = [...this.items].sort(() => Math.random() - 0.5);

    mezclados.forEach(item => {
      const el = document.createElement('div');
      el.className = 'game-item';
      el.dataset.correcto = item.es_correcto;

      // Ícono SVG local del Pacífico (con contador si el nombre es "N <cosa>")
      const iconWrapper = document.createElement('div');
      iconWrapper.className = 'game-item-icon-wrapper';
      iconWrapper.innerHTML = this._renderIcon(item.nombre);
      el.appendChild(iconWrapper);

      const label = document.createElement('div');
      label.className = 'game-item-label';
      label.textContent = item.nombre;
      el.appendChild(label);

      el.addEventListener('click', () => this._clic(el, item));
      this.area.appendChild(el);
    });
  }

  _clic(el, item) {
    // Ignorar si ya fue seleccionado
    if (el.classList.contains('correcto') || el.classList.contains('error')) return;

    if (item.es_correcto) {
      el.classList.add('correcto');
      el.style.pointerEvents = 'none';
      this.encontrados++;
      this.aciertos++;

      // Agregar badge de acierto con FontAwesome check
      const badge = document.createElement('div');
      badge.className = 'game-item-feedback-badge correcto';
      badge.innerHTML = '<i class="fa-solid fa-check"></i>';
      el.appendChild(badge);

      if (this.encontrados >= this.totalCorrectos) {
        setTimeout(() => this._completar(), 600);
      }
    } else {
      // Error: temblor y penalización
      el.classList.add('error');
      this.puntaje -= 10;
      this.errores++;
      this.onPuntaje(this.puntaje);

      // Agregar badge de error con FontAwesome xmark
      const badge = document.createElement('div');
      badge.className = 'game-item-feedback-badge error';
      badge.innerHTML = '<i class="fa-solid fa-xmark"></i>';
      el.appendChild(badge);

      setTimeout(() => {
        el.classList.remove('error');
        el.style.pointerEvents = 'none';
        el.style.opacity = '0.5';
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

  /**
   * Renderiza un ícono. Si el nombre empieza con un número (ej. "3 peces",
   * "three frogs", "6 conchas"), genera un grupo de N íconos del concepto
   * — clave para que niveles como contar ranas / conchas se vean reales.
   */
  _renderIcon(nombre) {
    const n = (nombre || '').toLowerCase().trim();
    const palabras = { one:1, two:2, three:3, four:4, five:5, six:6, seven:7, eight:8, nine:9 };
    let count = 0;
    let resto = n;
    const mNum = n.match(/^(\d+)\s+(.+)$/);
    const mWord = n.match(/^(one|two|three|four|five|six|seven|eight|nine)\s+(.+)$/);
    if (mNum) { count = parseInt(mNum[1]); resto = mNum[2]; }
    else if (mWord) { count = palabras[mWord[1]]; resto = mWord[2]; }
    if (count > 1 && count <= 9) {
      return PacificIcons.getGroup(resto, count);
    }
    return PacificIcons.get(nombre);
  }
}
