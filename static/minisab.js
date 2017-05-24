function marquer_favoris(idarticle) {
    $.get("/article/" + idarticle + "/favoris",
        function(data, status) {
            if (status == 200) {
                console.log("OK");
            }
        })
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