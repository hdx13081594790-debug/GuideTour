"""initial schema

Revision ID: 20260530_0001
Revises:
Create Date: 2026-05-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260530_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "poi",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("alias_names", sa.Text(), nullable=True),
        sa.Column("poi_type", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.Column("map_provider", sa.String(length=32), nullable=True),
        sa.Column("amap_poi_id", sa.String(length=128), nullable=True),
        sa.Column("baidu_uid", sa.String(length=128), nullable=True),
        sa.Column("area_name", sa.String(length=128), nullable=True),
        sa.Column("is_accessible", sa.Boolean(), nullable=False),
        sa.Column("opening_status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_poi_id"), "poi", ["id"], unique=False)
    op.create_index(op.f("ix_poi_name"), "poi", ["name"], unique=False)
    op.create_index(op.f("ix_poi_poi_type"), "poi", ["poi_type"], unique=False)

    op.create_table(
        "scenic_building",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("poi_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("dynasty", sa.String(length=64), nullable=True),
        sa.Column("historical_tags", sa.Text(), nullable=True),
        sa.Column("story_keywords", sa.Text(), nullable=True),
        sa.Column("bounding_polygon", sa.Text(), nullable=True),
        sa.Column("front_direction_degree", sa.Float(), nullable=True),
        sa.Column("recommended_view_distance_min", sa.Float(), nullable=False),
        sa.Column("recommended_view_distance_max", sa.Float(), nullable=False),
        sa.Column("default_intro", sa.Text(), nullable=True),
        sa.Column("rag_collection_name", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["poi_id"], ["poi.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scenic_building_name"), "scenic_building", ["name"], unique=False)
    op.create_index(op.f("ix_scenic_building_poi_id"), "scenic_building", ["poi_id"], unique=False)

    op.create_table(
        "user_session",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("current_poi_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_session_session_id"), "user_session", ["session_id"], unique=True)

    op.create_table(
        "device",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_code", sa.String(length=64), nullable=False),
        sa.Column("user_session_id", sa.String(length=64), nullable=True),
        sa.Column("device_type", sa.String(length=32), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("battery_level", sa.Integer(), nullable=True),
        sa.Column("last_latitude", sa.Float(), nullable=True),
        sa.Column("last_longitude", sa.Float(), nullable=True),
        sa.Column("last_heading", sa.Float(), nullable=True),
        sa.Column("last_pitch", sa.Float(), nullable=True),
        sa.Column("last_roll", sa.Float(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_device_device_code"), "device", ["device_code"], unique=True)
    op.create_index(op.f("ix_device_user_session_id"), "device", ["user_session_id"], unique=False)

    op.create_table(
        "navigation_task",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("user_session_id", sa.String(length=64), nullable=False),
        sa.Column("origin_latitude", sa.Float(), nullable=False),
        sa.Column("origin_longitude", sa.Float(), nullable=False),
        sa.Column("destination_poi_id", sa.Integer(), nullable=True),
        sa.Column("destination_name", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("route_distance_meters", sa.Float(), nullable=False),
        sa.Column("route_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("route_polyline", sa.Text(), nullable=False),
        sa.Column("route_steps", sa.Text(), nullable=False),
        sa.Column("current_step_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_navigation_task_task_id"), "navigation_task", ["task_id"], unique=True)
    op.create_index(op.f("ix_navigation_task_user_session_id"), "navigation_task", ["user_session_id"], unique=False)

    op.create_table(
        "interaction_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_session_id", sa.String(length=64), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=True),
        sa.Column("input_type", sa.String(length=32), nullable=False),
        sa.Column("user_text", sa.Text(), nullable=True),
        sa.Column("intent", sa.String(length=64), nullable=True),
        sa.Column("tool_called", sa.String(length=128), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("related_poi_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interaction_log_user_session_id"), "interaction_log", ["user_session_id"], unique=False)

    op.create_table(
        "photo_asset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=True),
        sa.Column("file_path", sa.String(length=512), nullable=True),
        sa.Column("related_poi_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_photo_asset_asset_id"), "photo_asset", ["asset_id"], unique=True)
    op.create_index(op.f("ix_photo_asset_session_id"), "photo_asset", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_photo_asset_session_id"), table_name="photo_asset")
    op.drop_index(op.f("ix_photo_asset_asset_id"), table_name="photo_asset")
    op.drop_table("photo_asset")
    op.drop_index(op.f("ix_interaction_log_user_session_id"), table_name="interaction_log")
    op.drop_table("interaction_log")
    op.drop_index(op.f("ix_navigation_task_user_session_id"), table_name="navigation_task")
    op.drop_index(op.f("ix_navigation_task_task_id"), table_name="navigation_task")
    op.drop_table("navigation_task")
    op.drop_index(op.f("ix_device_user_session_id"), table_name="device")
    op.drop_index(op.f("ix_device_device_code"), table_name="device")
    op.drop_table("device")
    op.drop_index(op.f("ix_user_session_session_id"), table_name="user_session")
    op.drop_table("user_session")
    op.drop_index(op.f("ix_scenic_building_poi_id"), table_name="scenic_building")
    op.drop_index(op.f("ix_scenic_building_name"), table_name="scenic_building")
    op.drop_table("scenic_building")
    op.drop_index(op.f("ix_poi_poi_type"), table_name="poi")
    op.drop_index(op.f("ix_poi_name"), table_name="poi")
    op.drop_index(op.f("ix_poi_id"), table_name="poi")
    op.drop_table("poi")
