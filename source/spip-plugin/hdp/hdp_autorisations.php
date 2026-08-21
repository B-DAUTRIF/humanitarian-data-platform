<?php

if (!defined('_ECRIRE_INC_VERSION')) {
    return;
}

function hdp_autoriser() {
}

function autoriser_hdp_voir_dist($faire, $type, $id, $qui, $opt) {
    return !empty($qui['id_auteur']);
}

function autoriser_hdp_publication_voir_dist($faire, $type, $id, $qui, $opt) {
    if (empty($qui['id_auteur'])) {
        return false;
    }
    if (in_array($qui['statut'] ?? '', ['0minirezo', '1comite'], true)) {
        return true;
    }
    return sql_getfetsel(
        'id_hdp_publication',
        'spip_hdp_publications',
        ['id_hdp_publication=' . intval($id), "statut='publie'"]
    ) !== null;
}

function autoriser_hdp_synchroniser_dist($faire, $type, $id, $qui, $opt) {
    return ($qui['statut'] ?? '') === '0minirezo' && !empty($qui['webmestre']);
}

function autoriser_hdp_publication_modifier_dist($faire, $type, $id, $qui, $opt) {
    return false;
}
