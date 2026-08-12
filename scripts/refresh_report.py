#!/usr/bin/env python3
"""
Refresca el Reporte Ejecutivo BUPA con datos en vivo desde la API de Monday.com.

Lee el tablero BUPA (id 9801038662) directo desde la API GraphQL de Monday
(no depende de Cowork), toma template.html, incrusta los datos y produce
index.html en la raiz del repo, listo para servir con GitHub Pages.

Requiere la variable de entorno MONDAY_API_TOKEN (token de API personal o de
la app, generado en Monday: Avatar -> Admin -> API, o Perfil -> Developers).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

MONDAY_API_URL = "https://api.monday.com/v2"
BOARD_ID = 9801038662
COLUMN_IDS = [
    "status",
    "text_mkvsgz7c",
    "color_mkvmmqp8",
    "color_mkvg9a3z",
    "person",
    "numeric_mkvmfwxv",
    "text_mkttdvpm",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
TEMPLATE_PATH = os.path.join(REPO_ROOT, "template.html")
OUTPUT_PATH = os.path.join(REPO_ROOT, "index.html")


def graphql(query, token, retries=3):
    payload = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        MONDAY_API_URL,
        data=payload,
        headers={
            "Authorization": token,
            "Content-Type": "application/json",
            "API-Version": "2024-10",
        },
        method="POST",
    )
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            if "errors" in body:
                raise RuntimeError(f"Monday API error: {json.dumps(body['errors'])}")
            return body["data"]
        except (urllib.error.URLError, RuntimeError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(2 * attempt)
            else:
                raise
    raise last_err


def fetch_all_items(token):
    cols = ", ".join(f'"{c}"' for c in COLUMN_IDS)
    first_query = f"""
    query {{
      boards(ids: [{BOARD_ID}]) {{
        items_page(limit: 500) {{
          cursor
          items {{
            id
            name
            group {{ id title }}
            column_values(ids: [{cols}]) {{ id text }}
          }}
        }}
      }}
    }}
    """
    data = graphql(first_query, token)
    boards = data.get("boards") or []
    if not boards:
        raise RuntimeError(f"Board {BOARD_ID} no encontrado o sin acceso con este token")
    page = boards[0]["items_page"]
    items = list(page["items"])
    cursor = page["cursor"]

    while cursor:
        next_query = f"""
        query {{
          next_items_page(cursor: "{cursor}", limit: 500) {{
            cursor
            items {{
              id
              name
              group {{ id title }}
              column_values(ids: [{cols}]) {{ id text }}
            }}
          }}
        }}
        """
        data = graphql(next_query, token)
        page = data["next_items_page"]
        items.extend(page["items"])
        cursor = page["cursor"]
        time.sleep(0.3)

    return items


def transform(raw_items):
    out = []
    for it in raw_items:
        cv = {c["id"]: c["text"] for c in (it.get("column_values") or [])}
        out.append(
            {
                "id": it["id"],
                "name": it["name"],
                "group": it.get("group"),
                "column_values": cv,
            }
        )
    return out


def main():
    token = os.environ.get("MONDAY_API_TOKEN")
    if not token:
        print("ERROR: falta la variable de entorno MONDAY_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    print(f"Consultando tablero BUPA ({BOARD_ID})...")
    raw_items = fetch_all_items(token)
    items = transform(raw_items)
    print(f"Obtenidos {len(items)} items.")

    if not os.path.exists(TEMPLATE_PATH):
        print(f"ERROR: no se encontro template.html en {TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    items_json = json.dumps(items, ensure_ascii=False)
    items_json_safe = items_json.replace("</script", "<\\/script").replace("<!--", "<\\!--")
    generated_at_iso = datetime.now(timezone.utc).isoformat()

    if "__STATIC_ITEMS_JSON__" not in html or "__GENERATED_AT_ISO__" not in html:
        print("ERROR: template.html no contiene los marcadores esperados", file=sys.stderr)
        sys.exit(1)

    html = html.replace("__STATIC_ITEMS_JSON__", items_json_safe)
    html = html.replace("__GENERATED_AT_ISO__", generated_at_iso)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"OK: index.html actualizado con {len(items)} items (generado {generated_at_iso})")


if __name__ == "__main__":
    main()
