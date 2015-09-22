var ajaxPending = false;

window.onload = function(){
    $(".wishlist-to-add").on("click", ".wl", addToWishList);
    $("body").on("click", ".delete-wli", deleteWishListItem);
    // $(".delete-wli").on("click", deleteWishListItem);
    console.log("hi");
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

function deleteWishListItem(event){
    console.log("trying to delte");
    event.preventDefault();
    var deleteBtn = $(this);
    var csrftoken = getCookie('csrftoken');
    var wishlistItemId = $(deleteBtn).attr("wItemId");

    if (!ajaxPending){

        ajaxPending = true;
        $.ajax({
            url: "/delete-wishlist-item/",
            type: "POST",
            data:{
                    wItemId: wishlistItemId,
                    csrfmiddlewaretoken: csrftoken
            },

            success: function(data){
                console.log("success removed from wishlist");
                // remove wishlist item from view
                // data should be the id of the wishlist item
                if(data){
                    var findString = "tr[wItemId=" + data + "]";
                    $(findString).remove();
                    $.notify("Removed item from wishlist!", "success");
                }else{
                    $.notify("Couldn't remove item.", "error");
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

function addToWishList(event){
    event.preventDefault();
    var submitButton = $(this);

    var prod_id = $(submitButton).attr("cItem-id");
    var wishlist_id = $(submitButton).attr("wishlist-id"); 
    var csrftoken = getCookie('csrftoken');

    $(submitButton).closest(".dropdown-menu").prev().dropdown("toggle");
    if (!ajaxPending){
        ajaxPending = true;
        $.ajax({
            url: "/add-to-wishlist/",
            type: "POST",
            data:{
                    productId: prod_id,
                    wishlistId: wishlist_id,
                    csrfmiddlewaretoken: csrftoken
            },

            success: function(data){
                event.preventDefault();
                console.log("success called add-to-wishlist");
                // close dropdowns
                ajaxPending = false;
                console.log(data);
                if (data == "success"){
                    $.notify("Added item to wishlist", "success");
                }else{
                    $.notify(data, "error");
                }
            },

            error: function( req, status, err ) {
                console.log( 'something went wrong', status, err );
                ajaxPending = false;
            }

        });
    }
}

