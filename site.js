// The sync line rises with the scroll, the top bar frosts once the page
// moves, panels light up as they arrive, cards tilt toward the pointer, a
// terminal types, the bridge's stage plays its swap, the footer's sign strikes
// and cuts out, presses sound like a light cycle, and a copy button copies.
(function () {
  'use strict';

  var root = document.documentElement;
  var reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }

  /* ---- Scroll: the sync line ---- */
  var sync = document.querySelector('.sync');
  var readout = document.querySelector('.sync-readout');
  var ticking = false;

  function updateSync() {
    if (!sync) return;
    var max = root.scrollHeight - window.innerHeight;
    var p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 1;
    sync.style.setProperty('--p', p.toFixed(4));
    if (readout) readout.textContent = p >= 0.995 ? 'SYNCED' : 'SYNC ' + Math.round(p * 100) + '%';
  }

  // The bar's mark shows once the hero's own wordmark has scrolled away.
  var hero = document.querySelector('.hero');
  function updateBar() {
    root.classList.toggle('scrolled', window.scrollY > 8);
    root.classList.toggle('past-hero', !hero || window.scrollY > hero.offsetHeight * 0.45);
  }

  function update() { ticking = false; updateSync(); updateBar(); }
  function request() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
  }
  window.addEventListener('scroll', request, { passive: true });
  window.addEventListener('resize', request);
  update();

  /* ---- Panels light up as they arrive ---- */
  var panels = document.querySelectorAll('.reveal');
  if (reduce || !('IntersectionObserver' in window)) {
    each(panels, function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var tall = entry.intersectionRect.height >= window.innerHeight * 0.25;
        if (entry.intersectionRatio >= 0.15 || tall) {
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: [0, 0.05, 0.1, 0.15] });
    each(panels, function (el) { io.observe(el); });
  }

  /* ---- Cards: a spotlight follows the pointer, and the card tilts toward it ---- */
  if (window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    each(document.querySelectorAll('.cards .card'), function (card) {
      var light = card.querySelector('.card-in') || card;
      card.addEventListener('pointermove', function (event) {
        var r = card.getBoundingClientRect();
        var x = (event.clientX - r.left) / r.width;
        var y = (event.clientY - r.top) / r.height;
        light.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
        light.style.setProperty('--my', (y * 100).toFixed(1) + '%');
        if (reduce) return;
        var px = x - 0.5, py = y - 0.5, d = Math.sqrt(px * px + py * py);
        if (d < 0.001) return;
        card.style.setProperty('--tx', (-py / d).toFixed(3));
        card.style.setProperty('--ty', (px / d).toFixed(3));
        card.style.setProperty('--ta', (d * 11).toFixed(2) + 'deg');
      });
      card.addEventListener('pointerleave', function () { card.style.setProperty('--ta', '0deg'); });
    });
  }

  /* ---- Run something only while its element is on screen ---- */
  function whileSeen(el, share, start, stop) {
    if (!('IntersectionObserver' in window)) { start(); return; }
    var on = false;
    new IntersectionObserver(function (entries) {
      var seen = entries[entries.length - 1].isIntersecting;
      if (seen === on) return;
      on = seen;
      if (seen) start(); else if (stop) stop();
    }, { threshold: share }).observe(el);
  }

  /* ---- How it works: the stage plays a swap, then the same swap stalling ---- */
  var stage = document.querySelector('[data-stage]');
  if (stage) {
    var SVG = 'http://www.w3.org/2000/svg';
    var START = { usdc: [412, 150], zec: [68, 290], you: [68, 200], bridge: [412, 200] };
    var LOCK = { el: 'usdc', d: 'M412 150V90L392 70H214' };
    var SEND = { el: 'zec', d: 'M68 290V350L88 370H214' };
    // Per step: what moves, which plates light, and the word in the middle.
    var SCENES = {
      settles: [
        { moves: [LOCK], hot: ['contract'], word: 'Locked' },
        { moves: [SEND], hot: ['contract', 'address'], word: 'Sent' },
        { moves: [{ el: 'usdc', d: 'M214 70H88L68 90V150' }, { el: 'you', d: 'M68 200V90L88 70H267' }], hot: ['you', 'address'], word: 'Claimed' },
        { moves: [{ el: 'you', d: 'M267 70H392L412 90V200' }, { el: 'zec', d: 'M214 370H392L412 350V290', at: 1000 }], hot: ['you', 'bridge'], word: 'Settled' }
      ],
      stalls: [
        { moves: [LOCK], hot: ['contract'], word: 'Locked' },
        { moves: [SEND], hot: ['contract', 'address'], word: 'Sent' },
        { moves: [{ el: 'usdc', d: 'M214 70H392L412 90V150' }, { el: 'bridge', d: 'M412 200V90L392 70H267' }], hot: ['bridge', 'address'], word: 'Stalled' },
        { moves: [{ el: 'bridge', d: 'M267 70H88L68 90V200' }, { el: 'zec', d: 'M214 370H88L68 350V290', at: 1000 }], hot: ['you', 'bridge'], word: 'Refunded' }
      ]
    };
    var TRAVEL = 1150;
    var parts = {};
    each(stage.querySelectorAll('[data-el]'), function (el) { parts[el.getAttribute('data-el')] = el; });
    var nodes = stage.querySelectorAll('[data-node]');
    var trails = stage.querySelector('.st-trails');
    var word = stage.querySelector('.st-state');
    var tabs = stage.querySelectorAll('.stage-tabs button');
    var playButton = stage.querySelector('.stage-play');
    var scene = 'settles';
    var step = 0;
    var playing = !reduce;
    var picked = false;
    var seen = false;
    var frame = 0;
    var next = 0;

    var move = function (name, point) { parts[name].setAttribute('transform', 'translate(' + point[0].toFixed(1) + ' ' + point[1].toFixed(1) + ')'); };
    var trail = function (d, shown) {
      var path = document.createElementNS(SVG, 'path');
      path.setAttribute('d', d);
      path.setAttribute('pathLength', '1');
      path.setAttribute('stroke-dasharray', '1 1');
      path.setAttribute('stroke-dashoffset', shown ? '0' : '1');
      trails.appendChild(path);
      return path;
    };
    var ease = function (t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
    var mark = function (n) {
      stage.setAttribute('data-at', n);
      stage.setAttribute('data-scene', scene);
      each(stage.querySelectorAll('[data-steps="' + scene + '"] li'), function (li, i) {
        li.classList.toggle('on', i === n - 1);
        li.classList.toggle('past', i < n - 1);
        var button = li.querySelector('button');
        if (i === n - 1) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current');
      });
      each(tabs, function (tab) { tab.setAttribute('aria-pressed', tab.getAttribute('data-scene') === scene ? 'true' : 'false'); });
    };
    var light = function (n) {
      var hot = n ? SCENES[scene][n - 1].hot : [];
      each(nodes, function (node) { node.classList.toggle('hot', hot.indexOf(node.getAttribute('data-node')) >= 0); });
      word.textContent = n ? SCENES[scene][n - 1].word : '';
      parts.usdc.classList.toggle('shielded', scene === 'settles' && n >= 3);
    };
    // Where everything stands once the first n steps are done.
    var place = function (n) {
      cancelAnimationFrame(frame);
      clearTimeout(next);
      trails.textContent = '';
      var spot = { usdc: START.usdc, zec: START.zec, you: START.you, bridge: START.bridge };
      SCENES[scene].slice(0, n).forEach(function (s) {
        s.moves.forEach(function (m) {
          var path = trail(m.d, true);
          var end = path.getPointAtLength(path.getTotalLength());
          spot[m.el] = [end.x, end.y];
        });
      });
      Object.keys(spot).forEach(function (name) { move(name, spot[name]); });
      light(n);
    };
    var queue = function (ms) { clearTimeout(next); if (playing && seen) next = setTimeout(advance, ms); };
    var run = function (n) {
      place(n - 1);
      step = n;
      mark(n);
      if (reduce) { place(n); return; }
      var moves = SCENES[scene][n - 1].moves.map(function (m) {
        var path = trail(m.d, false);
        return { el: m.el, at: m.at || 0, path: path, length: path.getTotalLength() };
      });
      var total = Math.max.apply(null, moves.map(function (m) { return m.at; })) + TRAVEL;
      var began = performance.now();
      var tick = function (now) {
        var t = now - began;
        moves.forEach(function (m) {
          var p = ease(Math.min(1, Math.max(0, (t - m.at) / TRAVEL)));
          var point = m.path.getPointAtLength(m.length * p);
          m.path.setAttribute('stroke-dashoffset', (1 - p).toFixed(4));
          move(m.el, [point.x, point.y]);
        });
        if (t < total) { frame = requestAnimationFrame(tick); return; }
        light(n);
        queue(n === 4 ? 2600 : 1250);
      };
      frame = requestAnimationFrame(tick);
    };
    var advance = function () {
      if (step < 4) { run(step + 1); return; }
      if (!picked) scene = scene === 'settles' ? 'stalls' : 'settles';
      run(1);
    };
    var setPlaying = function (on) {
      playing = on;
      playButton.setAttribute('aria-pressed', on ? 'true' : 'false');
      playButton.firstElementChild.textContent = on ? 'Pause' : 'Play';
      if (on) advance(); else clearTimeout(next);
    };

    each(tabs, function (tab) {
      tab.addEventListener('click', function () {
        picked = true;
        scene = tab.getAttribute('data-scene');
        if (reduce) { step = 4; mark(4); place(4); } else run(1);
      });
    });
    each(stage.querySelectorAll('.stage-steps button'), function (button) {
      button.addEventListener('click', function () {
        picked = true;
        if (playing && !reduce) { playing = false; playButton.setAttribute('aria-pressed', 'false'); playButton.firstElementChild.textContent = 'Play'; }
        run(Array.prototype.indexOf.call(button.closest('ol').children, button.closest('li')) + 1);
      });
    });
    if (reduce) {
      step = 4;
      mark(4);
      place(4);
    } else {
      playButton.hidden = false;
      playButton.addEventListener('click', function () { setPlaying(!playing); });
      mark(1);
      place(0);
      whileSeen(stage, 0.25, function () { seen = true; if (playing) { if (step) queue(700); else run(1); } }, function () { seen = false; clearTimeout(next); });
    }
  }

  /* ---- The terminal types its command once ---- */
  if (!reduce) {
    each(document.querySelectorAll('.term'), function (term) {
      var out = term.querySelector('.term-type');
      if (!out) return;
      var text = out.textContent;
      var started = false;
      out.textContent = '';
      out.classList.add('typing');
      whileSeen(term, 0.4, function () {
        if (started) return;
        started = true;
        var n = 0;
        var type = function () {
          n += 1;
          out.textContent = text.slice(0, n);
          if (n < text.length) { setTimeout(type, text.charAt(n - 1) === ' ' ? 70 : 17 + Math.random() * 22); return; }
          setTimeout(function () { out.classList.remove('typing'); term.classList.add('ran'); }, 380);
        };
        setTimeout(type, 420);
      });
    });
  }

  /* ---- The footer's sign: the visor opens, the letters strike outward from it,
          hold with the odd buzz, and cut out; a press switches it off and on ---- */
  var sign = document.querySelector('.sign');
  if (sign && !reduce) {
    var tubes = sign.querySelectorAll('.tube');
    var OUTWARD = [[2, 3], [1, 4], [0, 5]];
    var pending = [];
    var off = false;
    var at = function (ms, fn) { pending.push(setTimeout(fn, ms)); };
    var clear = function () { pending.forEach(clearTimeout); pending = []; };
    var lamp = function (i, on) { tubes[i].classList.toggle('on', on); };
    var all = function (on) { each(tubes, function (tube) { tube.classList.toggle('on', on); }); };
    var dark = function () { all(false); sign.classList.remove('power', 'seeing'); };
    var buzz = function () {
      var i = Math.floor(Math.random() * tubes.length);
      lamp(i, false);
      at(70, function () { lamp(i, true); });
      if (Math.random() < 0.5) { at(190, function () { lamp(i, false); }); at(250, function () { lamp(i, true); }); }
    };
    var strike = function () {
      clear();
      sign.classList.add('seeing');
      OUTWARD.forEach(function (pair, step) {
        pair.forEach(function (i, side) {
          var t = 950 + step * 360 + side * 70;
          at(t, function () { lamp(i, true); });
          at(t + 60, function () { lamp(i, false); });
          at(t + 210, function () { lamp(i, true); });
        });
      });
      at(1900, function () { sign.classList.add('power'); });
      at(4300, buzz);
      at(6900, buzz);
      at(9800, cut);
    };
    var cut = function () {
      clear();
      all(false);
      at(90, function () { all(true); });
      at(230, function () { all(false); sign.classList.remove('power'); });
      at(1000, function () { sign.classList.remove('seeing'); });
      if (!off) at(2500, strike);
    };
    sign.classList.add('dark');
    sign.addEventListener('click', function () {
      off = !off;
      sign.setAttribute('aria-pressed', off ? 'false' : 'true');
      if (off) cut(); else strike();
      play(off ? 'off' : 'on');
    });
    whileSeen(sign, 0.3, function () { if (!off) strike(); }, function () { clear(); dark(); });

    // The visor looks toward the pointer, and the head leans with it.
    if (window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      var helmet = sign.querySelector('.helmet');
      var footer = document.querySelector('.site-footer');
      footer.addEventListener('pointermove', function (event) {
        var r = helmet.getBoundingClientRect();
        var x = Math.max(-1, Math.min(1, (event.clientX - r.left - r.width / 2) / (window.innerWidth * 0.42)));
        var y = Math.max(-1, Math.min(1, (event.clientY - r.top - r.height * 0.6) / window.innerHeight));
        sign.classList.add('watching');
        sign.style.setProperty('--look', (0.5 + x * 0.5).toFixed(3));
        helmet.style.transform = 'translate(' + (x * 9).toFixed(1) + 'px,' + (y * 6).toFixed(1) + 'px)';
      });
      footer.addEventListener('pointerleave', function () {
        sign.classList.remove('watching');
        helmet.style.transform = '';
      });
    }
  }

  /* ---- Sound: a light cycle, synthesized; no audio files ---- */
  // Detuned saws pulled through a resonant filter, a glassy FM ring over them, and a short
  // metallic room behind both. Everything is quiet, and made on the visitor's own press.
  var AudioCtx = window.AudioContext || window.webkitAudioContext;
  var toggle = document.querySelector('.sound');
  var KEY = 'veylor.sound';
  var soundOn = true;
  var ctx = null;
  var bus = null;
  var room = null;

  try { if (window.localStorage.getItem(KEY) === 'off') soundOn = false; } catch (e) { /* storage blocked: stay on */ }

  function quiet(promise) { if (promise && promise.catch) promise.catch(function () {}); }

  // Made on the first press, never before: browsers only start audio after a gesture.
  function audio() {
    if (!AudioCtx) return null;
    if (!ctx) {
      try {
        ctx = new AudioCtx();
        bus = ctx.createGain();
        bus.gain.value = 0.55;
        bus.connect(ctx.destination);
        // The room: noise that dies in under a second, thinned out at the bottom, plus one echo.
        var length = Math.floor(ctx.sampleRate * 0.9);
        var impulse = ctx.createBuffer(2, length, ctx.sampleRate);
        for (var c = 0; c < 2; c++) {
          var data = impulse.getChannelData(c);
          for (var i = 0; i < length; i++) data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 3.4);
        }
        var reverb = ctx.createConvolver();
        reverb.buffer = impulse;
        var thin = ctx.createBiquadFilter();
        thin.type = 'highpass';
        thin.frequency.value = 420;
        var wet = ctx.createGain();
        wet.gain.value = 0.5;
        room = ctx.createGain();
        room.connect(thin);
        thin.connect(reverb);
        reverb.connect(wet);
        wet.connect(bus);
        var echo = ctx.createDelay(0.5);
        echo.delayTime.value = 0.13;
        var again = ctx.createGain();
        again.gain.value = 0.26;
        room.connect(echo);
        echo.connect(again);
        again.connect(echo);
        again.connect(bus);
      } catch (e) {
        ctx = null;
        return null;
      }
    }
    if (ctx.state === 'suspended' && ctx.resume) quiet(ctx.resume());
    return ctx;
  }

  function ramp(param, points, t) {
    param.setValueAtTime(points[0][1], t + points[0][0]);
    points.slice(1).forEach(function (p) { param.exponentialRampToValueAtTime(p[1], t + p[0]); });
  }

  function out(node, send) {
    node.connect(bus);
    var amount = ctx.createGain();
    amount.gain.value = send;
    node.connect(amount);
    amount.connect(room);
  }

  // The engine: two saws a few cents apart and a square an octave under, through a sweeping filter.
  function engine(t, o) {
    var filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.Q.value = o.q;
    ramp(filter.frequency, o.cut, t);
    var amp = ctx.createGain();
    ramp(amp.gain, o.amp, t);
    var end = t + o.amp[o.amp.length - 1][0];
    [['sawtooth', 1, -9], ['sawtooth', 1, 9], ['square', 0.5, 0]].forEach(function (v) {
      var osc = ctx.createOscillator();
      osc.type = v[0];
      osc.detune.value = v[2];
      ramp(osc.frequency, o.pitch.map(function (p) { return [p[0], p[1] * v[1]]; }), t);
      osc.connect(filter);
      osc.start(t);
      osc.stop(end + 0.02);
    });
    filter.connect(amp);
    out(amp, o.send);
  }

  // The ring: one sine bent by another at an odd ratio, so it chimes like glass and metal.
  function ring(t, o) {
    var carrier = ctx.createOscillator();
    var bend = ctx.createOscillator();
    var depth = ctx.createGain();
    var amp = ctx.createGain();
    ramp(carrier.frequency, o.pitch, t);
    ramp(bend.frequency, o.pitch.map(function (p) { return [p[0], p[1] * o.ratio]; }), t);
    ramp(depth.gain, o.depth, t);
    ramp(amp.gain, o.amp, t);
    bend.connect(depth);
    depth.connect(carrier.frequency);
    carrier.connect(amp);
    out(amp, o.send);
    var end = t + o.amp[o.amp.length - 1][0] + 0.02;
    carrier.start(t);
    bend.start(t);
    carrier.stop(end);
    bend.stop(end);
  }

  var SOUNDS = {
    // A link: a pulse of light passing.
    tap: function (t) {
      ring(t, { pitch: [[0, 620], [0.035, 1244.5]], ratio: 2.76, depth: [[0, 1500], [0.09, 60]], amp: [[0, 0.0001], [0.004, 0.05], [0.2, 0.0001]], send: 0.5 });
      engine(t, { pitch: [[0, 98], [0.09, 146.8]], cut: [[0, 260], [0.03, 2400], [0.13, 320]], q: 11, amp: [[0, 0.0001], [0.006, 0.026], [0.15, 0.0001]], send: 0.25 });
    },
    // A button: the cycle leaves the line.
    press: function (t) {
      engine(t, { pitch: [[0, 61.7], [0.16, 123.5], [0.5, 92.5]], cut: [[0, 180], [0.15, 3800], [0.55, 260]], q: 13, amp: [[0, 0.0001], [0.012, 0.075], [0.2, 0.06], [0.58, 0.0001]], send: 0.45 });
      ring(t + 0.03, { pitch: [[0, 493.9], [0.12, 987.8]], ratio: 3.53, depth: [[0, 2200], [0.3, 80]], amp: [[0, 0.0001], [0.008, 0.04], [0.5, 0.0001]], send: 0.6 });
    },
    // Power up, and down: the sign, and the sound switch itself.
    on: function (t) {
      engine(t, { pitch: [[0, 41.2], [0.55, 164.8], [0.8, 164.8]], cut: [[0, 120], [0.5, 4200], [0.85, 240]], q: 12, amp: [[0, 0.0001], [0.05, 0.055], [0.5, 0.06], [0.9, 0.0001]], send: 0.5 });
      ring(t + 0.4, { pitch: [[0, 659.3], [0.06, 1318.5]], ratio: 2.76, depth: [[0, 1800], [0.4, 60]], amp: [[0, 0.0001], [0.006, 0.045], [0.6, 0.0001]], send: 0.7 });
    },
    off: function (t) {
      engine(t, { pitch: [[0, 164.8], [0.5, 36.7]], cut: [[0, 3200], [0.5, 110]], q: 12, amp: [[0, 0.0001], [0.01, 0.07], [0.3, 0.045], [0.62, 0.0001]], send: 0.5 });
    }
  };

  function play(name) {
    if (!soundOn || !SOUNDS[name]) return;
    var ac = audio();
    if (ac) SOUNDS[name](ac.currentTime + 0.005);
  }

  if (AudioCtx) {
    // Create the context on the first gesture, so the first sound is not lost.
    var gestures = ['mousedown', 'pointerup', 'touchend', 'keydown'];
    var unlock = function () {
      if (soundOn) audio();
      gestures.forEach(function (type) { document.removeEventListener(type, unlock, true); });
    };
    gestures.forEach(function (type) { document.addEventListener(type, unlock, true); });

    document.addEventListener('click', function (event) {
      if (!soundOn) return;
      var target = event.target;
      var el = target && target.closest ? target.closest('a[href], button, label[for]') : null;
      if (!el || el === toggle) return;
      if (!el.classList.contains('sign')) play(el.classList.contains('btn') ? 'press' : 'tap');
    }, true);
  }

  if (toggle && AudioCtx) {
    var state = toggle.querySelector('.sound-state');
    var render = function () {
      toggle.setAttribute('aria-pressed', soundOn ? 'true' : 'false');
      if (state) state.textContent = soundOn ? 'On' : 'Off';
    };
    render();
    toggle.hidden = false;
    toggle.addEventListener('click', function () {
      soundOn = !soundOn;
      try { window.localStorage.setItem(KEY, soundOn ? 'on' : 'off'); } catch (e) { /* not remembered */ }
      render();
      if (soundOn) play('on');
      else if (ctx && ctx.state === 'running' && ctx.suspend) quiet(ctx.suspend());
    });
  }

  /* ---- Copy: a button copies the text of the element its data-copy-from names ---- */
  each(document.querySelectorAll('[data-copy-from]'), function (button) {
    var source = document.getElementById(button.getAttribute('data-copy-from'));
    if (!source) return;
    var label = button.textContent;
    var timer;
    var show = function (text) {
      button.textContent = text;
      clearTimeout(timer);
      timer = setTimeout(function () { button.textContent = label; }, 2000);
    };
    var select = function () {
      var range = document.createRange();
      range.selectNodeContents(source);
      var selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    };
    button.addEventListener('click', function () {
      var text = source.textContent.trim();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { show('Copied'); }, function () { select(); show('Selected'); });
      } else {
        select();
        show('Selected');
      }
    });
  });
})();
