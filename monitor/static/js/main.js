$(document).ready(function(){

    $(document).foundation();

    $('table.log').tablesorter({sortList: [[3,1]]});

    $('form input[type=text]:visible').first().focus();

    $('.log-clear').click(function(){
        var confirmed = confirm('Are you sure you want to clear the log for '+window.context.site+'?');
        if (confirmed) {
            ajaxPost(
                {slug: window.context.slug},
                '/api/log/clear/',
                function(response){ console.log(response) }
            );
            $('table.log tbody tr').remove();
        }
    });

});


/* utility functions */

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function ajaxPost(params, endpoint, callback_success) {
    params.csrfmiddlewaretoken = getCookie('csrftoken');
    $.ajax({
        type: "POST",
        url: endpoint,
        data: params,
        success: callback_success,
        error: function(xhr, textStatus, errorThrown) {
            console.log("Oh no! Something went wrong. Please report this error: \n"+errorThrown+xhr.status+xhr.responseText);
        }
    }); 
}
