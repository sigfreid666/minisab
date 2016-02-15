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
