// Docsify settings, and the one page behaviour that is not a plugin.
// Kept in a file rather than inline in index.html: the site's
// Content-Security-Policy allows scripts from files only, so a script
// injected into a page cannot run.
window.$docsify = Object.assign(window.$docsify || {}, {
  name: 'aCupOfTea',
  repo: 'AhmedYousriSobhi/aCupOfTea',
  // basePath: '../', // Tell docsify to look for the markdown files in the parent directory
  loadSidebar: './.docs/_sidebar.md',
  loadNavbar: './.docs/_navbar.md',
  notFoundPage: './.docs/_404.md',
  relativePath: false, // Use relative paths for sidebar and navbar links
  // Below 1400px the right-hand outline is hidden, so list the page's
  // sections (h2, h3) under it in the sidebar instead.
  subMaxLevel: window.matchMedia('(max-width: 1399px)').matches ? 3 : 0,
  auto2top: true,
  plugins: [window.themeToggle],
   pagination: {
    previousText: 'Previous',
    nextText: 'Next',
    crossChapter: true,
    crossChapterText: true,
  },
  // Configure the tabs plugin
  tabs: {
    persist: true,      // stay on the same tab when refreshing
    sync: true,         // sync tabs with same label across page
    theme: 'classic',   // 'classic' or 'material'
  },
  // Add this to help Docsify match URLs to the sidebar entries
  alias: {
    '/(.*)/_sidebar.md': './.docs/_sidebar.md',
    '/(.*)/_navbar.md': './.docs/_navbar.md'
  },
});

// On phones the sidebar covers the page: close it after a section link is
// tapped so the reader lands on the heading, not on the menu.
document.addEventListener('click', function (e) {
  var link = e.target.closest && e.target.closest('.sidebar-nav a.section-link');
  if (!link || window.innerWidth > 768) return;
  setTimeout(function () {
    var open = document.querySelector('aside.sidebar.show');
    var toggle = document.querySelector('button.sidebar-toggle');
    if (open && toggle) toggle.click();
  }, 0);
});
