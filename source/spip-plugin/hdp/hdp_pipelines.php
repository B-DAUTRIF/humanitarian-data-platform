<?php

if (!defined('_ECRIRE_INC_VERSION')) {
    return;
}

function hdp_taches_generales_cron($taches) {
    $taches['hdp_synchroniser'] = 300;
    return $taches;
}
