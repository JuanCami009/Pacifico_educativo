/**
 * atrapa_ranas.js — Minijuego "Los cangrejos del manglar" (Nivel 1 Matemáticas)
 * Cangrejos numerados vuelan; la gaviota atrapa los que indica el Riviel (imágenes en /static/images/level_matematicas/).
 */

(function () {
  'use strict';

  const FRASES_ALIENTO = ['¡Así se hace!', '¡El río te da poder!', '¡Excelente!'];

  /**
   * Inicia el nivel dentro del contenedor del área de juego.
   * @param {HTMLElement} contenedor - #game-area
   * @param {Object} datosNivel - Objeto del nivel desde la API (incluye configuracion)
   * @param {function(number): void} onCompletado - Callback con puntaje total al ganar (máx. 150)
   * @returns {function(): void} destroy - Detiene el bucle y limpia listeners
   */
  function iniciarNivel(contenedor, datosNivel, onCompletado) {
    const cfg = datosNivel.configuracion || {};
    const RONDAS_TOTAL = cfg.rondas || 5;
    const META_RONDA = cfg.insectos_para_ganar_ronda || 3;
    const MAX_VIDAS = cfg.vidas || 3;
    const VELOCIDAD_BASE = typeof cfg.velocidad_base === 'number' ? cfg.velocidad_base : 1.5;

    let destruido = false;
    let rafId = 0;
    let timeoutAlientoId = 0;
    let ronda = 1;
    let vidas = MAX_VIDAS;
    let puntaje = 0;
    let numeroPedido = 1;
    let atrapadosRonda = 0;
    let ultimoAnguloPintado = -999;
    /** @type {{ el: HTMLElement, n: number, x: number, y: number, dir: number, fase: number, amp: number, freq: number, correcto: boolean, escapando: boolean }[]} */
    let insectos = [];
    let jugadorSaltando = false;
    let ultimoSpawnMs = 0;
    let ultimoTickMs = 0;
    let acumulador8s = 0;

    const audioAcierto = new Audio('/static/audio/rana_atrapa.ogg');
    audioAcierto.preload = 'auto';
    const audioError = new Audio('/static/audio/error_suave.ogg');
    audioError.preload = 'auto';
    audioError.volume = 0.45;

    const ac = typeof AudioContext !== 'undefined' ? new AudioContext() : null;

    const cfgImg = (datosNivel.configuracion && datosNivel.configuracion.imagenes) || {};
    const URLS = {
      cangrejo: cfgImg.cangrejo || '/static/images/level_matematicas/cangrejo.png',
      gaviota: cfgImg.gaviota || '/static/images/level_matematicas/gaviota.png',
      riviel: cfgImg.riviel || '/static/images/level_matematicas/riviel.png',
    };

    contenedor.innerHTML = '';
    contenedor.className = (contenedor.className + ' atrapa-ranas-area').trim();

    function beepErrorSuave() {
      if (!ac) return;
      try {
        const o = ac.createOscillator();
        const g = ac.createGain();
        o.type = 'sine';
        o.frequency.value = 220;
        g.gain.setValueAtTime(0.08, ac.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.12);
        o.connect(g);
        g.connect(ac.destination);
        o.start();
        o.stop(ac.currentTime + 0.15);
      } catch (_) { /* silencio */ }
    }

    function reproducir(srcAudio, fallbackFn) {
      const p = srcAudio.play();
      if (p && typeof p.catch === 'function') {
        p.catch(() => { if (fallbackFn) fallbackFn(); });
      }
    }

    const root = document.createElement('div');
    root.className = 'atrapa-ranas-root';
    root.innerHTML = `
      <div class="atrapa-hud-superior">
        <div class="atrapa-vidas" id="atrapa-vidas" aria-label="Vidas"></div>
        <div class="atrapa-medallon" id="atrapa-puntaje-ui" role="status">0</div>
      </div>
      <div class="atrapa-pergamino" id="atrapa-pergamino">
        <div class="atrapa-riviel-fila">
          <img id="atrapa-riviel-img" class="atrapa-riviel-img" src="" alt="El Riviel" width="72" height="72" />
          <p class="atrapa-pergamino-texto" id="atrapa-mensaje-riviel"></p>
        </div>
      </div>
      <div class="atrapa-zona-vuelo" id="atrapa-zona-vuelo">
        <div class="atrapa-sombra-rio" aria-hidden="true"></div>
      </div>
      <div class="atrapa-zona-tronco" id="atrapa-zona-tronco">
        <div class="atrapa-tronco" aria-hidden="true"></div>
        <div class="atrapa-gaviota-host" id="atrapa-gaviota-host">
          <div class="atrapa-gaviota-inner" id="atrapa-gaviota-inner"></div>
        </div>
      </div>
      <div class="atrapa-overlay oculto" id="atrapa-gameover">
        <div class="atrapa-overlay-card">
          <h3>¡Oh no!</h3>
          <p>Se acabaron las vidas. ¿Reintentar desde la primera ronda?</p>
          <button type="button" class="btn-atrapa-reintentar" id="atrapa-btn-reintentar">Reintentar</button>
        </div>
      </div>
    `;
    contenedor.appendChild(root);

    const elVidas = root.querySelector('#atrapa-vidas');
    const elPuntaje = root.querySelector('#atrapa-puntaje-ui');
    const elMensaje = root.querySelector('#atrapa-mensaje-riviel');
    const elRivielImg = root.querySelector('#atrapa-riviel-img');
    const zonaVuelo = root.querySelector('#atrapa-zona-vuelo');
    const gaviotaHost = root.querySelector('#atrapa-gaviota-host');
    const gaviotaInner = root.querySelector('#atrapa-gaviota-inner');
    const overlayGO = root.querySelector('#atrapa-gameover');

    elRivielImg.src = URLS.riviel;
    elRivielImg.onerror = () => { elRivielImg.style.visibility = 'hidden'; };

    const gaviotaImg = document.createElement('img');
    gaviotaImg.className = 'atrapa-gaviota-img';
    gaviotaImg.src = URLS.gaviota;
    gaviotaImg.alt = 'Gaviota';
    gaviotaImg.draggable = false;
    gaviotaImg.onerror = () => { gaviotaImg.style.opacity = '0.35'; };
    gaviotaInner.appendChild(gaviotaImg);

    let anguloGaviota = 0;
    let pinzasAbiertas = false;

    function pintarGaviota() {
      const extra = pinzasAbiertas ? ' scale(1.08)' : '';
      gaviotaImg.style.transform = `rotate(${anguloGaviota}deg)${extra}`;
    }
    pintarGaviota();

    function renderVidas() {
      elVidas.innerHTML = '';
      for (let i = 0; i < MAX_VIDAS; i++) {
        const img = document.createElement('img');
        img.className = 'atrapa-vida-gaviota' + (i >= vidas ? ' atrapa-vida-perdida' : '');
        img.src = URLS.gaviota;
        img.alt = '';
        img.width = 36;
        img.height = 36;
        img.draggable = false;
        img.setAttribute('aria-hidden', 'true');
        elVidas.appendChild(img);
      }
    }

    function syncHudGlobal() {
      const d = document.getElementById('puntaje-display');
      if (d) d.textContent = String(puntaje);
    }

    function animarMedallon() {
      elPuntaje.classList.remove('atrapa-medallon-pop');
      void elPuntaje.offsetWidth;
      elPuntaje.classList.add('atrapa-medallon-pop');
    }

    function actualizarMensajePrincipal() {
      elMensaje.textContent = `¡Atrapa solo los cangrejos con el número ${numeroPedido}!`;
    }

    function rangoNumeroPorRonda(nr) {
      if (nr === 1) return 1 + Math.floor(Math.random() * 3);
      if (nr <= 3) return 1 + Math.floor(Math.random() * 6);
      return 1 + Math.floor(Math.random() * 9);
    }

    function velocidadPxFrame() {
      return (VELOCIDAD_BASE + 0.8) + 0.3 * (ronda - 1); // Más rápido
    }

    function crearInsecto(n) {
      const correcto = n === numeroPedido;
      const el = document.createElement('button');
      el.type = 'button';
      el.className = 'atrapa-cangrejo-vuelo' + (correcto ? ' atrapa-cangrejo-vuelo-meta' : '');
      el.setAttribute('aria-label', `Cangrejo número ${n}`);
      const img = document.createElement('img');
      img.className = 'atrapa-cangrejo-vuelo-img';
      img.src = URLS.cangrejo;
      img.alt = '';
      img.draggable = false;
      const num = document.createElement('span');
      num.className = 'atrapa-cangrejo-vuelo-num';
      num.textContent = String(n);
      el.appendChild(img);
      el.appendChild(num);

      const rect = zonaVuelo.getBoundingClientRect();
      const w = rect.width || 300;
      const h = rect.height || 200;
      const size = 100;
      const dir = Math.random() < 0.5 ? 1 : -1;
      
      // Sistema de 5 carriles para más cangrejos
      const numCarriles = 5;
      const occupiedLanes = insectos.map(ins => ins.lane);
      
      const availableLanes = [];
      for (let i = 0; i < numCarriles; i++) {
        if (!occupiedLanes.includes(i)) availableLanes.push(i);
      }
      
      let lane = availableLanes.length > 0 
        ? availableLanes[Math.floor(Math.random() * availableLanes.length)]
        : Math.floor(Math.random() * numCarriles);

      const x = dir > 0 ? -size : w + size * 0.2;
      
      // Añadir margen vertical para evitar recorte (clipping)
      const marginY = 50;
      const effectiveHeight = Math.max(100, h - marginY * 2);
      const laneHeight = effectiveHeight / numCarriles;
      const yBase = marginY + (lane * laneHeight) + (laneHeight / 2);
      const y = yBase; 
      
      const fase = Math.random() * Math.PI * 2;
      const amp = 4; // Oscilación mínima
      const freq = 0.01;

      el.style.width = `${size}px`;
      el.style.height = `${size}px`;
      zonaVuelo.appendChild(el);

      return { el, n, x, y, dir, fase, amp, freq, correcto, lane, escapando: false, temblando: false };
    }

    function poblacionInicial() {
      insectos.forEach(inv => inv.el.remove());
      insectos = [];
      const cant = 4; // Más al inicio
      const nums = [];
      for (let i = 0; i < cant; i++) {
        nums.push(1 + Math.floor(Math.random() * 9));
      }
      let hayCorrecto = nums.some(x => x === numeroPedido);
      if (!hayCorrecto && cant > 0) {
        nums[Math.floor(Math.random() * cant)] = numeroPedido;
        hayCorrecto = true;
      }
      for (const n of nums) {
        insectos.push(crearInsecto(n));
      }
    }

    function spawnExtra() {
      const maxIns = 5; 
      if (insectos.length >= maxIns) return;
      
      const hayCorrecto = insectos.some(inv => inv.n === numeroPedido && !inv.escapando && !inv.atrapado);
      
      let esCorrecto = false;
      if (!hayCorrecto) {
        esCorrecto = true;
      } else {
        // Probabilidad balanceada para que el número correcto aparezca seguido
        esCorrecto = Math.random() < 0.35;
      }
      
      const n = esCorrecto ? numeroPedido : (1 + Math.floor(Math.random() * 9));
      
      insectos.push(crearInsecto(n));
    }

    function insectoMasCercanoCorrecto() {
      const hostRect = gaviotaHost.getBoundingClientRect();
      const cx = hostRect.left + hostRect.width / 2;
      const cy = hostRect.top + hostRect.height / 2;
      let best = null;
      let bestD = Infinity;
      for (const inv of insectos) {
        if (inv.n !== numeroPedido || inv.escapando) continue;
        const r = inv.el.getBoundingClientRect();
        const ix = r.left + r.width / 2;
        const iy = r.top + r.height / 2;
        const d = (ix - cx) ** 2 + (iy - cy) ** 2;
        if (d < bestD) {
          bestD = d;
          best = inv;
        }
      }
      return best;
    }

    function apuntarGaviotaHaciaCangrejo() {
      const hostRect = gaviotaHost.getBoundingClientRect();
      const cx = hostRect.left + hostRect.width / 2;
      const cy = hostRect.top + hostRect.height / 2;
      const obj = insectoMasCercanoCorrecto();
      let tx = cx + 80;
      let ty = cy - 40;
      if (obj) {
        const r = obj.el.getBoundingClientRect();
        tx = r.left + r.width / 2;
        ty = r.top + r.height / 2;
      }
      const rad = Math.atan2(ty - cy, tx - cx);
      anguloGaviota = (rad * 180) / Math.PI * 0.4;
      if (Math.abs(anguloGaviota - ultimoAnguloPintado) > 2) {
        ultimoAnguloPintado = anguloGaviota;
        pintarGaviota();
      }
    }

    function iniciarRonda() {
      numeroPedido = rangoNumeroPorRonda(ronda);
      atrapadosRonda = 0;
      actualizarMensajePrincipal();
      poblacionInicial();
      ultimoSpawnMs = performance.now();
      acumulador8s = 0;
    }

    function mostrarAlientoYContinuar() {
      const f = FRASES_ALIENTO[Math.floor(Math.random() * FRASES_ALIENTO.length)];
      elMensaje.textContent = f;
      if (timeoutAlientoId) clearTimeout(timeoutAlientoId);
      timeoutAlientoId = setTimeout(() => {
        timeoutAlientoId = 0;
        if (destruido) return;
        ronda++;
        if (ronda > RONDAS_TOTAL) {
          destruir();
          onCompletado(Math.min(150, puntaje));
          return;
        }
        iniciarRonda();
        ultimoTickMs = 0;
        rafId = requestAnimationFrame(tick);
      }, 1800);
    }

    function restarVida() {
      vidas = Math.max(0, vidas - 1);
      renderVidas();
      if (vidas <= 0) {
        cancelAnimationFrame(rafId);
        overlayGO.classList.remove('oculto');
      }
    }

    function insectoEscapa(inv) {
      if (inv.escapando) return;
      inv.escapando = true;
      inv.el.style.pointerEvents = 'none';
      const iy = typeof inv.displayY === 'number' ? inv.displayY : 60;
      inv.el.style.setProperty('--ix', `${inv.x}px`);
      inv.el.style.setProperty('--iy', `${iy}px`);
      inv.el.classList.add('atrapa-cangrejo-vuelo-escape');
      restarVida();
      setTimeout(() => {
        inv.el.remove();
        const i = insectos.indexOf(inv);
        if (i >= 0) insectos.splice(i, 1);
      }, 900);
    }

    function actualizarPosiciones(dt) {
      const rect = zonaVuelo.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      const size = 52;
      const vel = velocidadPxFrame();
      const margen = size * 0.28;

      for (let i = 0; i < insectos.length; i++) {
        const inv = insectos[i];
        if (inv.escapando || inv.temblando || inv.atrapado) continue;

        inv.x += inv.dir * vel;
        // Oscilación limitada al carril
        const ySin = inv.y + inv.amp * Math.sin(inv.x * inv.freq + inv.fase);
        const clampedY = Math.max(size * 0.5, Math.min(h - size * 0.5, ySin));
        inv.displayY = clampedY;

        if (inv.correcto) {
          if (inv.dir > 0 && inv.x >= w - margen) insectoEscapa(inv);
          else if (inv.dir < 0 && inv.x <= margen * 0.35) {
            inv.dir = 1;
            inv.x = margen * 0.35;
          }
        } else if (inv.dir > 0 && inv.x >= w - margen) {
          inv.dir = -1;
          inv.x = w - margen;
        } else if (inv.dir < 0 && inv.x <= margen * 0.25) {
          inv.dir = 1;
          inv.x = margen * 0.25;
        }

        inv.el.style.transform = `translate3d(${inv.x}px, ${clampedY}px, 0)`;
      }

      acumulador8s += dt;
      if (acumulador8s >= 8000) {
        acumulador8s = 0;
        spawnExtra();
      }
    }

    function tick(now) {
      if (destruido) return;
      if (!ultimoTickMs) ultimoTickMs = now;
      const dt = Math.min(64, now - ultimoTickMs);
      ultimoTickMs = now;
      if (vidas > 0) {
        actualizarPosiciones(dt);
        apuntarGaviotaHaciaCangrejo();
      }
      if (!destruido && vidas > 0) rafId = requestAnimationFrame(tick);
    }

    function hitTest(clientX, clientY) {
      for (const inv of insectos) {
        if (inv.escapando) continue;
        const r = inv.el.getBoundingClientRect();
        if (clientX >= r.left && clientX <= r.right && clientY >= r.top && clientY <= r.bottom) {
          return inv;
        }
      }
      return null;
    }

    function animarSaltoGaviota(clientX, clientY, alAtrapar, onFin) {
      const inner = gaviotaInner;
      const hRect = gaviotaHost.getBoundingClientRect();
      const cx = hRect.left + hRect.width / 2;
      const cy = hRect.top + hRect.height / 2;
      const dx = clientX - cx;
      const dy = clientY - cy - 24;
      jugadorSaltando = true;
      pinzasAbiertas = alAtrapar;
      pintarGaviota();

      inner.style.transition = 'transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)';
      inner.style.transform = `translate(${dx}px, ${dy + 40}px) rotate(15deg) scale(1.1)`;

      setTimeout(() => {
        if (destruido) return;
        if (onFin) onFin();
        inner.style.transition = 'transform 0.4s ease-in-out';
        inner.style.transform = 'translate(0,0) rotate(0deg) scale(1)';
        pinzasAbiertas = false;
        pintarGaviota();
        setTimeout(() => {
          jugadorSaltando = false;
        }, 400);
      }, alAtrapar ? 500 : 420);
    }

    function onAcierto(inv, clientX, clientY) {
      animarSaltoGaviota(clientX, clientY, true, () => {
        reproducir(audioAcierto, null);
        const y = typeof inv.displayY === 'number' ? inv.displayY : 60;
        inv.el.style.transition = 'transform 0.2s ease-in, opacity 0.2s ease';
        inv.el.style.transform = `translate3d(${inv.x}px, ${y}px, 0) scale(0.02)`;
        inv.el.style.opacity = '0';
        setTimeout(() => {
          inv.el.remove();
          const ix = insectos.indexOf(inv);
          if (ix >= 0) insectos.splice(ix, 1);
        }, 220);
        puntaje += 10;
        elPuntaje.textContent = String(puntaje);
        syncHudGlobal();
        animarMedallon();
        atrapadosRonda++;
        spawnExtra();
        if (atrapadosRonda >= META_RONDA) {
          cancelAnimationFrame(rafId);
          insectos.forEach(o => {
            if (!o.escapando && o.el.parentNode) o.el.remove();
          });
          insectos = [];
          mostrarAlientoYContinuar();
        }
      });
    }

    function onFallo(inv, clientX, clientY) {
      animarSaltoGaviota(clientX, clientY, false, () => {
        reproducir(audioError, beepErrorSuave);
        inv.temblando = true;
        const iy = typeof inv.displayY === 'number' ? inv.displayY : 60;
        inv.el.style.setProperty('--ix', `${inv.x}px`);
        inv.el.style.setProperty('--iy', `${iy}px`);
        inv.el.classList.add('atrapa-cangrejo-vuelo-shake');
        setTimeout(() => {
          inv.temblando = false;
          inv.atrapado = false; // Reanudar vuelo
          inv.el.classList.remove('atrapa-cangrejo-vuelo-shake');
        }, 320);
        restarVida();
        if (vidas <= 0) cancelAnimationFrame(rafId);
      });
    }

    function manejarPointer(clientX, clientY) {
      if (destruido || jugadorSaltando || vidas <= 0) return;
      const inv = hitTest(clientX, clientY);
      if (!inv) return;
      
      // Detener el cangrejo inmediatamente
      inv.atrapado = true;
      
      if (inv.n === numeroPedido) onAcierto(inv, clientX, clientY);
      else onFallo(inv, clientX, clientY);
    }

    function onPointerDown(ev) {
      if (ac && ac.state === 'suspended') ac.resume().catch(() => {});
      const t = ev.changedTouches ? ev.changedTouches[0] : ev;
      manejarPointer(t.clientX, t.clientY);
    }

    zonaVuelo.addEventListener('pointerdown', onPointerDown);

    renderVidas();
    requestAnimationFrame(() => {
      iniciarRonda();
      syncHudGlobal();
      elPuntaje.textContent = '0';
      rafId = requestAnimationFrame(tick);
    });

    root.querySelector('#atrapa-btn-reintentar').addEventListener('click', () => {
      if (timeoutAlientoId) {
        clearTimeout(timeoutAlientoId);
        timeoutAlientoId = 0;
      }
      cancelAnimationFrame(rafId);
      overlayGO.classList.add('oculto');
      vidas = MAX_VIDAS;
      puntaje = 0;
      ronda = 1;
      elPuntaje.textContent = '0';
      syncHudGlobal();
      renderVidas();
      ultimoTickMs = 0;
      iniciarRonda();
      rafId = requestAnimationFrame(tick);
    });

    function destruir() {
      if (destruido) return;
      destruido = true;
      cancelAnimationFrame(rafId);
      if (timeoutAlientoId) clearTimeout(timeoutAlientoId);
      zonaVuelo.removeEventListener('pointerdown', onPointerDown);
      contenedor.classList.remove('atrapa-ranas-area');
      contenedor.innerHTML = '';
    }

    return destruir;
  }

  window.iniciarNivel = iniciarNivel;
})();
