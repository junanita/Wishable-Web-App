var ajaxPending = false;
$(document).ready(function(){
	$(".modal-close").click(function(){
		$('.modal').find("textarea").val('');
		$('.modal').find("input").removeAttr('checked');
		$('.modal').find("input:text").val('');
	});
	$("body").on("click", ".delete-wishlist", deleteWishList);
});

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

function deleteWishList(event){
    event.preventDefault();
    var deleteBtn = $(this);
    var csrftoken = getCookie('csrftoken');
    var wishlistId = $(deleteBtn).attr("wId");

    if (!ajaxPending){
        ajaxPending = true;
        $.ajax({
            url: "/delete-wishlist/",
            type: "POST",
            data:{
                    wId: wishlistId,
                    csrfmiddlewaretoken: csrftoken
            },

            success: function(data){
                // remove wishlist item from view
                // data should be the id of the wishlist item
                if (data){
                    var findString = "div[wId=" + data + "]";
                    $(findString).remove();
                    $.notify("Removed wishlist!", "success");
                } else {
                    $.notify("Could not delete wishlist", "error");
                }
                ajaxPending = false;
            },

            error: function( req, status, err ) {
                console.log( 'something went wrong', status, err );
                ajaxPending = false;
            }

        });
    }
}