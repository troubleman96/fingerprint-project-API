"""Self-contained API documentation page.

drf-spectacular's default Swagger view loads JavaScript and CSS from a CDN.
That can render a blank page on offline machines or networks that block jsdelivr.
This view keeps /api/docs/ useful without any external assets.
"""
from django.http import HttpResponse


def local_api_docs(request):
    return HttpResponse(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Secure Biometric Disciplinary API</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #172033;
      --muted: #647084;
      --line: #d9dee8;
      --get: #1f7a4f;
      --post: #98630f;
      --put: #2c67b1;
      --patch: #6b4bb8;
      --delete: #b63b3b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.45;
    }
    header {
      background: #172033;
      color: #fff;
      padding: 22px 28px;
    }
    header h1 { margin: 0 0 6px; font-size: 24px; }
    header p { margin: 0; color: #c5cedc; }
    main { max-width: 1180px; margin: 0 auto; padding: 22px; }
    .toolbar {
      display: flex;
      gap: 12px;
      align-items: center;
      margin-bottom: 18px;
    }
    input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 11px 12px;
      font-size: 15px;
      background: #fff;
    }
    a { color: #255da8; }
    .status {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      padding: 16px;
    }
    .endpoint {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      margin-bottom: 10px;
      overflow: hidden;
    }
    .endpoint summary {
      cursor: pointer;
      display: grid;
      grid-template-columns: 92px minmax(180px, 1fr);
      gap: 12px;
      align-items: center;
      padding: 13px 14px;
    }
    .method {
      color: #fff;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 700;
      text-align: center;
      padding: 6px 8px;
      letter-spacing: .02em;
    }
    .GET { background: var(--get); }
    .POST { background: var(--post); }
    .PUT { background: var(--put); }
    .PATCH { background: var(--patch); }
    .DELETE { background: var(--delete); }
    .path { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 14px; }
    .details {
      border-top: 1px solid var(--line);
      padding: 14px;
      color: var(--muted);
    }
    .details h3 { margin: 12px 0 6px; color: var(--text); font-size: 14px; }
    pre {
      white-space: pre-wrap;
      background: #f0f2f6;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      overflow: auto;
      color: #273246;
    }
    .meta { color: var(--muted); font-size: 13px; }
  </style>
</head>
<body>
  <header>
    <h1>Secure Biometric Disciplinary API</h1>
    <p>Local API reference generated from <a href="/api/schema/?format=json">/api/schema/</a></p>
  </header>
  <main>
    <div class="toolbar">
      <input id="search" type="search" placeholder="Search endpoints, methods, tags, descriptions">
    </div>
    <div id="status" class="status">Loading API schema...</div>
    <section id="endpoints"></section>
  </main>
  <script>
    const statusBox = document.getElementById("status");
    const endpointsBox = document.getElementById("endpoints");
    const search = document.getElementById("search");
    let endpointRows = [];

    const methods = ["get", "post", "put", "patch", "delete"];
    const escapeHtml = (value) => String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

    function shortSchema(schema) {
      if (!schema) return "";
      if (schema.$ref) return schema.$ref.replace("#/components/schemas/", "");
      if (schema.type) return schema.type;
      return JSON.stringify(schema, null, 2);
    }

    function render(rows) {
      if (!rows.length) {
        endpointsBox.innerHTML = "";
        statusBox.textContent = "No endpoints match your search.";
        statusBox.style.display = "block";
        return;
      }
      statusBox.style.display = "none";
      endpointsBox.innerHTML = rows.map((row) => {
        const params = row.operation.parameters || [];
        const requestBody = row.operation.requestBody;
        const responses = row.operation.responses || {};
        const description = row.operation.description || "";
        return `<details class="endpoint" data-index="${row.index}">
          <summary>
            <span class="method ${row.method}">${row.method}</span>
            <span>
              <span class="path">${escapeHtml(row.path)}</span>
              <span class="meta"> ${escapeHtml((row.operation.tags || []).join(", "))}</span>
            </span>
          </summary>
          <div class="details">
            ${description ? `<p>${escapeHtml(description)}</p>` : ""}
            ${params.length ? `<h3>Parameters</h3><pre>${escapeHtml(params.map((p) => `${p.in} ${p.name}${p.required ? " required" : ""}`).join("\\n"))}</pre>` : ""}
            ${requestBody ? `<h3>Request Body</h3><pre>${escapeHtml(JSON.stringify(requestBody.content || requestBody, null, 2))}</pre>` : ""}
            <h3>Responses</h3>
            <pre>${escapeHtml(Object.entries(responses).map(([code, value]) => `${code}: ${shortSchema(value.content?.["application/json"]?.schema) || value.description || ""}`).join("\\n"))}</pre>
          </div>
        </details>`;
      }).join("");
    }

    function applyFilter() {
      const term = search.value.trim().toLowerCase();
      if (!term) return render(endpointRows);
      render(endpointRows.filter((row) => row.searchText.includes(term)));
    }

    fetch("/api/schema/?format=json", { headers: { "Accept": "application/json" } })
      .then((response) => {
        if (!response.ok) throw new Error(`Schema request failed with HTTP ${response.status}`);
        return response.json();
      })
      .then((schema) => {
        endpointRows = [];
        Object.entries(schema.paths || {}).forEach(([path, pathItem]) => {
          methods.forEach((method) => {
            if (!pathItem[method]) return;
            const operation = pathItem[method];
            const row = {
              index: endpointRows.length,
              method: method.toUpperCase(),
              path,
              operation,
            };
            row.searchText = `${row.method} ${row.path} ${(operation.tags || []).join(" ")} ${operation.description || ""} ${operation.operationId || ""}`.toLowerCase();
            endpointRows.push(row);
          });
        });
        endpointRows.sort((a, b) => `${a.path} ${a.method}`.localeCompare(`${b.path} ${b.method}`));
        render(endpointRows);
      })
      .catch((error) => {
        statusBox.innerHTML = `<strong>Could not load /api/schema/.</strong><br>${escapeHtml(error.message)}<br><br>Open <a href="/api/schema/?format=json">/api/schema/?format=json</a> directly to inspect the raw schema.`;
      });

    search.addEventListener("input", applyFilter);
  </script>
</body>
</html>""",
        content_type="text/html",
    )
