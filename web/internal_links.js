window.onload = function() {
    
    //TODO:dry
    var jupyterLink = document.getElementById("jupyterLink");
    var pgadminLink = document.getElementById("pgadminLink");
    var kibanaLink = document.getElementById("kibanaLink");

    jupyterLink.onclick = function() {
        hostbase = document.location.host;
        fullpath = `http://jupyter.${hostbase}/lab`;
        window.location.href = fullpath;}

    pgadminLink.onclick = function() {
            hostbase = document.location.host;
            fullpath = `http://pgadmin.${hostbase}`;
            window.location.href = fullpath;}

    kibanaLink.onclick = function() {
                hostbase = document.location.host;
                fullpath = `http://kibana.${hostbase}`;
                window.location.href = fullpath;
    }

}