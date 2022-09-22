"""Documentation generator for Python projects."""
import os
import shutil
import subprocess
import tempfile

from pathlib import Path
from typing import Optional, TypedDict

from jinja2 import Environment, PackageLoader
import tomli

from doccer.types import EmailContact, ProjectType


def _jinja_env() -> Environment:
    """
    Return the jinja2 environment used to render templates.

    :return: jinja2 environment
    """
    return _jinja_env.env or Environment(loader=PackageLoader("doccer"))


_jinja_env.env = None


class DerivedConfigData(TypedDict):
    """Data computed from configuration files. All of these fields can be counted on to exist
    and have reasonable values.
    """

    author: EmailContact
    build_dir: str
    deploy_dir: str
    project_name: str


class DocConfig(TypedDict):
    """Documentation configuration."""

    pyproject_path: str
    doc_src: str
    doc_dest: str
    pyproject_data: dict
    py_modules: list[str]
    derived: DerivedConfigData


def precommit_hook() -> None:
    """
    This is the entry point when called as a pre-commit hook. It will build documentation from
    source, or create and build some example documentation source files if none are found.

    TODO: add details about how configs are found and how they are used to build docs.

    :return: None
    """

    # Find and act on configs in pyproject.toml file(s):
    configs = _load_configs()

    for config in configs:

        # Use a temp dir as the build destination:
        with tempfile.TemporaryDirectory() as tmpdir:
            config["derived"]["build_dir"] = tmpdir

            _debug_out(f"config found: {config}")

            if not Path(config["doc_src"]).exists():
                _debug_out(f"doc source dir not found. generating sample docs")
                _generate_sample_docs_source(config)

            _build_with_sphinx(config)
            _debug_out(f"deploying docs to {config['derived']['deploy_dir']}")
            _deploy_docs(config)


def _generate_sample_docs_source(config: DocConfig) -> None:
    """
    Generate sample documentation source files.

    :param config: Configuration options from pyproject.toml.
    :return: None
    """

    source_path = Path(config["doc_src"])
    # Root document:
    _render_template("README.rst.jinja2", source_path, **config)
    # Example subpage:
    _render_template("subpage.rst.jinja2", source_path / "docs", **config)
    # Sphinx config and makefile:
    _render_template("conf.py.jinja2", source_path, **config)
    _render_template("Makefile.jinja2", source_path, **config)


def _render_template(template_name: str, dest_dir: os.PathLike, **kwargs) -> None:
    """
    Render a template to a destination directory. The destination directory will be created if
    it does not exist. The destination filename will be the same as the template name, minus the
    .jinja2 extension.

    :param template_name:
    :param dest_dir:
    :param kwargs: Context data for the template.
    :return: None
    """

    template = _jinja_env().get_template(template_name)

    os.makedirs(dest_dir, exist_ok=True)
    with open(Path(dest_dir) / template_name.replace(".jinja2", ""), "w") as f:
        f.write(template.render(**kwargs))


def _load_configs(repo_root: os.PathLike = ".") -> list[DocConfig]:
    """
    Find all `pyproject.toml` files in the repository and create a `DocConfig` instance for each.

    :param repo_root: Root of the repository to search for pyproject.toml files. Defaults to the
        current working directory, which will be the repository root when called as a pre-commit.
    :return: list of DocConfig instances
    """

    # for now we only support pyproject.toml
    pyprojects = list(Path(repo_root).rglob("pyproject.toml"))
    _debug_out(f"Found {len(pyprojects)} pyprojects: {pyprojects}")

    configs = []
    for pyproject in pyprojects:
        if config := _load_config(pyproject):
            configs.append(config)

    return configs


def _load_config(pyproject: os.PathLike) -> Optional[DocConfig]:
    """
    Load a `DocConfig` instance from a `pyproject.toml` file, if there is a [tool.doccer] section,
    otherwise `None` is returned.

    :param pyproject:
    :return:
    """

    with open(pyproject, "rb") as f:
        toml = tomli.load(f)

    if (magdocs_config := toml.get("tool", {}).get("doccer")) is not None:

        src_dir = magdocs_config.get("doc_src", "docs/src")

        derived_config = {}
        if toml["project"].get("authors"):
            derived_config["author"] = toml["project"]["authors"][0]
        else:
            derived_config["author"] = EmailContact(name="unknown", email="unknown")

        # todo: make these configurable
        derived_config["build_dir"] = str(Path(src_dir).parent / "build")
        derived_config["deploy_dir"] = "."

        return {
            "pyproject_path": str(pyproject),
            "pyproject_data": toml,
            "doc_src": src_dir,
            "doc_dest": magdocs_config.get("doc_dest", "."),
            "derived": derived_config,
            "py_modules": magdocs_config.get("py_modules", [toml["project"]["name"]]),
        }


def _build_with_sphinx(config: DocConfig) -> bool:
    """
    Call out to ``sphinx-build`` to render the documentation files from source.

    :param config: Configuration options from pyproject.toml.
    :return: True if files were changed, False otherwise.
    """

    cmd = [
        "sphinx-build",
        "-b",  # builder to use is...
        "rst",  # reStructuredText
        config["doc_src"],
        config["derived"]["build_dir"],
    ]
    _debug_out(f"Building docs with sphinx: {cmd=}")
    sphinx_proc = subprocess.run(cmd, check=True, capture_output=True)

    _debug_out(f"sphinx stdout: {sphinx_proc.stdout.decode()}")
    _debug_out(f"sphinx exit code: {sphinx_proc.returncode}")

    # Exit with status code 1 if files were changed:
    return b"writing output" in sphinx_proc.stdout


def _deploy_docs(config: DocConfig) -> None:
    """
    Deploy the rendered documentation to the configured destination.

    :param config: Configuration options from pyproject.toml.
    :return: None
    """
    deploy_to = Path(config["derived"]["deploy_dir"])
    _debug_out(f"deploying docs to {deploy_to}")

    for docfile in Path(config["derived"]["build_dir"]).rglob("*.rst"):
        dest = deploy_to / docfile.relative_to(config["derived"]["build_dir"])
        shutil.copy(docfile, dest)


def _get_project_type(project_root: os.PathLike = ".") -> ProjectType:
    """
    Determine the flavor of the project by looking for certain files in the project root.

    :param project_root: Root of the project to check. Defaults to the current working directory,
        which will be the repository root when called as a pre-commit.
    :return: ProjectType
    """

    if Path(project_root) / "pyproject.toml":
        toml = tomli.load(open(Path(project_root) / "pyproject.toml", "rb"))

        if toml.get("tool", {}).get("poetry"):
            return ProjectType.POETRY

        elif toml.get("tool", {}).get("pdm"):
            return ProjectType.PDM

    elif Path(project_root) / "setup.py":
        return ProjectType.SETUP_PY

    else:
        return ProjectType.UNKNOWN


def _debug_out(msg: str) -> None:
    """
    Print a debug message. It will only be shown if pre-commit is invoked with --verbose.

    :param msg: the message to output.
    :return: None
    """

    print(f"[maglogs] {msg}")
