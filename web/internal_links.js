window.onload = function() {
    
    //TODO:dry
    var jupyterLink = document.getElementById("jupyterLink");
    var pgadminLink = document.getElementById("pgadminLink");
    var kibanaLink = document.getElementById("kibanaLink");
    var geoserverLink= document.getElementById("geoserverLink");
    var exportLink= document.getElementById("exportLink");


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

    geoserverLink.onclick = function() {
        hostbase = document.location.host;
        fullpath = `http://geoserver.${hostbase}/geoserver/web/`;
        window.location.href = fullpath;
    }

    exportLink.onclick = function() {
        hostbase = document.location.host;
        fullpath = `http://${hostbase}/export/`;
        window.location.href = fullpath;
    }


}