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

      // Icon wrapper con FontAwesome en lugar de emojis o imágenes rotas
      const iconWrapper = document.createElement('div');
      iconWrapper.className = 'game-item-icon-wrapper';
      
      const icon = document.createElement('i');
      icon.className = this._iconPorNombre(item.nombre);
      iconWrapper.appendChild(icon);
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
    // Emitir evento de nivel completado
    this.area.dispatchEvent(new CustomEvent('nivel_completado', {
      bubbles: true, detail: { puntaje: Math.max(0, this.puntaje) }
    }));
  }

  /** Devuelve una clase de FontAwesome representativa según el nombre del item */
  _iconPorNombre(nombre) {
    const mapa = {
      // Animales/Flora
      cangrejo: 'fa-solid fa-shrimp',
      pez: 'fa-solid fa-fish',
      pez_azul: 'fa-solid fa-fish',
      pez_rojo: 'fa-solid fa-fish',
      rana: 'fa-solid fa-frog',
      rana_verde: 'fa-solid fa-frog',
      ave: 'fa-solid fa-crow',
      mono: 'fa-solid fa-paw',
      ballena: 'fa-solid fa-water',
      insecto: 'fa-solid fa-bug',
      sol: 'fa-solid fa-sun',
      hoja: 'fa-solid fa-leaf',
      palma: 'fa-solid fa-tree',
      arbol: 'fa-solid fa-tree',
      flor: 'fa-solid fa-seedling',
      flor_roja: 'fa-solid fa-seedling',
      mariposa_azul: 'fa-solid fa-bugs',
      
      // Objetos/Elementos
      piedra: 'fa-solid fa-circle',
      agua: 'fa-solid fa-droplet',
      reciclar: 'fa-solid fa-recycle',
      sembrar_arbol: 'fa-solid fa-seedling',
      basura_rio: 'fa-solid fa-trash-can',
      talar_arbol: 'fa-solid fa-scissors',
      canoa: 'fa-solid fa-ship',
      barco_metal: 'fa-solid fa-ship',
      submarino: 'fa-solid fa-compass',
      
      // English Counting
      'three frogs': 'fa-solid fa-frog',
      'two frogs': 'fa-solid fa-frog',
      'four frogs': 'fa-solid fa-frog',
      '3ranas': 'fa-solid fa-frog',
      '3ranas_b': 'fa-solid fa-frog',
      '2ranas': 'fa-solid fa-frog',
      '4ranas': 'fa-solid fa-frog',
      
      // Backgrounds
      river: 'fa-solid fa-water',
      mountain: 'fa-solid fa-mountain',
      sky: 'fa-solid fa-cloud',
      rio_1: 'fa-solid fa-water',
      rio_2: 'fa-solid fa-water',
      montana: 'fa-solid fa-mountain',
      cielo: 'fa-solid fa-cloud',
    };

    const normalized = nombre.toLowerCase().trim();
    if (mapa[normalized]) return mapa[normalized];
    
    // Fallbacks genéricos
    if (normalized.includes('pez') || normalized.includes('fish')) return 'fa-solid fa-fish';
    if (normalized.includes('rana') || normalized.includes('frog')) return 'fa-solid fa-frog';
    if (normalized.includes('árbol') || normalized.includes('arbol') || normalized.includes('tree')) return 'fa-solid fa-tree';
    if (normalized.includes('agua') || normalized.includes('río') || normalized.includes('rio') || normalized.includes('river')) return 'fa-solid fa-droplet';
    if (normalized.includes('basura') || normalized.includes('trash')) return 'fa-solid fa-trash-can';
    if (normalized.includes('canoa') || normalized.includes('barco') || normalized.includes('bote') || normalized.includes('boat')) return 'fa-solid fa-ship';
    if (normalized.includes('flor') || normalized.includes('sembrar') || normalized.includes('planta') || normalized.includes('flower')) return 'fa-solid fa-seedling';
    if (normalized.includes('mariposa') || normalized.includes('butterfly')) return 'fa-solid fa-bugs';
    
    return 'fa-solid fa-circle-question';
  }
}
