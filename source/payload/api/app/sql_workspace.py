from __future__ import annotations

import re


ALLOWED_SQL_RELATIONS = frozenset(
    {
        "hdp_acquisitions",
        "hdp_artifacts",
        "hdp_federated_searches",
        "hdp_resources",
        "hdp_schedules",
        "hdp_processing_runs",
    }
)

FORBIDDEN_SQL_WORDS = frozenset(
    {
        "alter", "analyze", "call", "cluster", "comment", "copy", "create",
        "delete", "discard", "do", "drop", "execute", "grant", "insert", "listen",
        "load", "lock", "merge", "notify", "prepare", "reassign", "refresh", "reindex",
        "reset", "revoke", "security", "set", "truncate", "update", "vacuum",
    }
)

FORBIDDEN_SQL_FUNCTIONS = frozenset(
    {
        "dblink", "lo_export", "lo_import", "pg_advisory_lock", "pg_cancel_backend",
        "pg_read_binary_file", "pg_read_file", "pg_reload_conf", "pg_sleep",
        "pg_terminate_backend", "set_config",
    }
)

ALLOWED_SQL_FUNCTIONS = frozenset(
    {
        "abs", "any", "array_length", "avg", "btrim", "cast", "ceil", "ceiling",
        "char_length", "coalesce", "concat", "concat_ws", "count", "date_trunc",
        "exists", "explain", "extract", "filter", "floor", "greatest", "in",
        "jsonb_array_length", "jsonb_extract_path_text", "jsonb_typeof", "least",
        "length", "lower", "ltrim", "max", "min", "nullif", "over", "replace",
        "round", "rtrim", "string_agg", "substring", "sum", "to_char", "trim", "upper",
    }
)


def _code_only(sql: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    without_line_comments = re.sub(r"--[^\r\n]*", " ", without_block_comments)
    without_dollar_quotes = re.sub(r"\$[^$]*\$.*?\$[^$]*\$", "''", without_line_comments, flags=re.DOTALL)
    return re.sub(r"'(?:''|[^'])*'", "''", without_dollar_quotes)


def validate_readonly_sql(sql: str, *, max_length: int = 20_000) -> str:
    statement = sql.strip()
    if not statement:
        raise ValueError("La requête SQL est vide")
    if len(statement) > max_length:
        raise ValueError("La requête SQL est trop longue")
    code = _code_only(statement).strip()
    if ";" in code.rstrip(";"):
        raise ValueError("Une seule instruction SQL est autorisée")
    code = code.rstrip(";").strip()
    if not re.match(r"^(select\b|explain\s+(?:\([^)]*\)\s*)?select\b)", code, re.IGNORECASE):
        raise ValueError("Seules les requêtes SELECT ou EXPLAIN SELECT sont autorisées")
    words = {word.casefold() for word in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code)}
    forbidden = sorted(words & FORBIDDEN_SQL_WORDS)
    if forbidden:
        raise ValueError(f"Mot-clé SQL interdit : {forbidden[0]}")
    functions = {
        name.casefold()
        for name in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", code)
    }
    forbidden_functions = sorted(functions & FORBIDDEN_SQL_FUNCTIONS)
    if forbidden_functions:
        raise ValueError(f"Fonction SQL interdite : {forbidden_functions[0]}")
    unknown_functions = sorted(functions - ALLOWED_SQL_FUNCTIONS)
    if unknown_functions:
        raise ValueError(f"Fonction SQL non autorisée : {unknown_functions[0]}")
    from_segments = re.findall(
        r"\bfrom\b(.*?)(?=\bwhere\b|\bgroup\b|\border\b|\blimit\b|\bunion\b|$)",
        code,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if any("," in segment for segment in from_segments):
        raise ValueError("Utilisez JOIN : les relations séparées par une virgule sont interdites")
    relations = {
        name.casefold().split(".")[-1].strip('"')
        for name in re.findall(
            r"\b(?:from|join)\s+([A-Za-z_][A-Za-z0-9_.]*|\"[^\"]+\")",
            code,
            flags=re.IGNORECASE,
        )
    }
    if not relations:
        raise ValueError("La requête doit lire au moins une vue HDP")
    forbidden_relations = sorted(relations - ALLOWED_SQL_RELATIONS)
    if forbidden_relations:
        raise ValueError(f"Relation SQL non autorisée : {forbidden_relations[0]}")
    return code
