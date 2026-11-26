from collections import defaultdict
from pathlib import Path
from rdflib import Graph, RDF, RDFS, OWL, SKOS, Namespace

DCT = Namespace("http://purl.org/dc/terms/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
PROV_NS = "http://www.w3.org/ns/prov#"
EXCLUDED_URI_PREFIXES = (
    "http://www.w3.org/ns/prov",
    "http://www.opengis.net/ont/rim",
    "http://www.opengis.net/def/metamodel/rim",
    "urn:oasis:names:tc:ebxml-regrep:xsd:rim",
)
EXCLUDED_QNAME_PREFIXES = ("prov", "rim")

TTL_DIR = Path("resources/geosparql-swg/geosparql-geometry-datatypes/resources/")
OUTPUT_ADOC = Path("resources/geosparql-swg/geosparql-geometry-datatypes/doc/sections/datatypes.adoc")

def get_qname_or_uri(g: Graph, term) -> str:
    try:
        qname = g.namespace_manager.normalizeUri(term)
        if qname and not qname.startswith("<"):
            return qname
    except Exception:
        pass
    return str(term)


def format_term(g: Graph, term) -> str:
    if term is None:
        return ""
    text = str(term)
    if text.startswith(("http://", "https://")):
        label = get_qname_or_uri(g, term)
        safe_label = label.replace("]", "\\]").replace("|", "\\|")
        return f"link:{text}[`{safe_label}`]"
    return text.replace("|", "\\|")


def format_code_block(term) -> str:
    code = str(term).strip()
    return f"[source,turtle]\n----\n{code}\n----"


def is_excluded_predicate(g: Graph, pred) -> bool:
    if pred in (RDF.type, SKOS.definition, RDFS.comment, DCT.description):
        return True
    pred_str = str(pred)
    if pred_str.startswith(EXCLUDED_URI_PREFIXES):
        return True
    try:
        qname = g.namespace_manager.normalizeUri(pred)
        if not qname.startswith("<") and ":" in qname:
            prefix = qname.split(":", 1)[0].lower()
            if prefix.startswith(EXCLUDED_QNAME_PREFIXES):
                return True
    except Exception:
        pass
    return False


def get_label(g: Graph, subject) -> str:
    for pred in (RDFS.label, SKOS.prefLabel, DCT.title):
        val = g.value(subject, pred)
        if val:
            return str(val)
    qname = get_qname_or_uri(g, subject)
    if qname != str(subject):
        return qname
    return str(subject).split("/")[-1].split("#")[-1]


def get_description(g: Graph, subject) -> str | None:
    for pred in (SKOS.definition, RDFS.comment, DCT.description):
        val = g.value(subject, pred)
        if val:
            return str(val).strip()
    return None


def build_section_intro(
    g: Graph, format_name: str, filename: str, datatypes: list, properties: list
) -> str:
    dt_names = ", ".join(f"`{get_qname_or_uri(g, dt)}`" for dt in datatypes) or "none"
    dt_word = "datatype" if len(datatypes) == 1 else "datatypes"
    prop_count = len(properties)
    prop_phrase = (
        f"and {prop_count} accompanying serialization "
        f"{'property' if prop_count == 1 else 'properties'}"
        if prop_count
        else "with no accompanying serialization properties"
    )
    return (
        f"This section specifies the {format_name} geometry literal {dt_word} "
        f"({dt_names}) {prop_phrase} defined in `{filename}` for representing "
        f"{format_name} geometries in RDF."
    )


def build_datatype_intro(g: Graph, dt, format_name: str) -> str:
    dt_qname = get_qname_or_uri(g, dt)
    supported = sorted(
        {get_qname_or_uri(g, o) for o in g.objects(dt, GEO.supportsGeometryType)}
    )
    if supported:
        formatted = ", ".join(f"`{s}`" for s in supported[:4])
        suffix = ", among others" if len(supported) > 4 else ""
        support_clause = f", supporting geometry types such as {formatted}{suffix}"
    else:
        support_clause = ""
    return (
        f"The `{dt_qname}` datatype represents geometry literals serialized in the "
        f"{format_name} format{support_clause}. Its canonical IRI, metadata "
        f"attributes, and usage examples are detailed below."
    )


def build_property_intro(g: Graph, prop) -> str:
    prop_qname = get_qname_or_uri(g, prop)
    domain = g.value(prop, RDFS.domain)
    range_ = g.value(prop, RDFS.range)
    subprop = g.value(prop, RDFS.subPropertyOf)

    domain_str = (
        f"`{get_qname_or_uri(g, domain)}`" if domain else "spatial feature or geometry"
    )
    range_str = (
        f"`{get_qname_or_uri(g, range_)}`"
        if range_
        else "the corresponding geometry datatype"
    )
    subprop_clause = (
        f" as a subproperty of `{get_qname_or_uri(g, subprop)}`" if subprop else ""
    )
    return (
        f"The `{prop_qname}` property associates {domain_str} resources with "
        f"geometry literals typed as {range_str}{subprop_clause}."
    )


def render_attribute_table(g: Graph, subject, header_label: str) -> list[str]:
    grouped: dict[object, list[str]] = defaultdict(list)

    for p, o in sorted(g.predicate_objects(subject), key=lambda x: str(x)):
        if is_excluded_predicate(g, p):
            continue
        formatted_val = (
            format_code_block(o) if p == SKOS.example else format_term(g, o)
        )
        if formatted_val not in grouped[p]:
            grouped[p].append(formatted_val)

    rows = [
        '[cols="1,3",options="header"]',
        "|===",
        f"| {header_label} | Value",
        f"| URI | link:{subject}[`{subject}`]",
    ]

    for p in sorted(grouped.keys(), key=lambda x: str(x)):
        pred_cell = format_term(g, p)
        values = grouped[p]
        if p == SKOS.example:
            blocks = "\n\n".join(values)
            rows.append(f"| {pred_cell} a|\n{blocks}")
        elif len(values) == 1:
            rows.append(f"| {pred_cell} | {values[0]}")
        else:
            bullets = "\n".join(f"* {val}" for val in values)
            rows.append(f"| {pred_cell} a|\n{bullets}")

    rows.append("|===\n")
    return rows


def generate_adoc() -> None:
    ttl_files = sorted(TTL_DIR.glob("*.ttl"))
    if not ttl_files:
        raise FileNotFoundError(f"No .ttl files found in {TTL_DIR.resolve()}")

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
        properties_set = set()
        for pt in prop_types:
            properties_set.update(g.subjects(RDF.type, pt))
        properties = sorted(properties_set, key=lambda s: str(s))

        lines.append(f"=== {format_name} Datatype Specification\n")
        lines.append(
            f"{build_section_intro(g, format_name, ttl_path.name, datatypes, properties)}\n"
        )

        for dt in datatypes:
            lines.append(f"==== {get_label(g, dt)}\n")
            lines.append(f"{build_datatype_intro(g, dt, format_name)}\n")
            desc = get_description(g, dt)
            if desc:
                lines.append(f"{desc}\n")
            lines.extend(render_attribute_table(g, dt, "Attribute"))

        if properties:
            lines.append(f"==== Accompanying Properties ({format_name})\n")
            for prop in properties:
                lines.append(f"===== {get_label(g, prop)}\n")
                lines.append(f"{build_property_intro(g, prop)}\n")
                desc = get_description(g, prop)
                if desc:
                    lines.append(f"{desc}\n")
                lines.extend(render_attribute_table(g, prop, "Property Attribute"))

    OUTPUT_ADOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {OUTPUT_ADOC} from {len(ttl_files)} local TTL files.")


if __name__ == "__main__":
    generate_adoc()