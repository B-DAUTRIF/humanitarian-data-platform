from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from pglast import parser


ALLOWED_SQL_RELATIONS = frozenset(
    {
        "hdp_acquisitions",
        "hdp_artifacts",
        "hdp_federated_searches",
        "hdp_resources",
        "hdp_schedules",
        "hdp_processing_runs",
        "hdp_hdx_metadata",
        "hdp_signals",
    }
)

ALLOWED_SQL_FUNCTIONS = frozenset(
    {
        "abs", "array_length", "avg", "btrim", "ceil", "ceiling",
        "char_length", "coalesce", "concat", "concat_ws", "count",
        "date_trunc", "floor", "greatest", "jsonb_array_length",
        "jsonb_extract_path_text", "jsonb_typeof", "least", "length",
        "lower", "ltrim", "max", "min", "nullif", "replace", "round",
        "rtrim", "st_area", "st_asgeojson", "st_centroid", "st_contains",
        "st_distance", "st_dwithin", "st_envelope", "st_geometrytype",
        "st_intersects", "st_isvalid", "st_length", "st_makeenvelope",
        "st_transform", "st_within", "st_x", "st_y", "string_agg",
        "substring", "sum", "to_char", "trim", "upper",
    }
)

FORBIDDEN_AST_NODES = frozenset(
    {
        "AlterObjectDependsStmt", "AlterRoleStmt", "AlterTableStmt",
        "CallStmt", "ClusterStmt", "CommentStmt", "CompositeTypeStmt",
        "CopyStmt", "CreateFunctionStmt", "CreateRoleStmt", "CreateSchemaStmt",
        "CreateSeqStmt", "CreateStmt", "CreateTableAsStmt", "DeallocateStmt",
        "DeleteStmt", "DiscardStmt", "DoStmt", "DropRoleStmt", "DropStmt",
        "ExecuteStmt", "GrantRoleStmt", "GrantStmt", "IndexStmt", "InsertStmt",
        "ListenStmt", "LoadStmt", "LockStmt", "MergeStmt", "NotifyStmt",
        "PrepareStmt", "ReassignOwnedStmt", "RefreshMatViewStmt", "ReindexStmt",
        "RenameStmt", "RuleStmt", "SecLabelStmt", "TransactionStmt",
        "TruncateStmt", "UnlistenStmt", "UpdateStmt", "VacuumStmt",
        "VariableSetStmt",
    }
)


def _walk(value: Any) -> Iterator[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, dict):
                yield key, child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _string_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                string = item.get("String")
                if isinstance(string, dict) and isinstance(string.get("sval"), str):
                    values.append(string["sval"])
    return values


def validate_readonly_sql(sql: str, *, max_length: int = 20_000) -> str:
    """Validate one read-only PostgreSQL statement and return it unchanged."""

    statement = sql.strip()
    if not statement:
        raise ValueError("La requête SQL est vide")
    if len(statement) > max_length:
        raise ValueError("La requête SQL est trop longue")
    try:
        document = json.loads(parser.parse_sql_json(statement))
    except Exception as exc:
        raise ValueError("La syntaxe PostgreSQL est invalide") from exc

    statements = document.get("stmts")
    if not isinstance(statements, list) or len(statements) != 1:
        raise ValueError("Une seule instruction SQL est autorisée")
    root = statements[0].get("stmt", {})
    if not isinstance(root, dict) or len(root) != 1:
        raise ValueError("Instruction SQL invalide")

    root_type, root_value = next(iter(root.items()))
    if root_type == "ExplainStmt":
        query = root_value.get("query", {}) if isinstance(root_value, dict) else {}
        if not isinstance(query, dict) or set(query) != {"SelectStmt"}:
            raise ValueError("EXPLAIN est limité à une requête SELECT")
    elif root_type != "SelectStmt":
        raise ValueError("Seules les requêtes SELECT ou EXPLAIN SELECT sont autorisées")

    nodes = list(_walk(root))
    forbidden = sorted({node_type for node_type, _ in nodes} & FORBIDDEN_AST_NODES)
    if forbidden:
        raise ValueError(f"Opération SQL interdite : {forbidden[0]}")

    cte_names = {
        str(node.get("ctename", "")).casefold()
        for node_type, node in nodes
        if node_type == "CommonTableExpr" and node.get("ctename")
    }
    relations: set[str] = set()
    for node_type, node in nodes:
        if node_type != "RangeVar":
            continue
        schema = str(node.get("schemaname") or "public").casefold()
        name = str(node.get("relname") or "").casefold()
        if schema not in {"public", ""}:
            raise ValueError(f"Schéma SQL non autorisé : {schema}")
        if name not in cte_names:
            relations.add(name)
    if not relations:
        raise ValueError("La requête doit lire au moins une vue HDP")
    unknown_relations = sorted(relations - ALLOWED_SQL_RELATIONS)
    if unknown_relations:
        raise ValueError(f"Relation SQL non autorisée : {unknown_relations[0]}")

    for node_type, node in nodes:
        if node_type == "SelectStmt":
            if node.get("intoClause"):
                raise ValueError("SELECT INTO est interdit")
            if node.get("lockingClause"):
                raise ValueError("Les verrous SELECT FOR UPDATE/SHARE sont interdits")
        elif node_type == "RangeFunction":
            raise ValueError("Les fonctions utilisées comme relations sont interdites")
        elif node_type == "FuncCall":
            parts = _string_values(node.get("funcname"))
            name = (parts[-1] if parts else "").casefold()
            if name not in ALLOWED_SQL_FUNCTIONS:
                raise ValueError(f"Fonction SQL non autorisée : {name or 'inconnue'}")

    return statement[:-1].rstrip() if statement.endswith(";") else statement
