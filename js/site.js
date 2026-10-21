/* Kobalt Construction: shared site behavior
   1) lead tracking for click-to-call / email links (Google Analytics events)
   2) forms submit in place with a confirmation message, instead of sending visitors to Formspree's generic page */
(function () {
  function track(name, params) {
    if (typeof window.gtag === 'function') { try { window.gtag('event', name, params || {}); } catch (e) {} }
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="tel:"], a[href^="mailto:"]');
    if (!a) return;
    track(a.getAttribute('href').indexOf('tel:') === 0 ? 'click_to_call' : 'click_email',
          { link_location: a.closest('header') ? 'header' : (a.closest('footer') ? 'footer' : 'page') });
  });

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text) n.textContent = text;
    return n;
  }
  function phoneLink() {
    var a = el('a', null, '570.895.4613'); a.href = 'tel:+15708954613'; return a;
  }

  function showSuccess(form) {
    var kind = form.getAttribute('data-form');
    var panel = el('div', 'form-success');
    panel.setAttribute('role', 'status'); panel.setAttribute('tabindex', '-1');
    var p = el('p');
    if (kind === 'bid') {
      track('generate_lead', { form_name: 'bid_invitation' });
      panel.appendChild(el('h3', null, 'Bid invitation received'));
      p.appendChild(document.createTextNode("Thanks. We've received your invitation and will review it. For anything time-sensitive, call "));
      p.appendChild(phoneLink()); p.appendChild(document.createTextNode('.'));
    } else if (kind === 'contact') {
      track('generate_lead', { form_name: 'contact' });
      panel.appendChild(el('h3', null, 'Message received'));
      p.appendChild(document.createTextNode("Thanks for reaching out. We'll get back to you within one business day. If it's urgent, call "));
      p.appendChild(phoneLink()); p.appendChild(document.createTextNode('.'));
    } else {
      var pos = form.querySelector('[name="Position"]');
      track('submit_application', { position: pos ? pos.value : '' });
      panel.appendChild(el('h3', null, 'Application received'));
      p.appendChild(document.createTextNode("Thanks for your interest in joining Kobalt Construction. Our team will review your application and be in touch if there's a fit."));
    }
    panel.appendChild(p);
    if (kind === 'job') {
      var back = el('p'); var link = el('a', null, 'Back to all openings'); link.href = 'careers.html'; back.appendChild(link); panel.appendChild(back);
    }
    while (form.firstChild) form.removeChild(form.firstChild);
    form.appendChild(panel);
    panel.focus();
    if (panel.scrollIntoView) panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function showError(form, btn, label) {
    if (btn) { btn.disabled = false; btn.textContent = label; }
    var old = form.querySelector('.form-error'); if (old) old.remove();
    var err = el('p', 'form-error');
    err.setAttribute('role', 'alert');
    err.appendChild(document.createTextNode('Something went wrong sending that. Please try again, or call '));
    err.appendChild(phoneLink());
    err.appendChild(document.createTextNode(' or email info@kobaltconstruction.com.'));
    var row = form.querySelector('.form-submit-row');
    if (row) row.parentNode.insertBefore(err, row); else form.appendChild(err);
  }

  document.querySelectorAll('form.apply-form[data-form]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!window.fetch || !window.FormData) return;   /* older browsers: normal form post still works */
      e.preventDefault();
      var btn = form.querySelector('button[type="submit"]');
      var label = btn ? btn.textContent : '';
      if (btn) { btn.disabled = true; btn.textContent = 'Sending...'; }
      var stale = form.querySelector('.form-error'); if (stale) stale.remove();
      fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' } })
        .then(function (res) { if (!res.ok) throw new Error('status ' + res.status); })
        .then(function () { showSuccess(form); })
        .catch(function () { showError(form, btn, label); });
    });
  });
})();
