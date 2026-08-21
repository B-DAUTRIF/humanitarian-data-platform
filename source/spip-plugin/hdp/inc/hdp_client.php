<?php

if (!defined('_ECRIRE_INC_VERSION')) {
    return;
}

define('_HDP_BRIDGE_CONTRACT', 'hdp-spip/1.0');
define('_HDP_BRIDGE_MAX_RESPONSE', 5242880);

function hdp_bridge_configuration() {
    $url = defined('_HDP_BRIDGE_URL') ? trim(_HDP_BRIDGE_URL) : '';
    $token = defined('_HDP_BRIDGE_TOKEN') ? trim(_HDP_BRIDGE_TOKEN) : '';
    $parsed = $url ? parse_url($url) : false;
    if (!$parsed
        || ($parsed['scheme'] ?? '') !== 'https'
        || empty($parsed['host'])
        || !empty($parsed['user'])
        || !empty($parsed['pass'])
        || !empty($parsed['query'])
        || !empty($parsed['fragment'])
        || !empty(trim($parsed['path'] ?? '', '/'))) {
        return [false, '', '', 'La constante _HDP_BRIDGE_URL doit être une URL HTTPS.'];
    }
    if (strpos($token, 'hdps_') !== 0 || strlen($token) < 64) {
        return [false, '', '', 'La constante _HDP_BRIDGE_TOKEN est absente ou invalide.'];
    }
    return [true, rtrim($url, '/'), $token, ''];
}

