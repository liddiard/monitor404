$(document).ready(function(){

    var source = document.URL;

    /* configure settings */
    if (typeof _404_SETTINGS == 'undefined') _404_SETTINGS = {};
    if (!_404_SETTINGS.origin) _404_SETTINGS.origin = 'both';

    if (typeof _404_SETTINGS.include == 'undefined') 
        _404_SETTINGS.include = 'a';
    if (typeof _404_SETTINGS.exclude == 'undefined') 
        _404_SETTINGS.exclude = '';
    var selector = $(_404_SETTINGS.include).not(_404_SETTINGS.exclude);
    /* end settings */

    selector.click(function(event){
        var destination = $(this).prop('href');
        /* don't do anything else if the origin setting doesn't match */
        if (_404_SETTINGS.origin == 'different' && sameOrigin(destination))
            return;
        else if (_404_SETTINGS.origin == 'same' && !sameOrigin(destination))
            return;
        // if we get here, the origin matches
        event.preventDefault();
        ajaxGet(
            {source: source, destination: destination},
            'http://localhost:8000/api/check/',
            function(response) {
                if (response.error404 && _404_SETTINGS.callback)
                    _404_SETTINGS.callback;
                else
                    console.log(response);
            }
        );
        if (!_404_SETTINGS.callback)
            window.location = destination;
    });
});


/* utility functions */

function sameOrigin(url) {
    var link = document.createElement('a'); // TODO: make sure this doesn't cause a memory leak
    link.href = url;
    if (location.host == link.host) return true;
    else return false;
}

function ajaxGet(params, endpoint, callback_success) {
    $.ajax({
        type: "GET",
        url: endpoint,
        data: params,
        success: callback_success,
        error: function(xhr, textStatus, errorThrown) {
            console.log("Oh no! Something went wrong. Please report this error: \n"+errorThrown+xhr.status+xhr.responseText);
        }
    }); 
}
