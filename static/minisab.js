function marquer_lu(idarticle) {
    $.get("/article/" + idarticle + "/lu",
        function(data, status) {
            if (status == "success") {
                console.log("OK");
                $("#art_"+idarticle).remove();
            }
        })
}


function marquer_favoris(idarticle) {
    $.get("/article/" + idarticle + "/favoris",
        function(data, status) {
            if (status == "success") {
                $("#cat_favoris").append(data)
            }
        })
    $("#art_"+idarticle).remove();
}

function lancer_recherche(idarticle) {
    $.get("/article/" + idarticle + "/recherche",
        function(data, status) {
            if (status == "success") {
                console.log("OK");
                $("#art_"+idarticle).replaceWith(data);
            }
            else {
                $("#art_"+idarticle+" > span.recherche").text("Erreur !");
            }

        })
    $("#art_"+idarticle+" > span.recherche").text("Recherche...");
}

function envoyer_sab(idrecherche) {
    $.get("/recherche/" + idrecherche + "/telecharger",
        function(data, status) {
            if (status == "success") {
                console.log("OK envoyer_sab");
            }
        })
    $("#recherche_"+idrecherche).text($("#recherche_"+idrecherche).text() + " (En cours)");   
}