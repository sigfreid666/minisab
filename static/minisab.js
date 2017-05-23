function marquer_favoris(id) {
    $.get("/article/" + id + "/favoris",
        function(data, status) {
            if (status == 200) {
                console.write("OK");
            }
        })
}