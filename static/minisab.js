function marquer_lu(url, tabarticle, idcatdepart) {
    $.ajax({
        url: url,
        type: 'POST',
        data: JSON.stringify(tabarticle),
        contentType: 'application/json; charset=utf-8',
        success: function(data) {
            for (i = 0; i < tabarticle.length; i++) {
                $("#art_"+tabarticle[i]).remove();
            }
            $("#cat_" + idcatdepart).replaceWith(data[0]);
            $("#cat_" + idcatdepart + '_end').replaceWith(data[1]);
        }
    });
}

function marquer_lu_barre(url, tabarticle, idcatdepart) {
    $.ajax({
        url: url,
        type: 'POST',
        data: JSON.stringify(tabarticle),
        contentType: 'application/json; charset=utf-8',
        success: function(msg) {
            for (i = 0; i < tabarticle.length; i++) {
                $("#art_"+tabarticle[i]).remove();
            }
            $("#cat_" + idcatdepart).remove();
            $("#cat_" + idcatdepart + '_end').remove();
            $("#cat_" + idcatdepart + '_barre').remove();
        }
    });
}

function marquer_favoris(url, idarticle, idcatdepart, idcatarrivee) {
    $.get(url,
        function(data, status) {
            if (status == "success") {
                $("#art_"+idarticle).remove();
                $("#items_" + idcatarrivee).append(data[0]);
                $("#cat_" + idcatarrivee).replaceWith(data[1]);
                $("#cat_" + idcatarrivee + '_end').replaceWith(data[2]);
                $("#cat_" + idcatdepart).replaceWith(data[3]);
                $("#cat_" + idcatdepart + '_end').replaceWith(data[4]);
                $("#barre_categorie").replaceWith(data[5]);
            }
        });
}

function lancer_recherche(url, idarticle) {
    var stop_multi = $("#rec_multiple_" + idarticle).val();
    if (stop_multi != '') {
        url = url + "/" + stop_multi;
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

function envoyer_sab(url, idrecherche, idarticle) {
    var categorie = $("#art_"+idarticle+" div.recherche button.btn-danger").text()
    console.log("envoyer_sab " + categorie);
	if (categorie != "*") {
		url = url + categorie; }
    $.get(url,
        function(data, status) {
            if (status == "success") {
                console.log("OK envoyer_sab");
            }
        })
    $("#recherche_"+idrecherche).text($("#recherche_"+idrecherche).text() + " (En cours)");   
}

function envoyer_sab_tous(url, idarticle) {
    var categorie = $("#art_"+idarticle+" div.recherche button.btn-danger").text()
    console.log("envoyer_sab " + categorie);
    if (categorie != "*") {
        url = url + categorie; }
    $.get(url,
        function(data, status) {
            if (status == "success") {
                console.log("OK envoyer_sab");
            }
        })
    // $("#recherche_"+idrecherche).text($("#recherche_"+idrecherche).text() + " (En cours)");   
}

function change_selection(idarticle, categorie){
    $("#art_"+idarticle+" div.recherche button.btn-danger").removeClass('btn-danger').addClass('btn-default');
    $("#art_"+idarticle+" div.recherche button." + categorie).removeClass('btn-default').addClass('btn-danger');
    console.log('Test <' + categorie + '>');
}

function change_selection_cat(idarticle, categorie){
    $("#art_"+idarticle+" div.recherche button.btn-danger").removeClass('btn-danger').addClass('btn-default');
    $("#art_"+idarticle+" div.recherche button." + categorie).removeClass('btn-default').addClass('btn-danger');
    console.log('Test <' + categorie + '>');
    var url = "/categorie/" + idarticle + "/sabnzbd/" + categorie
    $.get(url,
        function(data, status) {
            if (status == "success") {
                console.log("OK envoyer_sab");
            }
        })
}
