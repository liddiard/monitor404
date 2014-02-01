$(document).ready(function(){
    var source = document.URL;
    $('a').click(function(event){
        event.preventDefault();
        var destination = $(this).prop('href');
        ajaxGet(
            {source: source, destination: destination},
            'http://localhost:8000/api/check/',
            function(response){ console.log(response); window.location = destination; }
        );
        // window.location = destination;
    });
});

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
