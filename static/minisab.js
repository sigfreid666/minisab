function marquer_lu(tabarticle) {
    console.log(tabarticle);
    $.ajax({
        url: 'articles/lu',
        type: 'POST',
        data: JSON.stringify(tabarticle),
        contentType: 'application/json; charset=utf-8',
        success: function(msg) {
            for (i = 0; i < tabarticle.length; i++) {
                $("#art_"+tabarticle[i]).remove();
            }
        }
    });
}

function marquer_lu_categorie(strcategorie) {
    $.get("categorie/" + strcategorie + "/lu",
        function(data, status) {
            if (status == "success") {
                console.log("OK");
                $("div.categorie > table").remove();
            }
        })
}


function marquer_favoris(idarticle) {
    $.get("article/" + idarticle + "/favoris",
        function(data, status) {
            if (status == "success") {
                $("#cat_favoris").append(data)
            }
        })
    $("#art_"+idarticle).remove();
}

function lancer_recherche(idarticle) {
    $.get("article/" + idarticle + "/recherche",
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

function envoyer_sab(idrecherche, idarticle) {
    var categorie = $("#art_"+idarticle+" select option:selected").text()
    console.log("envoyer_sab " + categorie);
	if (categorie == "*") {
		var url = "recherche/" + idrecherche + "/telecharger/"; }
	else {
		var url = "recherche/" + idrecherche + "/telecharger/" + categorie; }
    $.get(url,
        function(data, status) {
            if (status == "success") {
                console.log("OK envoyer_sab");
            }
        })
    $("#recherche_"+idrecherche).text($("#recherche_"+idrecherche).text() + " (En cours)");   
}

function deplier_recherche(idarticle) {
    val = $("#art_"+idarticle+" > div.list-group").css("display")
    if (val == "block") {
        $("#art_"+idarticle+" > div.list-group").css("display", "none");
    }
    else {
        $("#art_"+idarticle+" > div.list-group").css("display", "block");
    }
}
