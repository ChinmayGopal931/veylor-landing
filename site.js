// The sync line rises with the scroll, the top bar frosts once the page
// moves, panels light up as they arrive, cards tilt toward the pointer, the
// swap's rail fills as its steps are read, and presses make a quiet blip.
(function () {
  'use strict';

  var root = document.documentElement;
  var reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }

  /* ---- Scroll: the sync line, and the steps' rail ---- */
  var sync = document.querySelector('.sync');
  var readout = document.querySelector('.sync-readout');
  // Under reduced motion the rail is drawn fully lit by the stylesheet alone.
  var rails = reduce ? [] : document.querySelectorAll('[data-rail]');
  var ticking = false;

  function updateSync() {
    if (!sync) return;
    var max = root.scrollHeight - window.innerHeight;
    var p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 1;
    sync.style.setProperty('--p', p.toFixed(4));
    if (readout) readout.textContent = p >= 0.995 ? 'SYNCED' : 'SYNC ' + Math.round(p * 100) + '%';
  }

  function updateRails() {
    var line = window.innerHeight * 0.62;
    each(rails, function (wrap) {
      var rail = wrap.querySelector('.rail');
      if (!rail) return;
      var r = rail.getBoundingClientRect();
      var p = r.height > 0 ? (line - r.top) / r.height : 1;
      wrap.style.setProperty('--fill', Math.min(1, Math.max(0, p)).toFixed(4));
      each(wrap.querySelectorAll('.step'), function (step) {
        step.classList.toggle('lit', step.getBoundingClientRect().top + 12 <= line);
      });
    });
  }

  // The bar's mark shows once the hero's own wordmark has scrolled away.
  var hero = document.querySelector('.hero');
  function updateBar() {
    root.classList.toggle('scrolled', window.scrollY > 8);
    root.classList.toggle('past-hero', !hero || window.scrollY > hero.offsetHeight * 0.45);
  }

  function update() { ticking = false; updateSync(); updateRails(); updateBar(); }
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
    each(document.querySelectorAll('.cards .card, .link-card'), function (card) {
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

  /* ---- Sound: a 90s-game blip, synthesized; no audio files ---- */
  var AudioCtx = window.AudioContext || window.webkitAudioContext;
  var toggle = document.querySelector('.sound');
  var KEY = 'veylor.sound';
  var soundOn = true;
  var ctx = null;
  var bus = null;

  try { if (window.localStorage.getItem(KEY) === 'off') soundOn = false; } catch (e) { /* storage blocked: stay on */ }

  // Square waves stepping up in pitch, softened by a low-pass filter and kept quiet.
  var SOUNDS = {
    tap: { notes: [[1046.5, 0], [1568, 0.028]], len: 0.075, peak: 0.03 },
    press: { notes: [[987.8, 0], [1318.5, 0.055]], len: 0.16, peak: 0.03 },
    on: { notes: [[523.3, 0], [784, 0.045], [1046.5, 0.09]], len: 0.17, peak: 0.028 }
  };

  function quiet(promise) { if (promise && promise.catch) promise.catch(function () {}); }

  // Made on the first press, never before: browsers only start audio after a gesture.
  function audio() {
    if (!AudioCtx) return null;
    if (!ctx) {
      try {
        ctx = new AudioCtx();
        var lowpass = ctx.createBiquadFilter();
        lowpass.type = 'lowpass';
        lowpass.frequency.value = 3600;
        lowpass.connect(ctx.destination);
        bus = lowpass;
      } catch (e) {
        ctx = null;
        return null;
      }
    }
    if (ctx.state === 'suspended' && ctx.resume) quiet(ctx.resume());
    return ctx;
  }

  function blip(name) {
    var sound = SOUNDS[name];
    var ac = sound && audio();
    if (!ac) return;
    var t = ac.currentTime + 0.003;
    var osc = ac.createOscillator();
    var amp = ac.createGain();
    osc.type = 'square';
    sound.notes.forEach(function (note) { osc.frequency.setValueAtTime(note[0], t + note[1]); });
    amp.gain.setValueAtTime(0.0001, t);
    amp.gain.exponentialRampToValueAtTime(sound.peak, t + 0.005);
    amp.gain.setValueAtTime(sound.peak, t + sound.len * 0.6);
    amp.gain.exponentialRampToValueAtTime(0.0001, t + sound.len);
    osc.connect(amp);
    amp.connect(bus);
    osc.onended = function () { osc.disconnect(); amp.disconnect(); };
    osc.start(t);
    osc.stop(t + sound.len + 0.02);
  }

  if (AudioCtx) {
    // Create the context on the first gesture, so the first blip is not lost.
    var gestures = ['mousedown', 'pointerup', 'touchend', 'keydown'];
    var unlock = function () {
      if (soundOn) audio();
      gestures.forEach(function (type) { document.removeEventListener(type, unlock, true); });
    };
    gestures.forEach(function (type) { document.addEventListener(type, unlock, true); });

    document.addEventListener('click', function (event) {
      if (!soundOn) return;
      var target = event.target;
      var el = target && target.closest ? target.closest('a[href], button') : null;
      if (!el || el === toggle) return;
      blip(el.classList.contains('btn') ? 'press' : 'tap');
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
      if (soundOn) blip('on');
      else if (ctx && ctx.state === 'running' && ctx.suspend) quiet(ctx.suspend());
    });
  }
})();
