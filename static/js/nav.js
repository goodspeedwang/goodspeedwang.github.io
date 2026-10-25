(function () {
  'use strict';
  var container = document.getElementById('nav');

  function render(data) {
    (data.groups || []).forEach(function (group) {
      var cat = document.createElement('div');
      cat.className = 'category';

      var title = document.createElement('div');
      title.className = 'category-title';
      title.textContent = group.name || '';
      cat.appendChild(title);

      var links = document.createElement('div');
      links.className = 'links';

      (group.links || []).forEach(function (link) {
        var el = document.createElement('div');
        el.className = 'link' + (link.hot ? ' hot' : '');

        var a = document.createElement('a');
        a.href = link.url || '';
        a.target = '_blank';
        a.rel = 'noopener noreferrer';

        if (link.favicon) {
          var img = document.createElement('img');
          img.className = 'favicon';
          img.src = link.favicon;
          img.alt = '';
          img.loading = 'lazy';
          a.appendChild(img);
        }
        a.appendChild(document.createTextNode(link.name || ''));

        el.appendChild(a);
        links.appendChild(el);
      });

      cat.appendChild(links);
      container.appendChild(cat);
    });
  }

  fetch('nav.json')
    .then(function (resp) {
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      return resp.json();
    })
    .then(render)
    .catch(function (err) {
      container.textContent = '加载导航数据失败：' + err;
    });
})();
