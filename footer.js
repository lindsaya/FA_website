// Canonical footer — edit here to update site-wide
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var footer = document.querySelector('footer');
    if (!footer) return;
    footer.innerHTML =
      '\n  <div class="footer-location">Sydney, NSW \u00a0\u00b7\u00a0 Australia</div>' +
      '\n  <div class="footer-copy">\u00a9 Future Associate Pty Ltd \u00b7 All Rights Reserved</div>\n';
  });
})();
