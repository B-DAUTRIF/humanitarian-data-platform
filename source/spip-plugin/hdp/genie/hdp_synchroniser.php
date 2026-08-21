<?php

if (!defined('_ECRIRE_INC_VERSION')) {
    return;
}

function genie_hdp_synchroniser_dist($time) {
    include_spip('inc/hdp_client');
    $resultat = hdp_synchroniser_publications();
    if (!$resultat['ok']) {
        spip_log('Synchronisation interrompue: ' . $resultat['error'], 'hdp' . _LOG_ERREUR);
        return 0;
    }
    return 1;
}
