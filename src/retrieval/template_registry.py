"""SQL template registry: loads, validates, and renders Jinja2 SQL templates.

Templates are declared in configs/retrieval_templates.yaml. Parameters are
type-checked against the registry at render time — never construct SQL by
string concatenation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

_REGISTRY_PATH = Path(__file__).parent.parent.parent / "configs" / "retrieval_templates.yaml"
_TEMPLATES_DIR = Path(__file__).parent / "templates"


class TemplateRegistry:
    """Loads and manages Jinja2 SQL templates from the registry YAML.

    Attributes:
        _registry: Parsed registry dict keyed by template name.
        _env: Jinja2 environment pointing at the templates directory.
    """

    def __init__(self, registry_path: Path = _REGISTRY_PATH) -> None:
        """Initialise the registry from YAML.

        Args:
            registry_path: Path to retrieval_templates.yaml.
        """
        with registry_path.open() as fh:
            raw = yaml.safe_load(fh)
        self._registry: dict[str, dict[str, Any]] = {
            t["name"]: t for t in raw.get("templates", [])
        }
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            undefined=StrictUndefined,
            autoescape=False,
        )

    def get_template_names(self) -> list[str]:
        """Return all registered template names.

        Returns:
            Sorted list of template name strings.
        """
        return sorted(self._registry.keys())

    def render(self, template_name: str, params: dict[str, Any]) -> str:
        """Render a named SQL template with the given parameters.

        Parameters are type-checked against the registry declaration before
        rendering. Raises ValueError for unknown templates or type mismatches.

        Args:
            template_name: Key from retrieval_templates.yaml.
            params: Parameter dict to inject into the Jinja2 template.

        Returns:
            Rendered SQL string ready for execution.

        Raises:
            ValueError: If template_name is unknown or params fail type checks.
            KeyError: If a required parameter is missing from params.
        """
        if template_name not in self._registry:
            raise ValueError(
                f"Unknown template {template_name!r}. "
                f"Registered: {self.get_template_names()}"
            )
        meta = self._registry[template_name]
        self._validate_params(meta, params)
        tmpl = self._env.get_template(meta["file"])
        return tmpl.render(**params)

    def _validate_params(
        self, meta: dict[str, Any], params: dict[str, Any]
    ) -> None:
        """Type-check params against the registry declaration.

        Args:
            meta: Registry entry for the template.
            params: Caller-supplied parameters.

        Raises:
            KeyError: If a required parameter is absent.
            TypeError: If a parameter has the wrong Python type.
        """
        type_map: dict[str, type[Any]] = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
        }
        for param_def in meta.get("parameters", []):
            name: str = param_def["name"]
            expected_type_str: str = param_def["type"]
            if name not in params:
                raise KeyError(f"Required parameter {name!r} missing for template {meta['name']!r}")
            expected_type = type_map.get(expected_type_str, str)
            if not isinstance(params[name], expected_type):
                raise TypeError(
                    f"Parameter {name!r} expected {expected_type_str}, "
                    f"got {type(params[name]).__name__}"
                )


# Module-level singleton
registry = TemplateRegistry()
