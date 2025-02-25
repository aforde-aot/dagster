# ruff: isort: skip_file

MANIFEST_PATH = ""


def scope_load_assets_from_dbt_project():
    # start_load_assets_from_dbt_project
    from dagster_dbt import load_assets_from_dbt_project

    dbt_assets = load_assets_from_dbt_project(project_dir="path/to/dbt/project")
    # end_load_assets_from_dbt_project


def scope_load_assets_from_dbt_manifest():
    # start_load_assets_from_dbt_manifest
    import json

    from dagster_dbt import load_assets_from_dbt_manifest

    with open("path/to/dbt/manifest.json") as f:
        manifest_json = json.load(f)

    dbt_assets = load_assets_from_dbt_manifest(manifest_json)
    # end_load_assets_from_dbt_manifest


def scope_dbt_cli_resource_config():
    # start_dbt_cli_resource
    import os

    from dagster_dbt import DbtCliResource, load_assets_from_dbt_project

    from dagster import Definitions

    DBT_PROJECT_PATH = "path/to/dbt_project"
    DBT_TARGET = "hive" if os.getenv("EXECUTION_ENV") == "prod" else "duckdb"

    defs = Definitions(
        assets=load_assets_from_dbt_project(DBT_PROJECT_PATH),
        resources={
            "dbt": DbtCliResource(project_dir=DBT_PROJECT_PATH, target=DBT_TARGET),
        },
    )
    # end_dbt_cli_resource


def scope_schedule_assets_dbt_only(manifest):
    # start_schedule_assets_dbt_only
    from dagster_dbt import build_schedule_from_dbt_selection, dbt_assets

    @dbt_assets(manifest=manifest)
    def my_dbt_assets():
        ...

    daily_dbt_assets_schedule = build_schedule_from_dbt_selection(
        [my_dbt_assets],
        job_name="daily_dbt_models",
        cron_schedule="@daily",
        dbt_select="tag:daily",
    )
    # end_schedule_assets_dbt_only


def scope_schedule_assets_dbt_and_downstream(manifest):
    # start_schedule_assets_dbt_downstream
    from dagster import define_asset_job, ScheduleDefinition
    from dagster_dbt import build_dbt_asset_selection, dbt_assets

    @dbt_assets(manifest=manifest)
    def my_dbt_assets():
        ...

    # selects all models tagged with "daily", and all their downstream asset dependencies
    daily_selection = build_dbt_asset_selection(
        [my_dbt_assets], dbt_select="tag:daily"
    ).downstream()

    daily_dbt_assets_and_downstream_schedule = ScheduleDefinition(
        job=define_asset_job("daily_assets", selection=daily_selection),
        cron_schedule="@daily",
    )

    # end_schedule_assets_dbt_downstream


def scope_downstream_asset():
    from dagster import OpExecutionContext, DbtCliResource
    from dagster_dbt import dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        ...

    # start_downstream_asset
    from dagster_dbt import get_asset_key_for_model
    from dagster import asset

    @asset(deps=[get_asset_key_for_model([my_dbt_assets], "my_dbt_model")])
    def my_downstream_asset():
        ...

    # end_downstream_asset_pandas_df_manager


def scope_downstream_asset_pandas_df_manager():
    from dagster import OpExecutionContext, DbtCliResource
    from dagster_dbt import dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        ...

    # start_downstream_asset_pandas_df_manager
    from dagster_dbt import get_asset_key_for_model
    from dagster import AssetIn, asset

    @asset(
        ins={
            "my_dbt_model": AssetIn(
                input_manager_key="pandas_df_manager",
                key=get_asset_key_for_model([my_dbt_assets], "my_dbt_model"),
            )
        },
    )
    def my_downstream_asset(my_dbt_model):
        # my_dbt_model is a Pandas dataframe
        return my_dbt_model.where(foo="bar")

    # end_downstream_asset_pandas_df_manager


def scope_upstream_asset():
    # start_upstream_asset
    from dagster import asset, OpExecutionContext
    from dagster_dbt import DbtCliResource, get_asset_key_for_source, dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        ...

    @asset(key=get_asset_key_for_source([my_dbt_assets], "jaffle_shop"))
    def orders():
        return ...

    # end_upstream_asset


def scope_upstream_multi_asset():
    from dagster import OpExecutionContext
    from dagster_dbt import DbtCliResource, dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        ...

    # start_upstream_multi_asset
    from dagster import multi_asset, AssetOut, Output
    from dagster_dbt import get_asset_keys_by_output_name_for_source

    @multi_asset(
        outs={
            name: AssetOut(key=asset_key)
            for name, asset_key in get_asset_keys_by_output_name_for_source(
                [my_dbt_assets], "jaffle_shop"
            ).items()
        }
    )
    def jaffle_shop(context):
        output_names = list(context.selected_output_names)
        yield Output(value=..., output_name=output_names[0])
        yield Output(value=..., output_name=output_names[1])

    # end_upstream_multi_asset


def scope_existing_asset():
    # start_upstream_dagster_asset
    from dagster import asset

    @asset
    def upstream():
        ...

    # end_upstream_dagster_asset


def scope_input_manager():
    # start_input_manager
    import pandas as pd

    from dagster import ConfigurableIOManager

    class PandasIOManager(ConfigurableIOManager):
        connection_str: str

        def handle_output(self, context, obj):
            # dbt handles outputs for us
            pass

        def load_input(self, context) -> pd.DataFrame:
            """Load the contents of a table as a pandas DataFrame."""
            table_name = context.asset_key.path[-1]
            return pd.read_sql(f"SELECT * FROM {table_name}", con=self.connection_str)

    # end_input_manager


def scope_input_manager_resources():
    class PandasIOManager:
        def __init__(self, connection_str: str):
            pass

    # start_input_manager_resources
    from dagster_dbt import DbtCliResource, load_assets_from_dbt_project

    from dagster import Definitions

    defs = Definitions(
        assets=load_assets_from_dbt_project(...),
        resources={
            "dbt": DbtCliResource(project_dir="path/to/dbt_project"),
            "pandas_df_manager": PandasIOManager(connection_str=...),
        },
    )
    # end_input_manager_resources


def scope_custom_asset_key_dagster_dbt_translator():
    # start_custom_asset_key_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetKey, OpExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
            return self.get_asset_key(dbt_resource_props).with_prefix("snowflake")

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_asset_key_dagster_dbt_translator


def scope_custom_group_name_dagster_dbt_translator():
    # start_custom_group_name_dagster_dbt_translator
    from pathlib import Path
    from dagster import OpExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping, Optional

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_group_name(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Optional[str]:
            return "snowflake"

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_group_name_dagster_dbt_translator


def scope_custom_description_dagster_dbt_translator():
    # start_custom_description_dagster_dbt_translator
    import textwrap
    from pathlib import Path
    from dagster import OpExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str:
            return textwrap.indent(dbt_resource_props.get("raw_sql", ""), "\t")

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_description_dagster_dbt_translator


def scope_custom_metadata_dagster_dbt_translator():
    # start_custom_metadata_dagster_dbt_translator
    from pathlib import Path
    from dagster import MetadataValue, OpExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_metadata(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Mapping[str, Any]:
            return {"meta": MetadataValue.json(dbt_resource_props.get("meta", {}))}

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_metadata_dagster_dbt_translator
