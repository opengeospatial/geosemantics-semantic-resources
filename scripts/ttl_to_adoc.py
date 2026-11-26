import os
import glob
import urllib.request
import json
from rdflib import Graph, RDF, RDFS, OWL, SKOS, Namespace

SH = Namespace("http://w3.org")
DCT = Namespace("http://purl.org")

REPO_API_URL = (
    "https://github.com"
    "geosemantics-semantic-resources/contents/"
    "resources/geosparql-swg/geosparql-geometry-datatypes/resources"
)
LOCAL_TTL_DIR = "build/ttl"
OUTPUT_ADOC = "build/datatypes.adoc"


def fetch_ttl_files():
    os.makedirs(LOCAL_TTL_DIR, exist_ok=True)
    req = urllib.request.Request(
        REPO_API_URL, headers={"User-Agent": "OGC-Metanorma-Builder"}
    )
    with urllib.request.urlopen(req) as resp:
        items = json.loads(resp.read().decode("utf-8"))

    ttl_paths = []
    for item in items:
        if item["name"].endswith(".ttl") and item.get("download_url"):
            dest = os.path.join(LOCAL_TTL_DIR, item["name"])
            urllib.request.urlretrieve(item["download_url"], dest)
            ttl_paths.append(dest)
    return sorted(ttl_paths)


def format_term(g: Graph, term) -> str:
    if term is None:
        return ""
    qname = None
    try:
        qname = g.namespace_manager.normalizeUri(term)
    except Exception:
        pass
    text = str(term)
    if text.startswith("http://") or text.startswith("https://"):
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


def generate_adoc(ttl_files):
    os.makedirs(os.path.dirname(OUTPUT_ADOC), exist_ok=True)
    lines = []

    for ttl_path in ttl_files:
        g = Graph()
        g.parse(ttl_path, format="turtle")
        file_stem = os.path.splitext(os.path.basename(ttl_path))[0].upper()

        # Find Datatypes (fallback to RDFS/OWL classes if no rdfs:Datatype is explicitly typed)
        datatypes = sorted(
            set(g.subjects(RDF.type, RDFS.Datatype)), key=lambda s: str(s)
        )
        if not datatypes:
            datatypes = sorted(
                set(g.subjects(RDF.type, OWL.Class))
                | set(g.subjects(RDF.type, RDFS.Class)),
                key=lambda s: str(s),
            )

        # Find Properties in the file
        prop_types = (
            RDF.Property,
            OWL.DatatypeProperty,
            OWL.ObjectProperty,
            OWL.AnnotationProperty,
        )
        properties = set()
        for pt in prop_types:
            properties.update(g.subjects(RDF.type, pt))

        lines.append(f"=== {file_stem} Datatype Specification\n")

        for dt in datatypes:
            dt_label = get_label(g, dt)
            dt_desc = get_description(g, dt)

            lines.append(f"==== {dt_label}\n")
            lines.append(f"{dt_desc}\n")

            # Table of all attributes/predicates describing this datatype
            lines.append("[cols=\"1,3\",options=\"header\"]")
            lines.append("|===")
            lines.append("| Attribute | Value")
            lines.append(f"| URI | `{dt}`")

            for p, o in sorted(g.predicate_objects(dt), key=lambda x: str(x[0])):
                if p in (SKOS.definition, RDFS.comment, DCT.description):
                    continue
                lines.append(f"| {format_term(g, p)} | {format_term(g, o)}")
            lines.append("|===\n")

        # Accompanying properties section
        if properties:
            lines.append(f"==== Accompanying Properties ({file_stem})\n")
            for prop in sorted(properties, key=lambda s: str(s)):
                prop_label = get_label(g, prop)
                prop_desc = get_description(g, prop)

                lines.append(f"===== {prop_label}\n")
                lines.append(f"{prop_desc}\n")
                lines.append("[cols=\"1,3\",options=\"header\"]")
                lines.append("|===")
                lines.append("| Property Attribute | Value")
                lines.append(f"| URI | `{prop}`")

                for p, o in sorted(g.predicate_objects(prop), key=lambda x: str(x[0])):
                    if p in (SKOS.definition, RDFS.comment, DCT.description):
                        continue
                    lines.append(f"| {format_term(g, p)} | {format_term(g, o)}")
                lines.append("|===\n")

    with open(OUTPUT_ADOC, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    files = fetch_ttl_files()
    generate_adoc(files)
    print(f"Generated {OUTPUT_ADOC} from {len(files)} TTL files.")
