function marquer_lu(tabarticle, idcatdepart) {
    $.ajax({
        url: 'articles/lu',
        type: 'POST',
        data: JSON.stringify(tabarticle),
        contentType: 'application/json; charset=utf-8',
        success: function(msg) {
            for (i = 0; i < tabarticle.length; i++) {
                $("#art_"+tabarticle[i]).remove();
            }
            $.get("categorie/" + idcatdepart,
                function(data, status) {
                    if (status == "success") {
                        $("#cat_" + idcatdepart).replaceWith(data);
                    }
                }
            );
        }
    });
}


function marquer_favoris(idarticle, idcatdepart, idcatarrivee) {
    $.get("article/" + idarticle + "/favoris/categorie",
        function(data, status) {
            if (status == "success") {
                $("#art_"+idarticle).remove();
                $("#items_" + idcatarrivee).append(data[0]);
                $("#cat_" + idcatarrivee).replaceWith(data[1]);
                $("#cat_" + idcatarrivee + '_end').replaceWith(data[2]);
                $("#cat_" + idcatdepart).replaceWith(data[3]);
                $("#cat_" + idcatdepart + '_end').replaceWith(data[4]);
            }
        });
}

function lancer_recherche(idarticle) {
    var stop_multi = $("#rec_multiple_" + idarticle).val();
    if (stop_multi != '') {
        url = "article/" + idarticle + "/recherche/" + stop_multi;
    }
    else {
        url = "article/" + idarticle + "/recherche";
    }

    $.get(url,  
        function(data, status) {
            if (status == "success") {
                console.log("OK");
                $("#art_"+idarticle).replaceWith(data);
            }
            else {
                $("#art_"+idarticle+" > div.resultat_recherche").text('<button type="button" class="list-group-item">Erreur</button>');
            }

        })
}

function envoyer_sab(idrecherche, idarticle) {
    var categorie = $("#art_"+idarticle+" div.recherche button.btn-danger").text()
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

function change_selection(idarticle, categorie){
    $("#art_"+idarticle+" div.recherche button.btn-danger").removeClass('btn-danger').addClass('btn-default');
    $("#art_"+idarticle+" div.recherche button." + categorie).removeClass('btn-default').addClass('btn-danger');
    console.log('Test <' + categorie + '>');
}