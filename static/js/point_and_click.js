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
    this.encontrados  = 0;
    this.totalCorrectos = this.items.filter(i => i.es_correcto).length;

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

      // Intentar mostrar imagen; si falla, usar emoji/texto
      const emoji = this._emojiPorNombre(item.nombre);
      if (item.imagen) {
        const img = document.createElement('img');
        img.src = item.imagen;
        img.alt = item.nombre;
        img.style.cssText = 'width:70px;height:70px;object-fit:contain;border-radius:8px;';
        img.onerror = () => { img.replaceWith(document.createTextNode(emoji)); };
        el.appendChild(img);
      } else {
        el.textContent = emoji;
      }

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

      if (this.encontrados >= this.totalCorrectos) {
        setTimeout(() => this._completar(), 600);
      }
    } else {
      // Error: temblor y penalización
      el.classList.add('error');
      this.puntaje -= 10;
      this.onPuntaje(this.puntaje);
      setTimeout(() => el.classList.remove('error'), 500);
    }
  }

  _completar() {
    // Emitir evento de nivel completado
    this.area.dispatchEvent(new CustomEvent('nivel_completado', {
      bubbles: true, detail: { puntaje: Math.max(0, this.puntaje) }
    }));
  }

  /** Devuelve un emoji representativo según el nombre del item */
  _emojiPorNombre(nombre) {
    const mapa = {
      cangrejo:'🦀', pez:'🐟', pez_azul:'🐟', pez_rojo:'🐠',
      rana:'🐸', piedra:'🪨', hoja:'🍃', arbol:'🌳', agua:'💧',
      ave:'🦜', mono:'🐒', ballena:'🐋', palma:'🌴', flor:'🌸',
      flor_roja:'🌺', mariposa_azul:'🦋', rana_verde:'🐸',
      reciclar:'♻️', sembrar_arbol:'🌱', basura_rio:'🗑️', talar_arbol:'🪓',
      canoa:'🛶', barco_metal:'🚢', submarino:'🤿',
      sol:'☀️', insecto:'🐛',
    };
    return mapa[nombre] || '❓';
  }
}
