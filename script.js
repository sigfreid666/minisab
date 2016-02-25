function sendmessage() {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (xhttp.readyState == 4 && xhttp.status == 200) {
        var x = document.querySelectorAll("article.favoris");
        for (i = 0; i < x.length; i++) {
            x[i].style.visiblity = "hidden";
            x[i].style.display = "none";
        }
    }
  };
  xhttp.open("GET", "/minisab/miniflux.cgi?testjava", true);
  xhttp.send();
}

function supprimerfavoris(idminiflux, idsab) {
  // document.getElementById ("res").innerHTML = "Debug : envoie requete"
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function () {
    if (xhttp.readyState == 4 && xhttp.status == 200) {
        // document.getElementById ("res").innerHTML = xhttp.responseText;
        var o = JSON.parse(xhttp.responseText);
        document.getElementById (o.supprimer[0].id).style.display = "none";
    }
  }
  xhttp.open("POST", "miniflux.cgi", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("action=supprimerfavoris&miniflux=" + idminiflux + "&sab=" + idsab);//JSON.stringify(test));
  // xhttp.send(null);
}

function lancer_telechargement(idtelechargement, titre, idhtml) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function () {
    if (xhttp.readyState == 4 && xhttp.status == 200 && xhttp.responseText == 'OK') {
        document.getElementById (idhtml).style.display = "none";
    }
  }
  xhttp.open("POST", "miniflux.cgi", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("action=telechargement&id=" + idtelechargement + "&titre=" + titre);
}
