import unittest

from app.database import init_db
from app.services.language import detect_language
from app.services.qa import answer_question
from app.services.route import recommend_route
from app.services.vision import recognize_image


class GuideTourServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_detect_language(self):
        self.assertEqual(detect_language("请介绍佛香阁"), "zh")
        self.assertEqual(detect_language("Tell me about Kunming Lake"), "en")
        self.assertEqual(detect_language("こんにちは"), "ja")

    def test_route_recommendation_respects_start(self):
        route = recommend_route("east_gate", 90, ["建筑", "历史"])
        self.assertEqual(route["stops"][0]["poi_id"], "east_gate")
        self.assertGreaterEqual(len(route["stops"]), 2)
        self.assertLessEqual(route["total_minutes"], 90)

    def test_route_rejects_bad_start(self):
        with self.assertRaises(ValueError):
            recommend_route("missing", 90, [])

    def test_qa_uses_poi_knowledge(self):
        answer, citations, actions, intent = answer_question("佛香阁有什么历史故事？", "zh", None)
        self.assertIn("佛香阁", answer)
        self.assertTrue(citations)
        self.assertEqual(intent, "qa")

    def test_vision_uses_filename_hint(self):
        result = recognize_image("foxiang_pavilion.jpg", b"fake-image", "zh")
        self.assertEqual(result["candidates"][0]["poi_id"], "foxiang_pavilion")
        self.assertGreaterEqual(result["candidates"][0]["confidence"], 0.7)


if __name__ == "__main__":
    unittest.main()
