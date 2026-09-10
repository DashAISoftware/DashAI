import logging
import os
from pathlib import Path

from fastapi import Depends
from kink import di, inject
from sqlalchemy import exc, select
from sqlalchemy.orm import sessionmaker

from DashAI.back.api.api_v1.schemas.plugin_params import PluginParams
from DashAI.back.dependencies.database.models import Plugin, Tag

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@inject
def add_plugin_to_db(
    raw_plugin: PluginParams,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
) -> Plugin:
    """Create a Plugin from a PluginParams instance and store it in the DB.

    Parameters
    ----------
    params : List[PluginParams]
        The new plugins parameters.

    Returns
    -------
    List[Plugin]
        A list with the created plugins.

    Raises
    -------
    SQLAlchemyError
        If an error occurs when connecting to the database.
    """
    logger.debug(
        "Trying to store plugin metadata in database, plugin name: %s", raw_plugin.name
    )
    with session_factory() as db:
        try:
            existing_plugins = db.scalars(
                select(Plugin).where(Plugin.name == raw_plugin.name)
            ).all()
            if existing_plugins != []:
                logger.debug("Plugin already exists, updating it.")
                plugin = existing_plugins[0]
                setattr(plugin, "author", raw_plugin.author)
                setattr(plugin, "verified", raw_plugin.verified)
                setattr(plugin, "lastest_version", raw_plugin.lastest_version)
                setattr(plugin, "summary", raw_plugin.summary)
                setattr(plugin, "description", raw_plugin.description)
                setattr(
                    plugin,
                    "description_content_type",
                    raw_plugin.description_content_type,
                )
            else:
                logger.debug("Storing plugin.")
                plugin = Plugin(
                    name=raw_plugin.name,
                    author=raw_plugin.author,
                    verified=raw_plugin.verified,
                    installed_version=raw_plugin.installed_version,
                    lastest_version=raw_plugin.lastest_version,
                    summary=raw_plugin.summary,
                    description=raw_plugin.description,
                    description_content_type=raw_plugin.description_content_type,
                )
                db.add(plugin)
            db.flush()

            for raw_tag in raw_plugin.tags:
                logger.debug(
                    (
                        "Trying to store tag metadata in database, "
                        "plugin name: %s, tag name: %s"
                    ),
                    raw_plugin.name,
                    raw_tag.name,
                )
                existing_tags = db.scalars(
                    select(Tag).where(
                        Tag.name == raw_tag.name, Tag.plugin_id == plugin.id
                    )
                ).all()
                if existing_tags == []:
                    logger.debug("storing tag.")
                    tag = Tag(
                        plugin_id=plugin.id,
                        name=raw_tag.name,
                    )
                    db.add(tag)
                else:
                    logger.debug(
                        "Tag %s already exists for plugin %s, aborting",
                        raw_tag.name,
                        plugin.name,
                    )
            db.commit()
            db.refresh(plugin)
            return plugin

        except exc.SQLAlchemyError as e:
            db.rollback()
            logger.exception(e)
            raise exc.SQLAlchemyError("Error storing plugin.") from e


