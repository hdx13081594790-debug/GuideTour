from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.poi import POI
from app.models.scenic_building import ScenicBuilding

# MVP 种子数据脚本。
#
# main.py 启动时会调用 seed()，确保本地数据库里至少有一批颐和园 POI。
# 这些点位支持：
# - 最近厕所导航；
# - 德和园/仁寿殿等景点路线规划；
# - FovService 根据位置和朝向推断可见景点；
# - MockRAGClient 根据 poi_id 返回讲解。
#
# 注意：真实项目应把坐标和景点资料放入后台管理或正式数据导入流程。


SEED_POIS = [
    (1, "德和园", "deheyuan", "scenic_spot", 116.27300, 39.99950, "清代皇家听戏相关区域。", 8),
    (2, "德和园大戏楼", "大戏楼,戏楼", "scenic_spot", 116.27320, 39.99955, "德和园核心建筑之一。", 10),
    (3, "仁寿门", "", "scenic_spot", 116.27080, 39.99770, "进入仁寿殿区域的重要门户。", 7),
    (4, "仁寿殿", "", "scenic_spot", 116.27140, 39.99785, "颐和园政治活动相关建筑。", 9),
    (5, "苏州街", "", "scenic_spot", 116.26500, 40.00300, "仿江南水街风貌。", 8),
    (6, "谐趣园", "", "scenic_spot", 116.27550, 40.00310, "园中园，布局精巧。", 8),
    (7, "长廊", "", "scenic_spot", 116.26850, 39.99920, "著名彩画长廊。", 9),
    (8, "佛香阁", "", "scenic_spot", 116.26780, 40.00070, "万寿山前山标志性建筑。", 10),
    (9, "昆明湖", "", "scenic_spot", 116.26350, 39.99790, "颐和园主体水面。", 9),
    (10, "排云殿", "", "scenic_spot", 116.26750, 40.00010, "万寿山中轴线建筑群。", 8),
    (11, "厕所A", "卫生间A,洗手间A", "toilet", 116.27030, 39.99880, "公共卫生间。", 5),
    (12, "厕所B", "卫生间B,洗手间B", "toilet", 116.27420, 40.00010, "公共卫生间。", 5),
    (13, "医疗室", "急救站", "medical", 116.27180, 39.99820, "园区医疗服务点。", 6),
    (14, "游客服务中心", "服务中心", "service_center", 116.26960, 39.99740, "游客咨询与服务。", 6),
    (15, "东宫门入口", "入口,东门", "entrance", 116.27000, 39.99710, "主要入口之一。", 6),
    (16, "东宫门出口", "出口,东门出口", "exit", 116.27010, 39.99700, "主要出口之一。", 6),
]


def seed() -> None:
    # seed 是幂等的：如果 id 已存在就跳过，避免每次启动重复插入。
    init_db()
    db = SessionLocal()
    try:
        for item in SEED_POIS:
            if db.get(POI, item[0]):
                continue
            db.add(POI(id=item[0], name=item[1], alias_names=item[2], poi_type=item[3], longitude=item[4], latitude=item[5], description=item[6], priority=item[7]))
        if not db.get(ScenicBuilding, 1):
            db.add(ScenicBuilding(id=1, poi_id=2, name="德和园大戏楼", dynasty="清代", historical_tags="皇家戏曲,慈禧", story_keywords="三层戏台,样式雷,慈禧", front_direction_degree=270, default_intro="德和园大戏楼是清代皇家园林中极具代表性的戏曲演出空间。", rag_collection_name="summer_palace"))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
