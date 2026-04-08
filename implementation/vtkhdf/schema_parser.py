"""
schema_parser.py
ON-DEM WG3 - Schema Parser

Reads the ON-DEM Python schema files and builds a structured in-memory
representation of all classes, fields, types, and docstrings.

Usage:
    from schema_parser import parse_schema_dir
    schema = parse_schema_dir("/path/to/schema/")
"""

import ast
import os
import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class FieldDef:
    """One field (class-level annotated attribute) from a schema class."""
    name: str
    type_str: str           # raw type string, e.g. "float", "Vector3", "int"
    default: str            # raw default value as string, e.g. "None", "0.0"
    docstring: str          # the string literal immediately following the field
    mandatory: bool         # True if docstring contains [mandatory]
    optional: bool          # True if docstring contains [optional]
    units: str              # extracted unit string, e.g. "[L]", "[M T^{-1}]"
    hdf5_type: str          # inferred HDF5 type: "scalar_float", "scalar_int",
                            # "scalar_bool", "vector3", "quaternion", "matrix3",
                            # "string", "string_list", "unknown"
    hdf5_shape: str         # "scalar", "(N,)", "(N,3)", "(N,4)", "(N,9)"


@dataclass
class ClassDef:
    """One class from a schema file."""
    name: str
    module: str             # which file it came from (without .py)
    docstring: str
    bases: list             # list of base class name strings
    fields: list            # list of FieldDef (own fields only, not inherited)
    all_fields: list        # flattened including inherited (filled by resolver)
    is_abstract: bool       # True for Some*Class / abstract marker classes


@dataclass
class Schema:
    """Complete parsed schema."""
    classes: dict           # name -> ClassDef
    modules: dict           # module name -> list of class names


# ---------------------------------------------------------------------------
# Type inference
# ---------------------------------------------------------------------------

_TYPE_MAP = {
    "float":      ("scalar_float", "scalar"),
    "int":        ("scalar_int",   "scalar"),
    "bool":       ("scalar_bool",  "scalar"),
    "str":        ("string",       "scalar"),
    "Vector3":    ("vector3",      "(N,3)"),
    "Quaternion": ("quaternion",   "(N,4)"),
    "Matrix3":    ("matrix3",      "(N,9)"),
    "list":       ("string_list",  "(N,)"),
    "List[str]":  ("string_list",  "(N,)"),
}

def _infer_hdf5(type_str: str):
    t = type_str.strip()
    if t in _TYPE_MAP:
        return _TYPE_MAP[t]
    # List[X] variants
    if t.startswith("List["):
        return ("string_list", "(N,)")
    return ("unknown", "unknown")


# ---------------------------------------------------------------------------
# Unit extraction from docstring
# ---------------------------------------------------------------------------

_UNIT_RE = re.compile(r'\[([^\[\]]+)\]')

def _extract_units(doc: str) -> str:
    """Return the last [...] group in a docstring as units, or ''."""
    matches = _UNIT_RE.findall(doc)
    # skip [mandatory], [optional], [-]
    skip = {"mandatory", "optional", "-"}
    for m in reversed(matches):
        if m.strip() not in skip:
            return f"[{m}]"
    return ""


# ---------------------------------------------------------------------------
# AST-based parser for a single file
# ---------------------------------------------------------------------------

