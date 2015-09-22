var ajaxPending= false;

window.onload = function(){
    $(".wishlist-to-add").on("click", ".wl", addToWishList);
    $("#scrape-btn").on("click", scrapeProd);
    $(".new-prod-modal").on("click", "#add-new-prod", addNewProd);
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

function scrapeProd(event){
    event.preventDefault();
    var scrapeButton = $(this);
    var prodLink = $("#id_product_link").val();

    var csrftoken = getCookie('csrftoken');

    if (!ajaxPending){
        ajaxPending = true;
        $.ajax({
            url: "/scrape-product/",
            type: "POST",
            data:{
                product_link: prodLink,
                csrfmiddlewaretoken: csrftoken
            },

            success: function(data){
                console.log("success scraped product");
                $(".modal-body").append(data);
                $("#scrape-btn").hide();

                $(".modal-close").click(function(){
                    console.log("closing modal");
                    $('.modal').find(".scraped-prod-info").remove();
                    $("#id_product_link").val('');
                    $("#scrape-btn").show();
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


function addNewProd(event){
    event.preventDefault();
    console.log("adding new prod");
    var dataArray = $("form").serializeArray();
    var len = dataArray.length;
    var dataObj = {};
    var csrftoken = getCookie('csrftoken');

    for (i=0; i<len; i++) {
      dataObj[dataArray[i].name] = dataArray[i].value;
    }

    if (!ajaxPending){
        ajaxPending = true
        $.ajax({
            url: "/add-new-product/",
            type: "POST",
            data: {
                data: JSON.stringify(dataObj),
                csrfmiddlewaretoken: csrftoken
            },

            success: function(data){
                ajaxPending = false;
                if (data == "success"){
                    $.notify("Added item to wishlist", "success");
                    console.log("success scraped product");
                    $('.modal').find(".scraped-prod-info").remove();
                    $("#id_product_link").val('');
                    $("#scrape-btn").show();
                    $(".modal").modal('hide');
                    location.reload(true);
                }else{
                    console.log(data);
                    $.each(JSON.parse(data), function(key, value) {
                        $.notify(key + " is required.", "error");
                    });
                }
            },

            error: function( req, status, err ) {
                console.log( 'something went wrong', status, err );
                ajaxPending = false;
            }
        });
    }
}
