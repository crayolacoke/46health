(function(){
 var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.15});
 document.querySelectorAll('.rv').forEach(function(el){io.observe(el)});
 var cio=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;cio.unobserve(e.target);var el=e.target,to=+el.dataset.to,t0=null;
  function step(t){if(!t0)t0=t;var p=Math.min((t-t0)/1600,1);el.textContent=Math.round(to*(1-Math.pow(1-p,3)));if(p<1)requestAnimationFrame(step)}requestAnimationFrame(step)})},{threshold:.5});
 document.querySelectorAll('[data-to]').forEach(function(el){cio.observe(el)});
})();
