document.addEventListener('DOMContentLoaded', function() {

  var source = document.URL;

  /* configure settings */
  if (typeof _404_SETTINGS === 'undefined') window._404_SETTINGS = {};
  if (!_404_SETTINGS.origin) _404_SETTINGS.origin = 'both';

  if (typeof _404_SETTINGS.include === 'undefined')
    _404_SETTINGS.include = 'a';

  var selector = _404_SETTINGS.include;
  if (_404_SETTINGS.exclude) {
    selector += ':not(' + _404_SETTINGS.exclude + ')';
  }
  /* end settings */

  var els = document.querySelectorAll(selector);

  for (var i = 0; i < els.length; i++) {
    els[i].addEventListener('click', function(event) {

      var link = event.currentTarget;

      var url = link.href; // the literal text of the 'href' property

      // the full url of where the link goes
      // http://stackoverflow.com/a/2639218
      var destination = link.getAttribute('href', 2);

      /* don't do anything if the url starts with a hash or is empty */
      if (url[0] === '#' || url.length === 0)
        return;

      /* don't do anything else if the origin setting doesn't match */
      if (_404_SETTINGS.origin === 'different' && sameOrigin(
        destination))
        return;
      else if (_404_SETTINGS.origin === 'same' && !sameOrigin(
        destination))
        return;
      // if we get here, the origin matches

      /* make the ctrl/Apple/meta keys work as expected */
      var blank = event.ctrlKey || event.metaKey || link.target ===
        ('_blank' || 'blank');
      if (!blank) event.preventDefault();

      var timer_id;
      ajaxGet(
        'http://monitor404.com/api/check/?source=' + 
        window.encodeURIComponent(source) + '&destination=' + 
        window.encodeURIComponent(destination),
        function(response) {
          if (timer_id)
            window.clearTimeout(timer_id);
          openUrl(destination, blank);
        }
      );
      timer_id = window.setTimeout(function() {
        console.error('Ajax request to server timed out.');
        openUrl(destination, blank)
      }, 500);

    });
  }



  /* utility functions */

  function openUrl(url, blank) {
    if (!blank) window.location = url;
  }

  function sameOrigin(url) {
    var link = document.createElement('a'); // TODO: make sure this doesn't cause a memory leak
    link.href = url;
    if (location.host === link.host) return true;
    else return false;
  }

  function ajaxGet(url, callback_success) {
    var req = new XMLHttpRequest();
    req.open('GET', url, true);
    req.onreadystatechange = function(aEvt) {
      if (req.readyState == 4) {
        if (req.status == 200)
          callback_success(req.responseText);
        else
          console.error('Error contacting api at url: ' + url);
      }
    };
    req.send(null);
  }

});