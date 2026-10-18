// The sync line rises with the scroll, and panels light up as they arrive.
(function () {
  var root = document.documentElement;
  var sync = document.querySelector('.sync');
  var readout = document.querySelector('.sync-readout');
  var ticking = false;

  function update() {
    ticking = false;
    var max = root.scrollHeight - window.innerHeight;
    var p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 1;
    sync.style.setProperty('--p', p.toFixed(4));
    if (readout) readout.textContent = p >= 0.995 ? 'SYNCED' : 'SYNC ' + Math.round(p * 100) + '%';
  }

  if (sync) {
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  var panels = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    panels.forEach(function (el) { el.classList.add('in'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) { entry.target.classList.add('in'); io.unobserve(entry.target); }
    });
  }, { threshold: 0.15 });
  panels.forEach(function (el) { io.observe(el); });
})();
