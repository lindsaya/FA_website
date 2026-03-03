document.addEventListener('DOMContentLoaded', () => {
  const content = document.getElementById('page-content');

  // Fade in on load
  if (content) {
    content.style.opacity = '0';
    content.style.transition = 'opacity 0.25s ease';
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        content.style.opacity = '1';
      });
    });
  }

  // Fade out on nav link click (skip anchors and external links)
  document.querySelectorAll('nav a').forEach(link => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      if (!href || href.startsWith('#') || link.target === '_blank') return;
      // Skip anchor-only parts of index links (e.g. index.html#reel when already on index)
      const isSamePage = link.pathname === window.location.pathname;
      if (isSamePage) return;
      e.preventDefault();
      if (content) {
        content.style.opacity = '0';
        setTimeout(() => { window.location.href = href; }, 250);
      } else {
        window.location.href = href;
      }
    });
  });
});