def upgrade_plugin_info_in_db(
    raw_plugin: PluginParams,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
) -> Plugin:
    """Update a Plugin from a PluginParams instance and store it in the DB.

    Parameters
    ----------
    params : List[PluginParams]
        The new plugins parameters.

    Returns
    -------
    List[Plugin]
        A list with the created plugins.

    Raises
    -------
    SQLAlchemyError
        If an error occurs when connecting to the database.
    """
    logger.debug(
        "Trying to store plugin metadata in database, plugin name: %s", raw_plugin.name
    )
    with session_factory() as db:
        try:
            existing_plugins = db.scalars(
                select(Plugin).where(Plugin.name == raw_plugin.name)
            ).all()
            # the plugin always exists
            if existing_plugins != []:
                logger.debug("Plugin found, updating the info.")
                plugin = existing_plugins[0]
                setattr(plugin, "installed_version", raw_plugin.lastest_version)
                setattr(plugin, "verified", raw_plugin.verified)
                setattr(plugin, "lastest_version", raw_plugin.lastest_version)
                setattr(plugin, "summary", raw_plugin.summary)
                setattr(plugin, "description", raw_plugin.description)
                setattr(
                    plugin,
                    "description_content_type",
                    raw_plugin.description_content_type,
                )
                for raw_tag in raw_plugin.tags:
                    logger.debug(
                        (
                            "Trying to store tag metadata in database, "
                            "plugin name: %s, tag name: %s"
                        ),
                        raw_plugin.name,
                        raw_tag.name,
                    )
                    existing_tags = db.scalars(
                        select(Tag).where(
                            Tag.name == raw_tag.name, Tag.plugin_id == plugin.id
                        )
                    ).all()
                    if existing_tags == []:
                        logger.debug("storing tag.")
                        tag = Tag(
                            plugin_id=plugin.id,
                            name=raw_tag.name,
                        )
                        db.add(tag)
                    else:
                        logger.debug(
                            "Tag %s already exists for plugin %s, aborting",
                            raw_tag.name,
                            plugin.name,
                        )
                db.commit()
                db.refresh(plugin)
                return plugin
            else:
                logger.debug("Plugin not found, aborting.")
                return None

        except exc.SQLAlchemyError as e:
            db.rollback()
            logger.exception(e)
            raise exc.SQLAlchemyError("Error storing plugin.") from e


def find_entity_by_huey_id(huey_id: str) -> dict:
    """
    Find the entity associated with a huey_id and return its details.
    Returns None if no entity is found.
    """
    from kink import di

    from DashAI.back.dependencies.database.models import (
        Converter,
        Dataset,
        Explorer,
        GlobalExplainer,
        LocalExplainer,
        Run,
    )

    session_factory = di["session_factory"]

    with session_factory() as db:
        run = db.query(Run).filter(Run.huey_id == huey_id).first()
        if run:
            return {
                "entity_type": "train_model",
                "entity_id": run.id,
                "entity_name": run.name,
                "created_at": run.created,
                "last_modified": run.last_modified,
                "status": run.status,
            }

        dataset = db.query(Dataset).filter(Dataset.huey_id == huey_id).first()
        if dataset:
            return {
                "entity_type": "dataset",
                "entity_id": dataset.id,
                "entity_name": dataset.name,
                "created_at": dataset.created,
                "last_modified": dataset.last_modified,
                "status": dataset.status,
            }

        explorer = db.query(Explorer).filter(Explorer.huey_id == huey_id).first()
        if explorer:
            return {
                "entity_type": "explorer",
                "entity_id": explorer.id,
                "entity_name": explorer.name,
                "created_at": explorer.created,
                "last_modified": explorer.last_modified,
                "status": explorer.status,
            }

        global_explainer = (
            db.query(GlobalExplainer).filter(GlobalExplainer.huey_id == huey_id).first()
        )
        if global_explainer:
            return {
                "entity_type": "global_explainer",
                "entity_id": global_explainer.id,
                "entity_name": global_explainer.name,
                "created_at": global_explainer.created,
                "last_modified": global_explainer.last_modified,
            }

        local_explainer = (
            db.query(LocalExplainer).filter(LocalExplainer.huey_id == huey_id).first()
        )
        if local_explainer:
            return {
                "entity_type": "local_explainer",
                "entity_id": local_explainer.id,
                "entity_name": local_explainer.name,
                "created_at": local_explainer.created,
                "last_modified": local_explainer.last_modified,
            }

        converter = db.query(Converter).filter(Converter.huey_id == huey_id).first()
        if converter:
            return {
                "entity_type": "converter",
                "entity_id": converter.id,
                "entity_name": converter.name,
                "created_at": converter.created,
                "last_modified": converter.last_modified,
            }

        return None


def resolve_db_url(sqlite_file_path: Path) -> str:
    """
    Resolve database URL with the same priority as alembic:
      1) env var DATABASE_URL
      2) fallback to provided sqlite file path

    This is mainly to use in tests, where we set the env var to a temp path.
    """
    # 1) environment variable
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    if not str(sqlite_file_path).startswith("sqlite:///"):
        return f"sqlite:///{sqlite_file_path}"

    # 2) fallback to provided sqlite file path
    return sqlite_file_path
