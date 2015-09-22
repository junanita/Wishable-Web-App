var ajaxPending= false;

window.onload = function(){
    $("#userSearchBtn").on("click", searchUser);
};


// Taken from docs.djangoproject.com
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

function searchUser(event){
    event.preventDefault();
    console.log("search user");
    var searchButton = $(this);
    var searchName = $("#id_search").val();
    console.log(searchName);

    var csrftoken = getCookie('csrftoken');

    if (!ajaxPending){
        ajaxPending = true;
        $.ajax({
            url: "/wishing-well",
            type: "POST",
            data:{
            	search: searchName,
                csrfmiddlewaretoken: csrftoken
            },

            success: function(data){
                console.log("success scraped product");
                if (data == "error"){
                	$(".modal-body").append("<h6> Could not find users </h6>");
                }
                else{
                	$(".modal-body").append(data);
                }
                $(".close").click(function(){
                	console.log("closing modal");
                    $(".modal-body").html("");
                });
                ajaxPending = false;
            },

            error: function( req, status, err ) {
                console.log( 'something went wrong', status, err );
                ajaxPending = false;
            }
        });
    }
}