function hdp_bridge_request($methode, $chemin, $corps = null, $idempotence = '') {
    [$ok, $base, $token, $erreur] = hdp_bridge_configuration();
    if (!$ok) {
        return ['ok' => false, 'status' => 0, 'error' => $erreur];
    }
    include_spip('inc/distant');
    $headers = [
        'Accept: application/json',
        'Authorization: Bearer ' . $token,
    ];
    $options = [
        'methode' => strtoupper($methode),
        'headers' => $headers,
        'timeout' => 20,
        'taille_max' => _HDP_BRIDGE_MAX_RESPONSE,
    ];
    if ($corps !== null) {
        $options['headers'][] = 'Content-Type: application/json';
        $options['datas'] = json_encode($corps, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }
    if ($idempotence !== '') {
        $options['headers'][] = 'Idempotency-Key: ' . $idempotence;
    }
    $reponse = recuperer_url($base . $chemin, $options);
    $status = intval($reponse['status'] ?? 0);
    $json = json_decode($reponse['page'] ?? '', true);
    if ($status < 200 || $status >= 300 || !is_array($json)) {
        return [
            'ok' => false,
            'status' => $status,
            'error' => is_array($json) ? ($json['detail'] ?? 'Réponse HDP refusée') : 'Réponse HDP invalide',
        ];
    }
    return ['ok' => true, 'status' => $status, 'data' => $json];
}

function hdp_verifier_document($item) {
    if (($item['status'] ?? '') === 'withdrawn') {
        return [true, null, ''];
    }
    $canonique = $item['document_canonical'] ?? '';
    $attendue = $item['content_sha256'] ?? '';
    if (!is_string($canonique) || !preg_match('/^[0-9a-f]{64}$/', $attendue)) {
        return [false, null, 'Contrat ou empreinte absent'];
    }
    if (!hash_equals($attendue, hash('sha256', $canonique))) {
        return [false, null, 'Empreinte du document incohérente'];
    }
    $document = json_decode($canonique, true);
    if (!is_array($document)
        || ($document['schema'] ?? '') !== _HDP_BRIDGE_CONTRACT
        || ($document['data_classification'] ?? '') !== 'public'
        || ($document['body_format'] ?? '') !== 'plain_text') {
        return [false, null, 'Document HDP hors contrat public'];
    }
    foreach (['publication_id', 'series_id', 'project_id', 'title', 'kind', 'revision'] as $champ) {
        if (!array_key_exists($champ, $document)) {
            return [false, null, 'Champ contractuel absent: ' . $champ];
        }
    }
    return [true, $document, ''];
}

function hdp_texte_sur($texte) {
    return htmlspecialchars((string) $texte, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function hdp_importer_publication($item) {
    [$ok, $document, $erreur] = hdp_verifier_document($item);
    $series = $item['series_id'] ?? '';
    if (!preg_match('/^[0-9a-f-]{36}$/i', $series)) {
        return [false, 0, 'Identifiant de série invalide'];
    }
    $existant = sql_fetsel('*', 'spip_hdp_publications', 'series_id=' . sql_quote($series));
    if (($item['status'] ?? '') === 'withdrawn') {
        if ($existant) {
            sql_updateq('spip_hdp_publications', [
                'statut' => 'refuse',
                'publication_id' => (string) ($item['id'] ?? ''),
                'date_maj' => date('Y-m-d H:i:s'),
            ], 'id_hdp_publication=' . intval($existant['id_hdp_publication']));
            return [true, intval($existant['id_hdp_publication']), ''];
        }
        return [true, 0, ''];
    }
    if (!$ok) {
        return [false, 0, $erreur];
    }
    if ($existant && intval($existant['revision']) > intval($document['revision'])) {
        return [true, intval($existant['id_hdp_publication']), ''];
    }
    $valeurs = [
        'series_id' => $document['series_id'],
        'publication_id' => $document['publication_id'],
        'project_id' => $document['project_id'],
        'revision' => intval($document['revision']),
        'kind' => substr((string) $document['kind'], 0, 40),
        'titre' => hdp_texte_sur($document['title']),
        'descriptif' => hdp_texte_sur($document['summary'] ?? ''),
        'texte' => hdp_texte_sur($document['body_text'] ?? ''),
        'source_snapshot' => json_encode($document['source_snapshot'] ?? [], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        'content_sha256' => $item['content_sha256'],
        'statut' => 'publie',
        'date_publication' => date('Y-m-d H:i:s'),
        'date_maj' => date('Y-m-d H:i:s'),
    ];
    if ($existant) {
        $id = intval($existant['id_hdp_publication']);
        sql_updateq('spip_hdp_publications', $valeurs, 'id_hdp_publication=' . $id);
    } else {
        $id = intval(sql_insertq('spip_hdp_publications', $valeurs));
    }
    return [$id > 0, $id, $id > 0 ? '' : 'Écriture SPIP impossible'];
}

function hdp_accuser_reception($item, $id, $statut) {
    $publication = $item['id'] ?? '';
    $empreinte = ($item['status'] ?? '') === 'withdrawn' ? '' : ($item['content_sha256'] ?? '');
    $cle = 'spip-' . hash('sha256', $publication . '|' . $statut . '|' . $empreinte);
    $url = $id ? url_absolue(generer_url_public('hdp_publication', 'id_hdp_publication=' . intval($id))) : '';
    return hdp_bridge_request(
        'POST',
        '/api/spip-bridge/v1/publications/' . rawurlencode($publication) . '/acknowledge',
        [
            'status' => $statut,
            'external_id' => $id ? (string) $id : '',
            'external_url' => $url,
            'content_sha256' => $empreinte,
        ],
        $cle
    );
}

function hdp_synchroniser_publications() {
    $curseur = $GLOBALS['meta']['hdp_bridge_cursor'] ?? '';
    $total = 0;
    for ($page = 0; $page < 20; $page++) {
        $chemin = '/api/spip-bridge/v1/publications?limit=50';
        if ($curseur !== '') {
            $chemin .= '&cursor=' . rawurlencode($curseur);
        }
        $reponse = hdp_bridge_request('GET', $chemin);
        if (!$reponse['ok']) {
            return $reponse;
        }
        $data = $reponse['data'];
        if (($data['contract'] ?? '') !== _HDP_BRIDGE_CONTRACT || !is_array($data['items'] ?? null)) {
            return ['ok' => false, 'error' => 'Version de contrat HDP-SPIP incompatible'];
        }
        foreach ($data['items'] as $item) {
            [$ok, $id, $erreur] = hdp_importer_publication($item);
            if (!$ok) {
                return ['ok' => false, 'error' => $erreur];
            }
            $statut = ($item['status'] ?? '') === 'withdrawn' ? 'withdrawn' : 'published';
            $accuse = hdp_accuser_reception($item, $id, $statut);
            if (!$accuse['ok']) {
                return ['ok' => false, 'error' => $accuse['error']];
            }
            $total++;
        }
        $curseur = $data['next_cursor'] ?? $curseur;
        if ($curseur !== '') {
            ecrire_meta('hdp_bridge_cursor', $curseur);
        }
        if (empty($data['has_more'])) {
            return ['ok' => true, 'count' => $total, 'error' => ''];
        }
    }
    return ['ok' => false, 'error' => 'Limite de 1000 changements atteinte; reprise au prochain cron'];
}
