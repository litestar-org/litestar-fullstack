from typing import Any

from app.domain.teams.models import Team, TeamInvitation, TeamMember
from app.lib.service import RepositoryService

__all__ = ["TeamService", "TeamInvitationService", "TeamMemberService"]


class TeamService(RepositoryService[Team]):
    """Team Service."""

    async def create(
        self,
        obj_in: dict[str, Any],
        commit: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> Team:
        """Create a workspace.

        Args:
            db_session (AsyncSession): _description_
            obj_in (TeamCreate): _description_

        Returns:
            Team: _description_
        """
        owner_id = obj_in.pop("owner_id")
        if owner_id is None:
            raise TeamServiceError("'owner_id' is required to create a workspace.")
        obj_tags = obj_in.pop("tags", [])
        obj_collections = obj_in.pop("collections", [])
        slug = await self.repository.get_available_slug(db_session, cast("str", obj_in.get("name")))
        obj_in["slug"] = slug

        db_obj = self.model(**obj_in)
        db_obj.members.append(TeamMember(user_id=owner_id, role=TeamRoles.ADMIN, is_owner=True))
        if obj_tags:
            for tag_text in obj_tags:
                tag, _ = await tags_service.get_or_create(
                    db_session=db_session,
                    obj_in={"name": tag_text},
                    commit=False,
                )
                db_obj.tags.append(tag)
        assessment_id = uuid4()
        db_obj.assessments.append(
            Assessment(  # type: ignore[call-arg]
                id=assessment_id,
                is_processed=False,
                bigquery_dataset=slug.replace("-", "_"),
                looker_studio_url=LookerStudioReportCloner(
                    report_id_to_clone=LOOKER_STUDIO_REPORT_ID,
                    report_name="OP",
                    report_parameters=generate_bms_sizing_parameters(settings.gcp.PROJECT, slug.replace("-", "_")),
                ).url,
            ),
        )
        db_obj = await self.repository.create(db_session, db_obj)

        if obj_collections:
            uploaded_files = await collections_storage.upload(path=f"{db_obj.id}", files=obj_collections)
            logger.info("Uploaded files to: %s", uploaded_files)
            objs_in = [
                {
                    "id": uuid4(),
                    "workspace_id": db_obj.id,
                    "collection_key": file_helpers.get_collection_key_from_file(Path(archive)),
                    "collection_id": file_helpers.get_collection_id_from_key(
                        file_helpers.get_collection_key_from_file(Path(archive)),
                    ),
                    "collection_version": str(file_helpers.get_version_from_file(Path(archive))),
                    "collection_options": file_helpers.get_collection_config_opt_from_file(Path(archive)),
                    "database_type": file_helpers.get_dbms_from_file(Path(archive)),
                    "database_version": file_helpers.get_db_version_from_file(Path(archive)),
                    "uploaded_by_id": owner_id,
                    "file_name": archive,
                }
                for archive in uploaded_files
            ]
            db_objs = await collections_service.create_many(db_session=db_session, objs_in=objs_in, commit=commit)
            logger.info("saved %s collection records", len(db_objs))
            await queue.enqueue(
                "run_workspace_assessment",
                data={
                    "assessment_id": assessment_id,
                },
                key=f"workspace-assessment-{db_obj.id}",
                timeout=1200,
                heartbeat=30,
                retries=0,
                # start it in 2 seconds
                scheduled=time() + 2,
            )
        return db_obj

    async def update(
        self,
        db_session: AsyncSession,
        db_obj: Team,
        obj_in: dict[str, Any],
        commit: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> Team:
        """Update model instance `db_obj` with fields and values specified by.

        `obj_in`.

        Args:
            db_session:   The database session.
            db_obj: The object to update.
            obj_in: The object to update with.

        Returns:
            The updated object.
        """
        tags_updated: list[str] = obj_in.pop("tags", [])
        for field_name, field_value in obj_in.items():
            if hasattr(db_obj, field_name):
                setattr(db_obj, field_name, field_value)

        tags_to_remove = [tag for tag in db_obj.tags if tag.name not in tags_updated]
        existing_tags = [tag.name for tag in db_obj.tags]
        tags_to_add = [tag for tag in tags_updated if tag not in existing_tags]
        for tag_rm in tags_to_remove:
            db_obj.tags.remove(tag_rm)
        for tag_text in tags_to_add:
            tag, _ = await tags_service.get_or_create(db_session=db_session, obj_in={"name": tag_text}, commit=False)
            db_obj.tags.append(tag)
        await self.repository.update(db_session, db_obj, commit)
        return db_obj

    async def delete(
        self,
        db_session: AsyncSession,
        id: UUID4,
        commit: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> Team | None:
        """Delete a workspace and associated BigQuery dataset."""
        db_obj = await super().delete(db_session, id, commit, *args, **kwargs)
        if db_obj is not None:
            gcp.bq_tools.delete_dataset(db_obj.slug.replace("-", "_"), settings.gcp.PROJECT)

        return db_obj


class TeamMemberService(RepositoryService[TeamMember]):
    """Team Member Service."""


class TeamInvitationService(RepositoryService[TeamInvitation]):
    """Team Invitation Service."""
