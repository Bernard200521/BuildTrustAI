import json
from decimal import Decimal
from typing import Optional, List, Dict, Any, BinaryIO
import boto3
from botocore.exceptions import ClientError
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.project import ProjectResponse, ProjectCreate, ProjectPolicy
from backend.app.schemas.release import ReleaseResponse, ReleaseCreate
from backend.app.schemas.evidence import EvidenceEnvelope
from backend.app.schemas.assessment import AssessmentRecord
from backend.app.schemas.audit import AuditEvent
from backend.app.utils.timestamps import utc_now_iso

def _replace_floats_with_decimals(obj: Any) -> Any:
    if isinstance(obj, list):
        return [_replace_floats_with_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _replace_floats_with_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj

def _replace_decimals_with_floats(obj: Any) -> Any:
    if isinstance(obj, list):
        return [_replace_decimals_with_floats(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _replace_decimals_with_floats(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)
    return obj

class DynamoDBRepository(BaseRepository):
    """
    AWS DynamoDB implementation of BaseRepository.
    Uses single-table design with Partition Key (PK) and Sort Key (SK).
    """

    def __init__(self, table_name: str, region_name: str = "ap-south-1", session: Optional[boto3.Session] = None):
        self.table_name = table_name
        self.region_name = region_name
        if session:
            self.dynamodb = session.resource("dynamodb", region_name=region_name)
        else:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    # ------------------ Projects ------------------
    def create_project(self, project: ProjectCreate, creator: str) -> ProjectResponse:
        now = utc_now_iso()
        item = {
            "PK": f"PROJECT#{project.project_id}",
            "SK": "METADATA",
            "project_id": project.project_id,
            "name": project.name,
            "description": project.description or "",
            "repository_url": project.repository_url,
            "policy": project.policy.model_dump(),
            "created_at": now,
            "updated_at": now,
            "created_by": creator,
            "releases_count": 0
        }
        item = _replace_floats_with_decimals(item)
        try:
            self.table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(PK)"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ValueError(f"Project with ID '{project.project_id}' already exists.")
            raise

        data = _replace_decimals_with_floats(item)
        return ProjectResponse(**data)

    def get_project(self, project_id: str) -> Optional[ProjectResponse]:
        try:
            resp = self.table.get_item(Key={"PK": f"PROJECT#{project_id}", "SK": "METADATA"})
            item = resp.get("Item")
            if not item:
                return None
            data = _replace_decimals_with_floats(item)
            releases = self.list_releases(project_id=project_id)
            data["releases_count"] = len(releases)
            return ProjectResponse(**data)
        except ClientError:
            return None

    def list_projects(self) -> List[ProjectResponse]:
        # Using scan for prototype list or GSI in production
        try:
            resp = self.table.scan(
                FilterExpression="begins_with(PK, :prefix) AND SK = :meta",
                ExpressionAttributeValues={":prefix": "PROJECT#", ":meta": "METADATA"}
            )
            items = resp.get("Items", [])
            results = []
            for item in items:
                data = _replace_decimals_with_floats(item)
                releases = self.list_releases(project_id=data["project_id"])
                data["releases_count"] = len(releases)
                results.append(ProjectResponse(**data))
            return results
        except ClientError:
            return []

    def update_project_policy(self, project_id: str, policy: ProjectPolicy) -> Optional[ProjectResponse]:
        now = utc_now_iso()
        policy_data = _replace_floats_with_decimals(policy.model_dump())
        try:
            resp = self.table.update_item(
                Key={"PK": f"PROJECT#{project_id}", "SK": "METADATA"},
                UpdateExpression="SET policy = :pol, updated_at = :now",
                ExpressionAttributeValues={":pol": policy_data, ":now": now},
                ReturnValues="ALL_NEW"
            )
            item = resp.get("Attributes")
            if not item:
                return None
            return ProjectResponse(**_replace_decimals_with_floats(item))
        except ClientError:
            return None

    # ------------------ Releases ------------------
    def create_release(self, release: ReleaseCreate, creator: str) -> ReleaseResponse:
        now = utc_now_iso()
        item = {
            "PK": f"PROJECT#{release.project_id}",
            "SK": f"RELEASE#{release.release_id}",
            "release_id": release.release_id,
            "project_id": release.project_id,
            "version": release.version,
            "source_commit": release.source_commit,
            "artifact": release.artifact.model_dump(),
            "evidence_requirements": release.evidence_requirements.model_dump(),
            "policy_version": release.policy_version,
            "environment": release.environment,
            "created_at": now,
            "updated_at": now,
            "created_by": creator,
            "latest_assessment_id": None,
            "latest_decision": "PENDING_ASSESSMENT",
            "latest_trust_score": None,
            "evidence_counts": {}
        }
        item = _replace_floats_with_decimals(item)
        try:
            self.table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(SK)"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ValueError(f"Release with ID '{release.release_id}' already exists.")
            raise

        data = _replace_decimals_with_floats(item)
        return ReleaseResponse(**data)

    def get_release(self, release_id: str) -> Optional[ReleaseResponse]:
        # Scan for release_id or query if project_id known
        try:
            resp = self.table.scan(
                FilterExpression="release_id = :rid AND begins_with(SK, :sk)",
                ExpressionAttributeValues={":rid": release_id, ":sk": "RELEASE#"}
            )
            items = resp.get("Items", [])
            if not items:
                return None
            data = _replace_decimals_with_floats(items[0])
            ev_list = self.list_evidence_for_release(release_id)
            counts: Dict[str, int] = {}
            for ev in ev_list:
                counts[ev.evidence_type] = counts.get(ev.evidence_type, 0) + 1
            data["evidence_counts"] = counts
            return ReleaseResponse(**data)
        except ClientError:
            return None

    def list_releases(self, project_id: Optional[str] = None) -> List[ReleaseResponse]:
        try:
            if project_id:
                resp = self.table.query(
                    KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                    ExpressionAttributeValues={":pk": f"PROJECT#{project_id}", ":sk": "RELEASE#"}
                )
            else:
                resp = self.table.scan(
                    FilterExpression="begins_with(SK, :sk)",
                    ExpressionAttributeValues={":sk": "RELEASE#"}
                )
            items = resp.get("Items", [])
            results = []
            for item in items:
                data = _replace_decimals_with_floats(item)
                ev_list = self.list_evidence_for_release(data["release_id"])
                counts: Dict[str, int] = {}
                for ev in ev_list:
                    counts[ev.evidence_type] = counts.get(ev.evidence_type, 0) + 1
                data["evidence_counts"] = counts
                results.append(ReleaseResponse(**data))
            return results
        except ClientError:
            return []

    def update_release_status(self, release_id: str, decision: str, trust_score: Optional[float], assessment_id: str) -> Optional[ReleaseResponse]:
        existing = self.get_release(release_id)
        if not existing:
            return None
        now = utc_now_iso()
        score_val = Decimal(str(trust_score)) if trust_score is not None else None
        try:
            resp = self.table.update_item(
                Key={"PK": f"PROJECT#{existing.project_id}", "SK": f"RELEASE#{release_id}"},
                UpdateExpression="SET latest_decision = :dec, latest_trust_score = :score, latest_assessment_id = :aid, updated_at = :now",
                ExpressionAttributeValues={
                    ":dec": decision,
                    ":score": score_val,
                    ":aid": assessment_id,
                    ":now": now
                },
                ReturnValues="ALL_NEW"
            )
            item = resp.get("Attributes")
            if not item:
                return None
            data = _replace_decimals_with_floats(item)
            return ReleaseResponse(**data)
        except ClientError:
            return None

    # ------------------ Evidence ------------------
    def save_evidence(self, evidence: EvidenceEnvelope) -> EvidenceEnvelope:
        item = {
            "PK": f"RELEASE#{evidence.release_id}",
            "SK": f"EVIDENCE#{evidence.received_at}#{evidence.evidence_id}",
            **evidence.model_dump()
        }
        item = _replace_floats_with_decimals(item)
        self.table.put_item(Item=item)
        return evidence

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceEnvelope]:
        try:
            resp = self.table.scan(
                FilterExpression="evidence_id = :eid",
                ExpressionAttributeValues={":eid": evidence_id}
            )
            items = resp.get("Items", [])
            if not items:
                return None
            return EvidenceEnvelope(**_replace_decimals_with_floats(items[0]))
        except ClientError:
            return None

    def list_evidence_for_release(self, release_id: str) -> List[EvidenceEnvelope]:
        try:
            resp = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={":pk": f"RELEASE#{release_id}", ":sk": "EVIDENCE#"}
            )
            items = resp.get("Items", [])
            evs = [EvidenceEnvelope(**_replace_decimals_with_floats(i)) for i in items]
            return sorted(evs, key=lambda x: x.received_at)
        except ClientError:
            return []

    def is_evidence_duplicate(self, release_id: str, evidence_type: str, content_sha256: str) -> bool:
        evs = self.list_evidence_for_release(release_id)
        for ev in evs:
            if ev.evidence_type == evidence_type and ev.content_sha256 == content_sha256:
                return True
        return False

    # ------------------ Assessments ------------------
    def save_assessment(self, assessment: AssessmentRecord) -> AssessmentRecord:
        ver_str = str(assessment.assessment_version).zfill(6)
        item = {
            "PK": f"RELEASE#{assessment.release_id}",
            "SK": f"ASSESSMENT#{ver_str}",
            **assessment.model_dump()
        }
        item = _replace_floats_with_decimals(item)
        self.table.put_item(Item=item)
        return assessment

    def get_latest_assessment(self, release_id: str) -> Optional[AssessmentRecord]:
        history = self.list_assessments(release_id)
        if not history:
            return None
        return history[-1]

    def list_assessments(self, release_id: str) -> List[AssessmentRecord]:
        try:
            resp = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={":pk": f"RELEASE#{release_id}", ":sk": "ASSESSMENT#"}
            )
            items = resp.get("Items", [])
            records = [AssessmentRecord(**_replace_decimals_with_floats(i)) for i in items]
            return sorted(records, key=lambda x: x.assessment_version)
        except ClientError:
            return []

    # ------------------ Audit Events ------------------
    def record_audit_event(self, event: AuditEvent) -> AuditEvent:
        item = {
            "PK": f"RELEASE#{event.release_id}",
            "SK": f"AUDIT#{event.timestamp}#{event.event_id}",
            **event.model_dump()
        }
        item = _replace_floats_with_decimals(item)
        self.table.put_item(Item=item)
        return event

    def list_audit_events(self, project_id: Optional[str] = None, release_id: Optional[str] = None, limit: int = 100) -> List[AuditEvent]:
        try:
            if release_id:
                resp = self.table.query(
                    KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                    ExpressionAttributeValues={":pk": f"RELEASE#{release_id}", ":sk": "AUDIT#"}
                )
                items = resp.get("Items", [])
            else:
                resp = self.table.scan(
                    FilterExpression="begins_with(SK, :sk)",
                    ExpressionAttributeValues={":sk": "AUDIT#"}
                )
                items = resp.get("Items", [])

            events = [AuditEvent(**_replace_decimals_with_floats(i)) for i in items]
            if project_id:
                events = [e for e in events if e.project_id == project_id]
            events.sort(key=lambda x: x.timestamp, reverse=True)
            return events[:limit]
        except ClientError:
            return []

    # ------------------ Users ------------------
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            resp = self.table.get_item(Key={"PK": f"USER#{email.lower()}", "SK": "METADATA"})
            item = resp.get("Item")
            if not item:
                return None
            return _replace_decimals_with_floats(item)
        except ClientError:
            return None

    def save_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        item = {
            "PK": f"USER#{user_data['email'].lower()}",
            "SK": "METADATA",
            **user_data
        }
        item = _replace_floats_with_decimals(item)
        self.table.put_item(Item=item)
        return user_data

    # Artifact Storage delegate to S3
    def store_artifact(self, key: str, file_obj: BinaryIO) -> str:
        raise NotImplementedError("Artifact binary storage in DynamoDB is delegated to S3Repository.")

    def get_artifact_bytes(self, key: str) -> Optional[bytes]:
        raise NotImplementedError("Artifact binary storage in DynamoDB is delegated to S3Repository.")
