import json
from typing import Dict, Any, List, Optional
from backend.app.schemas.evidence import SBOMPayload, SBOMComponent

class SBOMAnalyzer:
    """
    Parses and analyzes CycloneDX Software Bill of Materials (SBOM) documents.
    Extracts dependencies, detects duplicate components, and validates schema integrity.
    """

    @staticmethod
    def parse_cyclonedx(raw_sbom: Dict[str, Any]) -> SBOMPayload:
        """Parse raw CycloneDX JSON dictionary into validated SBOMPayload."""
        bom_format = raw_sbom.get("bomFormat", "CycloneDX")
        spec_version = str(raw_sbom.get("specVersion", "1.5"))
        raw_components = raw_sbom.get("components", [])

        components: List[SBOMComponent] = []
        seen_purls = set()
        seen_names = set()
        duplicates: List[str] = []

        for comp in raw_components:
            name = comp.get("name", "unknown")
            version = comp.get("version", "0.0.0")
            purl = comp.get("purl")
            comp_type = comp.get("type", "library")

            # Extract license if available
            license_str = None
            licenses = comp.get("licenses", [])
            if licenses and isinstance(licenses, list):
                first_lic = licenses[0]
                if isinstance(first_lic, dict):
                    if "license" in first_lic:
                        license_str = first_lic["license"].get("id") or first_lic["license"].get("name")
                    elif "expression" in first_lic:
                        license_str = first_lic["expression"]

            # Duplicate check
            key = f"{name}@{version}"
            if key in seen_names:
                duplicates.append(key)
            else:
                seen_names.add(key)

            components.append(SBOMComponent(
                name=name,
                version=version,
                purl=purl,
                type=comp_type,
                license=license_str
            ))

        has_sig = "signature" in raw_sbom or "signatures" in raw_sbom

        return SBOMPayload(
            format=bom_format,
            spec_version=spec_version,
            component_count=len(components),
            components=components,
            duplicate_components=list(set(duplicates)),
            has_signature=has_sig
        )
