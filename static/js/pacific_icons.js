/**
 * pacific_icons.js - Sistema de íconos SVG locales (offline) del Pacífico.
 *
 * Reemplaza FontAwesome por SVGs descargados (Twemoji) almacenados en
 * /static/images/icons/. Expone PacificIcons.get(nombre) que retorna
 * el HTML <img> listo para inyectar, y helpers para grupos repetidos.
 *
 * El objetivo es que los niveles luzcan vivos y consistentes con los
 * fondos ilustrados generados por el autor.
 */
(function (global) {
  const BASE = '/static/images/icons/';

  // Mapeo nombre normalizado -> archivo .svg en /static/images/icons/
  const MAP = {
    // ── Fauna del Pacífico ──────────────────────────────────────────
    pez: 'pez_tropical',
    'pez tropical': 'pez_tropical',
    'pez azul': 'pez_tropical',
    'pez rojo': 'pez_tropical',
    'pez_azul': 'pez_tropical',
    'pez_rojo': 'pez_tropical',
    'blue fish': 'pez_tropical',
    fish: 'pez',
    pescado: 'pez',
    cangrejo: 'cangrejo',
    crab: 'cangrejo',
    caracol: 'caracol',
    snail: 'caracol',
    concha: 'concha',
    conchas: 'concha',
    seashell: 'concha',
    rana: 'rana',
    frog: 'rana',
    'rana verde': 'rana',
    'rana_verde': 'rana',
    'three frogs': 'rana',
    'two frogs': 'rana',
    'four frogs': 'rana',
    ballena: 'ballena',
    whale: 'ballena',
    mono: 'mono',
    monkey: 'mono',
    mariposa: 'mariposa',
    butterfly: 'mariposa',
    'mariposa azul': 'mariposa',
    'mariposa_azul': 'mariposa',
    'blue butterfly': 'mariposa',
    ave: 'ave',
    aves: 'ave',
    bird: 'ave',
    pelicano: 'ave',
    pelícano: 'ave',
    pelican: 'ave',
    gaviota: 'ave',
    tucan: 'tucan',
    tucán: 'tucan',
    parrot: 'tucan',
    loro: 'tucan',
    insecto: 'mariposa',
    bug: 'mariposa',

    // ── Flora ───────────────────────────────────────────────────────
    hoja: 'hoja',
    leaf: 'hoja',
    planta: 'hoja',
    plantas: 'hoja',
    flor: 'hoja',
    'flor roja': 'hoja',
    'flor_roja': 'hoja',
    'red flower': 'hoja',
    sembrar_arbol: 'hoja',
    'sembrar árbol': 'hoja',
    palma: 'palma',
    palmera: 'palma',
    arbol: 'palma',
    árbol: 'palma',
    tree: 'palma',
    'palm tree': 'palma',

    // ── Naturaleza / efectos ────────────────────────────────────────
    sol: 'sol',
    sun: 'sol',
    agua: 'gota',
    droplet: 'gota',
    gota: 'gota',
    ola: 'ola',
    river: 'ola',
    rio: 'ola',
    río: 'ola',
    rio_1: 'ola',
    rio_2: 'ola',

    // ── Objetos / útiles ─────────────────────────────────────────────
    canoa: 'canoa',
    canoe: 'canoa',
    barco: 'canoa',
    bote: 'canoa',
    'bote madera': 'canoa',
    'bote_madera': 'canoa',
    'barco metal': 'canoa',
    'barco_metal': 'canoa',
    submarino: 'canoa',
    canasta: 'cesta',
    canastas: 'cesta',
    cesta: 'cesta',
    basket: 'cesta',

    // ── Decoración / feedback ────────────────────────────────────────
    estrella: 'estrella',
    star: 'estrella',
    corazon: 'corazon',
    corazón: 'corazon',
    heart: 'corazon',
    brillo: 'brillo',
    sparkles: 'brillo',
    trofeo: 'trofeo',
    trophy: 'trofeo',
    fuego: 'fuego',
    fire: 'fuego',

    // ── Conservación / acciones (Biología nivel 5) ───────────────────
    reciclar: 'hoja',
    basura: 'fuego',
    basura_rio: 'fuego',
    'tirar basura': 'fuego',
    talar_arbol: 'fuego',
    'talar árboles': 'fuego',
  };

  // Fallbacks parciales: si el nombre incluye una keyword, usar este SVG
  const FALLBACK_KEYWORDS = [
    ['cangrejo', 'cangrejo'],
    ['pez', 'pez_tropical'],
    ['peces', 'pez_tropical'],
    ['fish', 'pez_tropical'],
    ['rana', 'rana'],
    ['frog', 'rana'],
    ['concha', 'concha'],
    ['shell', 'concha'],
    ['caracol', 'caracol'],
    ['snail', 'caracol'],
    ['ballena', 'ballena'],
    ['whale', 'ballena'],
    ['mariposa', 'mariposa'],
    ['butterfly', 'mariposa'],
    ['mono', 'mono'],
    ['monkey', 'mono'],
    ['ave', 'ave'],
    ['gaviota', 'ave'],
    ['pelícano', 'ave'],
    ['pelicano', 'ave'],
    ['pajaro', 'ave'],
    ['bird', 'ave'],
    ['tucan', 'tucan'],
    ['parrot', 'tucan'],
    ['loro', 'tucan'],
    ['hoja', 'hoja'],
    ['leaf', 'hoja'],
    ['planta', 'hoja'],
    ['flor', 'hoja'],
    ['flower', 'hoja'],
    ['palma', 'palma'],
    ['árbol', 'palma'],
    ['arbol', 'palma'],
    ['tree', 'palma'],
    ['sol', 'sol'],
    ['sun', 'sol'],
    ['agua', 'gota'],
    ['water', 'gota'],
    ['canoa', 'canoa'],
    ['canoe', 'canoa'],
    ['barco', 'canoa'],
    ['bote', 'canoa'],
    ['boat', 'canoa'],
    ['canasta', 'cesta'],
    ['cesta', 'cesta'],
    ['basket', 'cesta'],
    ['ola', 'ola'],
    ['wave', 'ola'],
    ['rio', 'ola'],
    ['río', 'ola'],
    ['river', 'ola'],
    ['mountain', 'palma'],
    ['montaña', 'palma'],
    ['cielo', 'sol'],
    ['sky', 'sol'],
    ['reciclar', 'hoja'],
    ['sembrar', 'hoja'],
    ['basura', 'fuego'],
    ['talar', 'fuego'],
  ];

  function normaliza(nombre) {
    return (nombre || '').toString().toLowerCase().trim();
  }

  /** Retorna el nombre del archivo SVG (sin ruta) para un concepto dado. */
  function resolveName(nombre) {
    const n = normaliza(nombre);
    if (!n) return 'brillo';
    if (MAP[n]) return MAP[n];
    for (const [kw, file] of FALLBACK_KEYWORDS) {
      if (n.includes(kw)) return file;
    }
    return 'brillo'; // por defecto un sparkle inofensivo
  }

  /** Retorna la ruta absoluta al icono. */
  function path(nombre) {
    const rName = resolveName(nombre);
    if (['pez_tropical', 'canoa', 'caracol', 'ola'].includes(rName)) {
      return BASE + rName + '.png';
    }
    return BASE + rName + '.svg';
  }

  /** Retorna el HTML <img> de un ícono individual. */
  function get(nombre, opts) {
    opts = opts || {};
    const cls = opts.className || 'pacific-icon';
    const size = opts.size ? ` style="width:${opts.size};height:${opts.size}"` : '';
    return `<img src="${path(nombre)}" class="${cls}" alt="${nombre || ''}" draggable="false"${size}>`;
  }

  /**
   * Retorna varios íconos en una cuadrícula compacta (para mostrar
   * "3 peces", "6 conchas", etc.). Se acomodan en filas de hasta 3.
   */
  function getGroup(nombre, count, opts) {
    opts = opts || {};
    const cls = opts.className || 'pacific-icon-group';
    const itemCls = opts.itemClassName || 'pacific-icon-group-item';
    const arr = [];
    const n = Math.max(0, count | 0);
    const isConcha = resolveName(nombre) === 'concha';

    for (let i = 0; i < n; i++) {
      let srcPath = path(nombre);
      if (isConcha) {
        srcPath = BASE + 'concha' + ((i % 3) + 1) + '.png';
      }
      arr.push(`<img src="${srcPath}" class="${itemCls}" alt="" draggable="false">`);
    }
    // data-count permite estilos responsivos según cuántos hay
    return `<div class="${cls}" data-count="${n}">${arr.join('')}</div>`;
  }

  global.PacificIcons = { get, getGroup, path, resolveName };
})(window);
