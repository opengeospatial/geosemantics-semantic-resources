from pathlib import Path
from rdflib import Graph, RDF, RDFS, OWL, SKOS, Namespace

DCT = Namespace("http://purl.org/dc/terms/")

TTL_DIR = Path("resources/geosparql-swg/geosparql-geometry-datatypes/resources/")
OUTPUT_ADOC = Path("resources/geosparql-swg/geosparql-geometry-datatypes/doc/sections/datatypes.adoc")

def format_term(g: Graph, term) -> str:
    if term is None:
        return ""
    qname = None
    try:
        qname = g.namespace_manager.normalizeUri(term)
    except Exception:
        pass
    text = str(term)
    if text.startswith(("http://", "https://")):
        label = qname if qname and not qname.startswith("<") else text
        return f"`{label}` ({text})"
    return text.replace("|", "\\|")


def get_label(g: Graph, subject) -> str:
    for pred in (RDFS.label, SKOS.prefLabel, DCT.title):
        val = g.value(subject, pred)
        if val:
            return str(val)
    try:
        return g.namespace_manager.normalizeUri(subject)
    except Exception:
        return str(subject).split("/")[-1].split("#")[-1]


def get_description(g: Graph, subject) -> str:
    for pred in (SKOS.definition, RDFS.comment, DCT.description):
        val = g.value(subject, pred)
        if val:
            return str(val).strip()
    return "_No description provided._"


def render_attribute_table(g: Graph, subject, header_label: str) -> list[str]:
    rows = [
        '[cols="1,3",options="header"]',
        "|===",
        f"| {header_label} | Value",
        f"| URI | `{subject}`",
    ]
    for p, o in sorted(g.predicate_objects(subject), key=lambda x: str(x)):
        if p in (SKOS.definition, RDFS.comment, DCT.description):
            continue
        rows.append(f"| {format_term(g, p)} | {format_term(g, o)}")
    rows.append("|===\n")
    return rows


def generate_adoc() -> None:
    ttl_files = sorted(TTL_DIR.glob("*.ttl"))
    if not ttl_files:
        raise FileNotFoundError(f"No .ttl files found in {TTL_DIR}")

    OUTPUT_ADOC.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    for ttl_path in ttl_files:
        g = Graph()
        g.parse(ttl_path, format="turtle")
        format_name = ttl_path.stem.upper()

        datatypes = sorted(
            set(g.subjects(RDF.type, RDFS.Datatype)), key=lambda s: str(s)
        )
        if not datatypes:
            datatypes = sorted(
                set(g.subjects(RDF.type, OWL.Class))
                | set(g.subjects(RDF.type, RDFS.Class)),
                key=lambda s: str(s),
            )

        prop_types = (
            RDF.Property,
            OWL.DatatypeProperty,
            OWL.ObjectProperty,
            OWL.AnnotationProperty,
        )
        properties = set()
        for pt in prop_types:
            properties.update(g.subjects(RDF.type, pt))

        lines.append(f"=== {format_name} Datatype Specification\n")

        for dt in datatypes:
            lines.append(f"==== {get_label(g, dt)}\n")
            lines.append(f"{get_description(g, dt)}\n")
            lines.extend(render_attribute_table(g, dt, "Attribute"))

        if properties:
            lines.append(f"==== Accompanying Properties ({format_name})\n")
            for prop in sorted(properties, key=lambda s: str(s)):
                lines.append(f"===== {get_label(g, prop)}\n")
                lines.append(f"{get_description(g, prop)}\n")
                lines.extend(render_attribute_table(g, prop, "Property Attribute"))

    OUTPUT_ADOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {OUTPUT_ADOC} from {len(ttl_files)} local TTL files.")


if __name__ == "__main__":
    generate_adoc()
