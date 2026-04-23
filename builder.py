import os
import urllib.request
import base64

# Configuration
PYODIDE_VERSION = "v0.23.4"
BASE_URL = f"https://cdn.jsdelivr.net/pyodide/{PYODIDE_VERSION}/full/"
# Core files needed
FILES = ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip"]

def get_base64(url):
    print(f"[*] Fetching and encoding: {url}")
    response = urllib.request.urlopen(url)
    return base64.b64encode(response.read()).decode('utf-8')

def package_single_file():
    # 1. Download and Encode all parts
    encoded_files = {}
    for f in FILES:
        encoded_files[f] = get_base64(BASE_URL + f)

    # 2. Build the "All-in-One" HTML
    # We use a Blob strategy to trick the browser into thinking these are real files
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Portable Python (Offline)</title>
    <style>
        body {{ font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }}
        #console {{ background: #000; padding: 15px; border-radius: 5px; height: 150px; overflow-y: auto; color: #9cdcfe; border: 1px solid #333; }}
        textarea {{ width: 100%; background: #252526; color: #fff; border: 1px solid #333; padding: 10px; margin-top: 10px; border-radius: 5px; font-family: monospace; }}
        button {{ background: #007acc; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 3px; margin-top: 10px; }}
        button:hover {{ background: #0062a3; }}
    </style>
</head>
<body>
    <h3>Portable Python Console</h3>
    <div id="console">Initializing Virtual Filesystem...</div>
    <textarea id="input" rows="8">import math\nprint(f"Pi is {{math.pi}}")\n\nfor i in range(3):\n    print(f"Offline execution #{{i+1}}")</textarea>
    <button id="runBtn" disabled onclick="runCode()">Booting...</button>

    <script>
        const encodedData = {{
            "pyodide.js": "{encoded_files['pyodide.js']}",
            "asm_js": "{encoded_files['pyodide.asm.js']}",
            "asm_wasm": "{encoded_files['pyodide.asm.wasm']}",
            "stdlib": "{encoded_files['python_stdlib.zip']}"
        }};

        function base64ToBlob(b64, type) {{
            const bin = atob(b64);
            const array = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) array[i] = bin.charCodeAt(i);
            return new Blob([array], {{ type: type }});
        }}

        async function init() {{
            const consoleDiv = document.getElementById('console');
            
            // Create virtual URLs for the embedded blobs
            const pyodideJsUrl = URL.createObjectURL(base64ToBlob(encodedData["pyodide.js"], "text/javascript"));
            const wasmUrl = URL.createObjectURL(base64ToBlob(encodedData["asm_wasm"], "application/wasm"));
            const stdlibUrl = URL.createObjectURL(base64ToBlob(encodedData["stdlib"], "application/zip"));

            // Inject the loader script
            const script = document.createElement('script');
            script.src = pyodideJsUrl;
            script.onload = async () => {{
                try {{
                    window.pyodide = await loadPyodide({{
                        indexURL: "./", // Irrelevant but required
                        // We override the internal fetch to serve our blobs
                        _getBinary: () => base64ToBlob(encodedData["asm_wasm"], "application/wasm")
                    }});

                    // Manually load the standard library from our blob
                    await pyodide.unpackArchive(await base64ToBlob(encodedData["stdlib"], "application/zip").arrayBuffer(), "zip");
                    
                    document.getElementById('runBtn').disabled = false;
                    document.getElementById('runBtn').innerText = "Run Python";
                    consoleDiv.innerText = "Ready. All systems internal.\\n";
                }} catch (e) {{
                    consoleDiv.innerText = "Boot Error: " + e;
                }}
            }};
            document.head.appendChild(script);
        }}

        async function runCode() {{
            const code = document.getElementById('input').value;
            const consoleDiv = document.getElementById('console');
            try {{
                pyodide.runPython("import sys, io; sys.stdout = io.StringIO()");
                await pyodide.runPythonAsync(code);
                const out = pyodide.runPython("sys.stdout.getvalue()");
                consoleDiv.innerText += "> " + out + "\\n";
            }} catch (err) {{
                consoleDiv.innerText += "Error: " + err + "\\n";
            }}
        }}

        init();
    </script>
</body>
</html>
"""
    with open("python_offline.html", "w") as f:
        f.write(html_template)
    print("\n[!] SUCCESS: Single-file HTML created: python_offline.html")

if __name__ == "__main__":
    package_single_file()