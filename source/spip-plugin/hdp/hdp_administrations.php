<?php

if (!defined('_ECRIRE_INC_VERSION')) {
    return;
}

function hdp_upgrade($nom_meta_base_version, $version_cible) {
    $maj = [];
    $maj['create'] = [['maj_tables', ['spip_hdp_publications']]];
    include_spip('base/upgrade');
    maj_plugin($nom_meta_base_version, $version_cible, $maj);
}

function hdp_vider_tables($nom_meta_base_version) {
    sql_drop_table('spip_hdp_publications');
    effacer_meta('hdp_bridge_cursor');
    effacer_meta($nom_meta_base_version);
}
