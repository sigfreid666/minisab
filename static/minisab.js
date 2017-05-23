function marquer_favoris(id) {
    $.get("/article/" + id + "/favoris",
        function(data, status) {
            if (status == 200) {
                console.write("OK");
            }
        })
}

function lancer_recherche(id) {
    $.get("/article/" + id + "/recherche",
        function(data, status) {
            if (status == 200) {
                console.write("OK");
            }
        })
}