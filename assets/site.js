/* Crypto Hogs · shared behavior for subpages (kept deliberately light: no 3D, no canvas) */
(function(){
  "use strict";
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (/[?&]motion/.test(location.search)) reduced = false;
  var LITE = window.matchMedia('(max-width:860px)').matches ||
             (navigator.deviceMemory && navigator.deviceMemory <= 2);
  if (LITE) document.documentElement.classList.add('lite');
  var staticMode = /[?&]static/.test(location.search);
  if (staticMode){
    document.documentElement.classList.add('lite');
    reduced = true;
    document.addEventListener('DOMContentLoaded', function(){
      var sh = location.search.match(/shift=(\d+)/);
      if (sh) document.body.style.transform = 'translateY(-' + sh[1] + 'px)';
    });
  }

  /* brand → home */
  /* nav scroll state */
  var header = document.getElementById('header');
  function onScrollNav(){ header.classList.toggle('scrolled', window.scrollY > 24); }
  window.addEventListener('scroll', onScrollNav, {passive:true}); onScrollNav();

  /* mobile menu: Escape closes it, the burger's aria-expanded stays in sync, page behind the overlay is inert */
  var burger = document.querySelector('.burger');
  if (burger){
    var behind = document.querySelectorAll('main, footer');
    var syncMenu = function(){
      var open = document.body.classList.contains('menu-open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      behind.forEach(function(el){ el.inert = open; });
    };
    document.addEventListener('click', syncMenu);
    document.addEventListener('keydown', function(e){
      if (e.key === 'Escape' && document.body.classList.contains('menu-open')){
        document.body.classList.remove('menu-open'); syncMenu(); burger.focus();
      }
    });
  }

  /* reveals */
  if ('IntersectionObserver' in window && !staticMode){
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){ if (e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
    }, {threshold:.12, rootMargin:'0px 0px -6% 0px'});
    document.querySelectorAll('.reveal').forEach(function(el){ io.observe(el); });
  } else {
    document.querySelectorAll('.reveal').forEach(function(el){ el.classList.add('in'); });
  }

  /* scramble on mono labels */
  if (!staticMode && !reduced && 'IntersectionObserver' in window){
    var GLY = '₿ΞÐ#$%&@01<>*';
    var sio = new IntersectionObserver(function(es){
      es.forEach(function(en){
        if (!en.isIntersecting) return;
        sio.unobserve(en.target);
        var el = en.target, orig = el.textContent, len = orig.length, frame = 0;
        var total = Math.max(14, Math.min(26, len + 6));
        (function step(){
          frame++;
          var out = '';
          var rev = (frame - 4) * (len / (total - 8));
          for (var i = 0; i < len; i++){
            out += (i < rev || orig[i] === ' ') ? orig[i] : GLY[Math.floor(Math.random() * GLY.length)];
          }
          el.textContent = out;
          if (frame < total) setTimeout(step, 34); else el.textContent = orig;
        })();
      });
    }, {threshold: .8});
    document.querySelectorAll('.eyebrow').forEach(function(el){ sio.observe(el); });
  }

  /* scroll progress */
  var pb = document.createElement('div');
  pb.className = 'scroll-progress';
  document.body.appendChild(pb);
  /* cache the scroll extent: reading scrollHeight/clientHeight per frame forces a full layout */
  var pbTick = false, pbMax = 1;
  function pbMeasure(){ var h = document.documentElement; pbMax = Math.max(1, h.scrollHeight - h.clientHeight); }
  pbMeasure();
  window.addEventListener('resize', pbMeasure, {passive:true});
  if (window.ResizeObserver) new ResizeObserver(pbMeasure).observe(document.body);
  window.addEventListener('load', pbMeasure);
  window.addEventListener('scroll', function(){
    if (pbTick) return; pbTick = true;
    requestAnimationFrame(function(){
      pb.style.transform = 'scaleX(' + (window.scrollY / pbMax) + ')';
      pbTick = false;
    });
  }, {passive:true});

  /* custom cursor */
  if (!staticMode && !reduced && window.matchMedia('(hover:hover) and (pointer:fine)').matches){
    var dot = document.createElement('div'); dot.className = 'cur-dot';
    var ring = document.createElement('div'); ring.className = 'cur-ring';
    document.body.appendChild(dot); document.body.appendChild(ring);
    document.body.classList.add('cursor-on');
    var mx = -100, my = -100, rx = -100, ry = -100, cs = 1, craf = null;
    var cloop = function(){
      rx += (mx - rx) * .16; ry += (my - ry) * .16;
      var ts = document.body.classList.contains('cursor-hot') ? 1.6 : 1;
      cs += (ts - cs) * .18;
      ring.style.transform = 'translate(' + rx + 'px,' + ry + 'px) translate(-50%,-50%) scale(' + cs.toFixed(3) + ')';
      dot.style.transform = 'translate(' + mx + 'px,' + my + 'px) translate(-50%,-50%)';
      if (Math.abs(mx - rx) < .2 && Math.abs(my - ry) < .2 && Math.abs(ts - cs) < .01){ craf = null; return; }
      craf = requestAnimationFrame(cloop);
    };
    var ckick = function(){ if (craf === null) craf = requestAnimationFrame(cloop); };
    document.addEventListener('mousemove', function(e){
      mx = e.clientX; my = e.clientY;
      if (craf === null && rx < -50){ rx = mx; ry = my; }
      ckick();
    }, {passive:true});
    document.addEventListener('mouseover', function(e){
      var t = e.target.closest ? e.target.closest('a,button,summary,.gcard,.row') : null;
      document.body.classList.toggle('cursor-hot', !!t);
      ckick();
    }, {passive:true});
  }

  /* console egg */
  try {
    console.log('%cCRYPTO HOGS', 'font-size:26px;font-weight:bold;color:#C9A96A;text-shadow:2px 2px 0 #9D2235;');
    console.log('%c₿ You opened devtools. You should probably join.\n→ GroupMe: https://groupme.com/join_group/113608298/MGcsS3ON', 'color:#F4EFE4;font-size:12px;line-height:1.7;');
  } catch (e) {}
})();
