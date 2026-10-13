from backend.app.services.sbom_analyzer import SBOMAnalyzer

def test_cyclonedx_sbom_parsing():
    raw_sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "components": [
            {"name": "fastapi", "version": "0.110.0", "type": "library"},
            {"name": "cryptography", "version": "42.0.0", "type": "library"}
        ]
    }
    payload = SBOMAnalyzer.parse_cyclonedx(raw_sbom)
    assert payload.format == "CycloneDX"
    assert payload.component_count == 2
    assert len(payload.components) == 2
    assert payload.components[0].name == "fastapi"
    assert len(payload.duplicate_components) == 0

def test_sbom_duplicate_component_detection():
    raw_sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "components": [
            {"name": "requests", "version": "2.31.0"},
            {"name": "requests", "version": "2.31.0"} # duplicate
        ]
    }
    payload = SBOMAnalyzer.parse_cyclonedx(raw_sbom)
    assert payload.component_count == 2
    assert len(payload.duplicate_components) == 1
    assert "requests@2.31.0" in payload.duplicate_components
