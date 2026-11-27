from collections import defaultdict
from pathlib import Path
from rdflib import Graph, RDF, RDFS, OWL, SKOS, Namespace

DCT = Namespace("http://purl.org/dc/terms/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
PROV_NS = "http://www.w3.org/ns/prov"
RIM_NAMESPACES = (
    "http://www.opengis.net/ont/rim",
    "http://www.opengis.net/def/metamodel/rim/",
    "urn:oasis:names:tc:ebxml-regrep:xsd:rim",
)

# Relative paths from geosparql-1.1/source/alignments/doc/
ALIGNMENTS_DIR = Path("resources/geosparql-swg/geosparql-1.1/source/alignments/")
OUTPUT_ADOC = Path("resources/geosparql-swg/geosparql-1.1/source/alignments/doc/sections/alignments.adoc")

ALIGNMENT_PREDICATES = (
    OWL.equivalentClass,
    OWL.equivalentProperty,
    RDFS.subClassOf,
    RDFS.subPropertyOf,
    SKOS.exactMatch,
    SKOS.closeMatch,
    SKOS.broadMatch,
    SKOS.narrowMatch,
    SKOS.relatedMatch,
    OWL.sameAs,
    RDFS.seeAlso,
)


def make_anchor(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "-" for ch in text.lower())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")


def get_qname_or_uri(g: Graph, term) -> str:
    try:
        qname = g.namespace_manager.normalizeUri(term)
        if qname and not qname.startswith("<"):
            return qname
    except Exception:
        pass
    return str(term)


def format_term_link(g: Graph, term) -> str:
    if term is None:
        return ""
    text = str(term)
    if text.startswith(("http://", "https://")):
        label = get_qname_or_uri(g, term)
        safe_label = label.replace("]", "\\]").replace("|", "\\|")
        return f"link:{text}[`{safe_label}`]"
    return text.replace("|", "\\|")


def is_excluded_triple(g: Graph, s, p, o) -> bool:
    if p in (RDF.type, OWL.imports, SKOS.definition, RDFS.comment, DCT.description, RDFS.label, SKOS.prefLabel, DCT.title):
        return True
    for term in (s, p, o):
        t_str = str(term)
        if t_str.startswith(PROV_NS) or t_str.startswith(RIM_NAMESPACES):
            return True
        try:
            qname = g.namespace_manager.normalizeUri(term)
            if qname.startswith(("prov", "rim")):
                return True
        except Exception:
            pass
    return False


def get_ontology_title(g: Graph, fallback: str) -> str:
    for onto in g.subjects(RDF.type, OWL.Ontology):
        for pred in (DCT.title, RDFS.label, SKOS.prefLabel):
            val = g.value(onto, pred)
            if val:
                return str(val).strip()
    return fallback


def get_ontology_description(g: Graph) -> str | None:
    for onto in g.subjects(RDF.type, OWL.Ontology):
        for pred in (DCT.description, SKOS.definition, RDFS.comment):
            val = g.value(onto, pred)
            if val:
                return str(val).strip()
    return None


def collect_namespaces(ttl_files: list[Path]) -> dict[str, str]:
    namespaces: dict[str, str] = {}
    excluded_prefixes = {"xml", "xsd", "rdf", "rdfs", "owl", "skos", "dct", "dcterms", "prov", "prov1", "rim"}
    for ttl_path in ttl_files:
        g = Graph()
        g.parse(ttl_path, format="turtle")
        for prefix, ns in g.namespaces():
            if prefix and prefix not in excluded_prefixes and not prefix.startswith(("prov", "rim")):
                namespaces[prefix] = str(ns)
    return dict(sorted(namespaces.items()))


def render_namespaces_table(namespaces: dict[str, str]) -> list[str]:
    if not namespaces:
        return []
    rows = [
        "[[table-alignment-namespaces]]",
        ".Alignment: Namespaces",
        '[cols="1,3",options="header"]',
        "|===",
        "| Prefix | Namespace IRI",
    ]
    for prefix, iri in namespaces.items():
        rows.append(f"| `{prefix}:` | link:{iri}[`{iri}`]")
    rows.append("|===\n")
    return rows


def render_alignment_table(g: Graph, ttl_path: Path, vocab_title: str) -> tuple[list[str], int]:
    # Collect mapping triples where predicate is an alignment predicate or relates GeoSPARQL to external terms
    mappings: list[tuple[object, object, object, str]] = []
    seen = set()

    for s, p, o in sorted(g.triples((None, None, None)), key=lambda t: (str(t[0]), str(t[1]), str(t[2]))):
        if is_excluded_triple(g, s, p, o):
            continue
        if (s, RDF.type, OWL.Ontology) in g:
            continue
        if p not in ALIGNMENT_PREDICATES:
            continue

        key = (str(s), str(p), str(o))
        if key in seen:
            continue
        seen.add(key)

        note_parts = []
        for note_pred in (SKOS.scopeNote, SKOS.note, RDFS.comment, SKOS.definition):
            for val in g.objects(s, note_pred):
                txt = str(val).strip().replace("|", "\\|")
                if txt and txt not in note_parts:
                    note_parts.append(txt)
        note_text = " ".join(note_parts) if note_parts else "—"
        mappings.append((s, p, o, note_text))

    table_id = f"table-alignment-{make_anchor(ttl_path.stem)}"
    rows = [
        f"[[{table_id}]]",
        f".Alignment between GeoSPARQL and {vocab_title}",
        '[cols="2,2,2,3",options="header"]',
        "|===",
        "| Source Term | Alignment Relation | Target Term | Notes",
    ]

    if not mappings:
        rows.append("| _No direct alignment triples found._ | — | — | —")
    else:
        for s, p, o, note in mappings:
            rows.append(
                f"| {format_term_link(g, s)} | {format_term_link(g, p)} | {format_term_link(g, o)} | {note}"
            )

    rows.append("|===\n")
    return rows, len(mappings)


def generate_adoc() -> None:
    ttl_files = sorted(ALIGNMENTS_DIR.glob("*.ttl"))
    if not ttl_files:
        raise FileNotFoundError(f"No .ttl files found in {ALIGNMENTS_DIR.resolve()}")

    OUTPUT_ADOC.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    # Overview & Namespace Prefix Table (modeled after GeoSPARQL 1.1 Annex E.0 / Table E.1)
    namespaces = collect_namespaces(ttl_files)
    lines.append("=== Overview\n")
    lines.append(
        "This document specifies alignments between OGC GeoSPARQL and external spatial and domain vocabularies. "
        "The namespace prefixes used across the alignment mappings are listed in <<table-alignment-namespaces>>.\n"
    )
    lines.extend(render_namespaces_table(namespaces))

    # Per-vocabulary alignment subsections (modeled after GeoSPARQL 1.1 Annex E.1 .. E.n)
    for ttl_path in ttl_files:
        g = Graph()
        g.parse(ttl_path, format="turtle")

        fallback_title = ttl_path.stem.replace("-", " ").replace("_", " ").upper()
        vocab_title = get_ontology_title(g, fallback_title)
        onto_desc = get_ontology_description(g)
        table_id = f"table-alignment-{make_anchor(ttl_path.stem)}"

        table_lines, mapping_count = render_alignment_table(g, ttl_path, vocab_title)

        lines.append(f"=== {vocab_title}\n")
        lines.append(
            f"This section defines {mapping_count} RDF alignment mapping(s) between "
            f"{format_term_link(g, GEO[''])} and {vocab_title} as specified in `{ttl_path.name}`. "
            f"The formal term correspondences are summarized in <<{table_id}>>.\n"
        )

        if onto_desc:
            lines.append(f".RDF Description (`{ttl_path.name}`)")
            lines.append("[NOTE]")
            lines.append("====")
            lines.append(onto_desc)
            lines.append("====\n")

        lines.extend(table_lines)

    OUTPUT_ADOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {OUTPUT_ADOC} from {len(ttl_files)} alignment TTL files.")


if __name__ == "__main__":
    generate_adoc()
