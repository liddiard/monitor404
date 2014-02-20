$(document).ready(function(){

    var source = document.URL;

    /* configure settings */
    if (typeof _404_SETTINGS === 'undefined') _404_SETTINGS = {};
    if (!_404_SETTINGS.origin) _404_SETTINGS.origin = 'both';

    if (typeof _404_SETTINGS.include === 'undefined') 
        _404_SETTINGS.include = 'a';
    if (typeof _404_SETTINGS.exclude === 'undefined') 
        _404_SETTINGS.exclude = '';
    var selector = $(_404_SETTINGS.include).not(_404_SETTINGS.exclude);
    /* end settings */

    selector.click(function(event){
        var destination = $(this).prop('href');

        /* don't do anything if the url starts with a hash or is empty */
        if (destination[0] === '#' || destination.length === 0)
            return;

        /* don't do anything else if the origin setting doesn't match */
        if (_404_SETTINGS.origin === 'different' && sameOrigin(destination))
            return;
        else if (_404_SETTINGS.origin === 'same' && !sameOrigin(destination))
            return;
        // if we get here, the origin matches

        /* make the ctrl/Apple/meta keys work as expected */
        var blank = event.ctrlKey || event.metaKey || $(this).prop('target') === ('_blank' || 'blank');
        if (!blank) event.preventDefault();

        var timer_id;
        ajaxGet(
            {source: source, destination: destination},
            'http://monitor404.com/api/check/',
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

    function ajaxGet(params, endpoint, callback_success) {
        $.ajax({
            type: "GET",
            url: endpoint,
            data: params,
            crossDomain: true,
            success: callback_success,
            error: function(xhr, textStatus, errorThrown) {
                if (xhr.status != 0)
                    console.error('Oh no! Something went wrong. Please report this error: \n'+errorThrown+xhr.status+xhr.responseText);
            }
        }); 
    }

});
