<?php

if (!defined('_ECRIRE_INC_VERSION')) {
    return;
}

function hdp_declarer_tables_objets_sql($tables) {
    $tables['spip_hdp_publications'] = [
        'type' => 'hdp_publication',
        'principale' => 'oui',
        'field' => [
            'id_hdp_publication' => 'bigint(21) NOT NULL',
            'series_id' => "varchar(36) NOT NULL DEFAULT ''",
            'publication_id' => "varchar(36) NOT NULL DEFAULT ''",
            'project_id' => "varchar(36) NOT NULL DEFAULT ''",
            'revision' => 'bigint(21) NOT NULL DEFAULT 1',
            'kind' => "varchar(40) NOT NULL DEFAULT ''",
            'titre' => "text NOT NULL DEFAULT ''",
            'descriptif' => "text NOT NULL DEFAULT ''",
            'texte' => "longtext NOT NULL DEFAULT ''",
            'source_snapshot' => "longtext NOT NULL DEFAULT ''",
            'content_sha256' => "char(64) NOT NULL DEFAULT ''",
            'statut' => "varchar(20) NOT NULL DEFAULT 'prepa'",
            'date_publication' => "datetime NOT NULL DEFAULT '0000-00-00 00:00:00'",
            'date_maj' => "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        ],
        'key' => [
            'PRIMARY KEY' => 'id_hdp_publication',
            'UNIQUE KEY series_id' => 'series_id',
            'KEY statut' => 'statut',
            'KEY publication_id' => 'publication_id',
        ],
        'titre' => "titre AS titre, '' AS lang",
        'date' => 'date_publication',
        'statut_textes_instituer' => [
            'prepa' => 'texte_statut_en_cours_redaction',
            'publie' => 'texte_statut_publie',
            'refuse' => 'texte_statut_refuse',
        ],
        'statut' => [['champ' => 'statut', 'publie' => 'publie', 'previsu' => 'publie,prepa']],
        'texte_objets' => 'hdp:publications_titre',
        'texte_objet' => 'hdp:publication_titre',
        'info_aucun_objet' => 'hdp:publication_aucune',
        'info_1_objet' => 'hdp:publication_une',
        'info_nb_objets' => 'hdp:publications_nombre',
        'page' => false,
        'url_voir' => '',
        'editable' => false,
        'champs_editables' => [],
        'champs_versionnes' => [],
        'rechercher_champs' => ['titre' => 8, 'descriptif' => 5, 'texte' => 3],
    ];
    return $tables;
}
