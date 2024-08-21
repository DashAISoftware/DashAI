import logging

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
