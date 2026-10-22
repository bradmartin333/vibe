# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "requests>=2.34.2",
# ]
# ///
"""Publish the pygbag web build to a PythonAnywhere web app as a static site.

Reads its configuration from the environment:

- PA_USERNAME: PythonAnywhere account name
- PA_API_TOKEN: API token from the PythonAnywhere "Account" page
- PA_DOMAIN: web app domain, e.g. ``username.pythonanywhere.com``
- PA_HOST: API host (optional, defaults to ``www.pythonanywhere.com``;
  use ``eu.pythonanywhere.com`` for EU accounts)

Usage: ``uv run scripts/deploy_pythonanywhere.py build/vibe/build/web``
"""

import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import requests

REMOTE_DIR_NAME: str = "vibe-web"
PYTHON_VERSION: str = "python313"
TIMEOUT_S: float = 60.0


@dataclass(frozen=True)
class Config:
    """Connection settings for the PythonAnywhere API."""

    username: str
    token: str
    domain: str
    host: str

    @property
    def api_base(self) -> str:
        """Base URL for all user-scoped API endpoints."""
        return f"https://{self.host}/api/v0/user/{self.username}"

    @property
    def remote_dir(self) -> str:
        """Absolute path on PythonAnywhere that holds the static site."""
        return f"/home/{self.username}/{REMOTE_DIR_NAME}"


def load_config() -> Config:
    """Build a Config from environment variables, exiting if any are missing."""
    missing: list[str] = [
        name
        for name in ("PA_USERNAME", "PA_API_TOKEN", "PA_DOMAIN")
        if not os.environ.get(name)
    ]
    if missing:
        sys.exit(f"missing environment variables: {', '.join(missing)}")
    return Config(
        username=os.environ["PA_USERNAME"].strip(),
        token=os.environ["PA_API_TOKEN"].strip(),
        domain=normalize_domain(os.environ["PA_DOMAIN"]),
        host=normalize_domain(os.environ.get("PA_HOST") or "www.pythonanywhere.com"),
    )


def normalize_domain(value: str) -> str:
    """Reduce a domain or URL such as " https://Me.pythonanywhere.com/ " to its host."""
    host: str = value.strip().lower()
    for scheme in ("https://", "http://"):
        host = host.removeprefix(scheme)
    return host.split("/", 1)[0]


def make_session(config: Config) -> requests.Session:
    """Create an HTTP session authenticated with the API token."""
    session: requests.Session = requests.Session()
    session.headers["Authorization"] = f"Token {config.token}"
    return session


def check(response: requests.Response) -> requests.Response:
    """Exit with a readable message if the API returned an error."""
    if not response.ok:
        sys.exit(
            f"{response.request.method} {response.url} failed "
            f"({response.status_code}): {response.text}"
        )
    return response


def ensure_webapp(session: requests.Session, config: Config) -> str:
    """Return the web app's domain as PythonAnywhere spells it, creating it if missing."""
    webapps: list[dict[str, object]] = check(
        session.get(f"{config.api_base}/webapps/", timeout=TIMEOUT_S)
    ).json()
    existing: list[str] = [str(app["domain_name"]) for app in webapps]
    for domain in existing:
        if domain.lower() == config.domain:
            print(f"using existing web app {domain}")
            return domain

    print(f"creating web app {config.domain}")
    response: requests.Response = session.post(
        f"{config.api_base}/webapps/",
        data={"domain_name": config.domain, "python_version": PYTHON_VERSION},
        timeout=TIMEOUT_S,
    )
    if not response.ok:
        sys.exit(
            f"could not create web app ({response.status_code}): {response.text}\n"
            f"web apps on this account: {', '.join(existing) or 'none'} - "
            "set PA_DOMAIN to one of these"
        )
    return config.domain


def upload_dir(session: requests.Session, config: Config, local_dir: Path) -> None:
    """Upload every file under local_dir into the remote site directory."""
    files: list[Path] = sorted(p for p in local_dir.rglob("*") if p.is_file())
    if not files:
        sys.exit(f"no files to upload in {local_dir}")
    for path in files:
        remote: str = f"{config.remote_dir}/{path.relative_to(local_dir).as_posix()}"
        print(f"uploading {remote}")
        with path.open("rb") as fh:
            check(
                session.post(
                    f"{config.api_base}/files/path{remote}",
                    files={"content": fh},
                    timeout=TIMEOUT_S,
                )
            )


def ensure_root_mapping(session: requests.Session, config: Config) -> None:
    """Map the site root URL "/" to the remote site directory."""
    url: str = f"{config.api_base}/webapps/{config.domain}/static_files/"
    mappings: list[dict[str, object]] = check(
        session.get(url, timeout=TIMEOUT_S)
    ).json()
    target: dict[str, str] = {"url": "/", "path": f"{config.remote_dir}/"}
    for mapping in mappings:
        if mapping["url"] != "/":
            continue
        if mapping["path"] != target["path"]:
            print(f"updating static mapping / -> {target['path']}")
            check(
                session.patch(f"{url}{mapping['id']}/", data=target, timeout=TIMEOUT_S)
            )
        return
    print(f"creating static mapping / -> {target['path']}")
    check(session.post(url, data=target, timeout=TIMEOUT_S))


def reload_webapp(session: requests.Session, config: Config) -> None:
    """Reload the web app so new files and mappings take effect."""
    print(f"reloading {config.domain}")
    check(
        session.post(
            f"{config.api_base}/webapps/{config.domain}/reload/", timeout=TIMEOUT_S
        )
    )


def main() -> None:
    """Deploy the build directory given on the command line."""
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    local_dir: Path = Path(sys.argv[1])
    if not (local_dir / "index.html").is_file():
        sys.exit(f"{local_dir} does not contain index.html - build first")

    config: Config = load_config()
    session: requests.Session = make_session(config)
    config = replace(config, domain=ensure_webapp(session, config))
    upload_dir(session, config, local_dir)
    ensure_root_mapping(session, config)
    reload_webapp(session, config)
    print(f"deployed to https://{config.domain}/")


if __name__ == "__main__":
    main()