def _parse_file(filepath: str, module_name: str) -> dict:
    """Parse one schema .py file. Returns dict of ClassDef."""
    with open(filepath, "r") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"[schema_parser] SyntaxError in {filepath}: {e}")
        return {}

    classes = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        # Class docstring
        cls_doc = ast.get_docstring(node) or ""

        # Base classes
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(f"{b.value.id}.{b.attr}")

        # Abstract marker
        is_abstract = (
            "abstract" in cls_doc.lower() or
            node.name.startswith("Some") or
            node.name.startswith("some_")
        )

        # Fields: annotated assignments at class body level
        fields = []
        body = node.body

        # We need to look at consecutive pairs: AnnAssign followed by Expr(Constant)
        i = 0
        while i < len(body):
            stmt = body[i]
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                fname = stmt.target.id

                # Type annotation
                ftype = ast.unparse(stmt.annotation) if stmt.annotation else "unknown"

                # Default value
                fdefault = ast.unparse(stmt.value) if stmt.value else "None"

                # Look ahead for docstring
                fdoc = ""
                if i + 1 < len(body):
                    nxt = body[i + 1]
                    if (isinstance(nxt, ast.Expr) and
                            isinstance(nxt.value, (ast.Constant, ast.Str))):
                        fdoc = nxt.value.s if isinstance(nxt.value, ast.Constant) else nxt.value.s

                mandatory = "**[mandatory]**" in fdoc or "[mandatory]" in fdoc
                optional  = "*[optional]*"   in fdoc or "[optional]"  in fdoc
                units     = _extract_units(fdoc)
                hdf5_type, hdf5_shape = _infer_hdf5(ftype)

                fields.append(FieldDef(
                    name=fname,
                    type_str=ftype,
                    default=fdefault,
                    docstring=fdoc,
                    mandatory=mandatory,
                    optional=optional,
                    units=units,
                    hdf5_type=hdf5_type,
                    hdf5_shape=hdf5_shape,
                ))
            i += 1

        classes[node.name] = ClassDef(
            name=node.name,
            module=module_name,
            docstring=cls_doc,
            bases=bases,
            fields=fields,
            all_fields=[],      # filled by resolver
            is_abstract=is_abstract,
        )

    return classes


# ---------------------------------------------------------------------------
# Inheritance resolver
# ---------------------------------------------------------------------------

def _resolve_inheritance(classes: dict):
    """Fill all_fields for each class using MRO-like resolution."""

    def get_all_fields(cls_name, visited=None):
        if visited is None:
            visited = set()
        if cls_name in visited or cls_name not in classes:
            return []
        visited.add(cls_name)
        cls = classes[cls_name]
        inherited = []
        for base in cls.bases:
            inherited.extend(get_all_fields(base, visited))
        # own fields override inherited
        own_names = {f.name for f in cls.fields}
        merged = [f for f in inherited if f.name not in own_names]
        merged.extend(cls.fields)
        return merged

    for name, cls in classes.items():
        cls.all_fields = get_all_fields(name)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Files to skip (not schema definitions)
_SKIP_FILES = {"base_types.py", "model.py"}

def parse_schema_dir(schema_dir: str) -> Schema:
    """Parse all schema .py files in a directory.

    Parameters
    ----------
    schema_dir : str
        Path to directory containing the ON-DEM schema .py files.

    Returns
    -------
    Schema
        Structured representation of all classes and fields.
    """
    all_classes = {}
    modules = {}

    py_files = sorted([
        f for f in os.listdir(schema_dir)
        if f.endswith(".py") and f not in _SKIP_FILES
    ])

    for fname in py_files:
        module_name = fname.replace(".py", "")
        fpath = os.path.join(schema_dir, fname)
        file_classes = _parse_file(fpath, module_name)
        all_classes.update(file_classes)
        modules[module_name] = list(file_classes.keys())
        print(f"[schema_parser] Parsed {fname}: {list(file_classes.keys())}")

    _resolve_inheritance(all_classes)

    return Schema(classes=all_classes, modules=modules)


def print_schema_summary(schema: Schema):
    """Print a human-readable summary of the parsed schema."""
    print("\n=== ON-DEM Schema Summary ===")
    for mod, class_names in schema.modules.items():
        print(f"\n  [{mod}]")
        for cname in class_names:
            cls = schema.classes[cname]
            bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
            print(f"    {cname}{bases_str}  {'[abstract]' if cls.is_abstract else ''}")
            for f in cls.fields:
                tag = "M" if f.mandatory else ("O" if f.optional else "?")
                print(f"      [{tag}] {f.name}: {f.type_str} "
                      f"→ hdf5={f.hdf5_type}/{f.hdf5_shape} {f.units}")


if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    schema = parse_schema_dir(d)
    print_schema_summary(schema)
