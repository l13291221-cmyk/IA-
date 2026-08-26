"""Salvataggio dello STATO su GitHub: il bot "si salva da solo".

Su un host gratuito (es. Render) il disco è "usa e getta": a un riavvio o a un
nuovo deploy lo stato locale può sparire. Con questo modulo il bot scrive da solo
il proprio stato su GitHub (un ramo dedicato del repo) e se lo ricarica all'avvio,
così i movimenti e lo storico NON si perdono anche se l'host riparte da zero.

Regole di sicurezza:
- Usa SOLO la libreria standard (urllib): nessuna dipendenza.
- Si attiva SOLO se sono presenti le variabili d'ambiente; altrimenti non fa nulla
  e resta il normale salvataggio locale su file.
- NON salva mai le chiavi API. Qui va solo lo stato dei bot (movimenti, equity,
  cimitero, contatori) che non contiene segreti. Le chiavi restano in config.json,
  che non viene mai toccato da qui.

Variabili d'ambiente:
  STATE_GITHUB_TOKEN   token GitHub con permesso di scrittura sui *contenuti* del repo
                       (meglio un token "fine-grained" limitato a QUEL repo, solo
                       Contents: Read and write — niente altro).
  STATE_GITHUB_REPO    "utente/repo" dove salvare lo stato.
  STATE_GITHUB_BRANCH  ramo dedicato allo stato (default "agentcolony-state").
                       ⚠️ DEVE essere DIVERSO dal ramo di deploy, altrimenti ogni
                       salvataggio farebbe ripartire il deploy su Render (loop).
  STATE_GITHUB_PATH    nome del file (default "state.json").
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request

_API = "https://api.github.com"
_sha = {"v": None}   # sha dell'ultimo file salvato, per aggiornarlo al posto giusto


def _cfg():
    return (
        os.environ.get("STATE_GITHUB_TOKEN", ""),
        os.environ.get("STATE_GITHUB_REPO", ""),
        os.environ.get("STATE_GITHUB_BRANCH", "") or "agentcolony-state",
        os.environ.get("STATE_GITHUB_PATH", "") or "state.json",
    )


def enabled() -> bool:
    tok, repo, _, _ = _cfg()
    return bool(tok and repo)


def _req(method: str, url: str, token: str, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header("Authorization", f"Bearer {token}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "AgentColony")
    if body is not None:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=25) as resp:
        raw = resp.read()
        return resp.status, (json.loads(raw) if raw else {})


def load():
    """Ritorna lo stato salvato su GitHub (dict) o None se non c'è / non attivo."""
    if not enabled():
        return None
    tok, repo, branch, path = _cfg()
    url = f"{_API}/repos/{repo}/contents/{path}?ref={branch}"
    try:
        status, j = _req("GET", url, tok)
        if status == 200 and j.get("content"):
            _sha["v"] = j.get("sha")
            return json.loads(base64.b64decode(j["content"]))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None   # non ancora salvato: normale al primo avvio
    except Exception:
        return None
    return None


def _ensure_branch(tok: str, repo: str, branch: str) -> None:
    """Crea il ramo dedicato (dal ramo di default) se non esiste ancora."""
    try:
        _req("GET", f"{_API}/repos/{repo}/branches/{branch}", tok)
        return   # esiste già
    except urllib.error.HTTPError as e:
        if e.code != 404:
            return
    except Exception:
        return
    try:
        _, info = _req("GET", f"{_API}/repos/{repo}", tok)
        default = info.get("default_branch", "main")
        _, ref = _req("GET", f"{_API}/repos/{repo}/git/ref/heads/{default}", tok)
        sha = ref["object"]["sha"]
        _req("POST", f"{_API}/repos/{repo}/git/refs", tok,
             {"ref": f"refs/heads/{branch}", "sha": sha})
    except Exception:
        pass


def _put(state: dict) -> bool:
    tok, repo, branch, path = _cfg()
    content = base64.b64encode(json.dumps(state).encode()).decode()
    data = {"message": "agentcolony: salvataggio automatico dello stato",
            "content": content, "branch": branch}
    if _sha["v"]:
        data["sha"] = _sha["v"]
    status, j = _req("PUT", f"{_API}/repos/{repo}/contents/{path}", tok, data)
    if status in (200, 201):
        _sha["v"] = (j.get("content") or {}).get("sha")
        return True
    return False


def save(state: dict) -> bool:
    """Salva lo stato su GitHub (ramo dedicato). True se riuscito."""
    if not enabled():
        return False
    tok, repo, branch, _ = _cfg()
    try:
        _ensure_branch(tok, repo, branch)
        return _put(state)
    except urllib.error.HTTPError as e:
        # sha non aggiornato (qualcuno ha scritto nel frattempo): rileggo e riprovo una volta
        if e.code in (409, 422):
            try:
                load()          # aggiorna _sha["v"]
                return _put(state)
            except Exception:
                return False
        return False
    except Exception:
        return False
