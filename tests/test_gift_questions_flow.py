import unittest
from test_privacy_validation import PrivacyValidationTests


class GiftQuestionFlowTests(PrivacyValidationTests):
    def test_questions_can_be_answered_and_deleted_only_by_owner(self):
        public = f"/events/public/{self.event.public_token}/gifts/{self.gift.id}/questions"
        status, question = self.request("POST", public, {"guest_name": "Гость", "text": "Какой цвет?"})
        self.assertEqual(status, 201)
        path = f"/gifts/{self.gift.id}/questions/{question['id']}"
        self.assertEqual(self.request("PATCH", path + "/answer", {"answer": "Синий"}, self.guest_token)[0], 403)
        self.assertEqual(self.request("PATCH", path + "/answer", {"answer": "Синий"}, self.owner_token)[0], 200)
        self.assertEqual(self.request("GET", public)[1][0]["answer"], "Синий")
        self.assertEqual(self.request("DELETE", path, token=self.guest_token)[0], 403)
        self.assertEqual(self.request("DELETE", path, token=self.owner_token)[0], 200)
        self.assertEqual(self.request("GET", public)[1], [])
        self.assertEqual(self.request("DELETE", path, token=self.owner_token)[0], 404)

    def test_archived_event_keeps_questions_but_rejects_new_ones(self):
        public = f"/events/public/{self.event.public_token}/gifts/{self.gift.id}/questions"
        self.assertEqual(self.request("POST", public, {"guest_name": "Гость", "text": "Размер?"})[0], 201)
        self.events.set_status(self.event.id, self.event.owner_id, "archived")
        self.assertEqual(len(self.request("GET", public)[1]), 1)
        self.assertEqual(self.request("POST", public, {"guest_name": "Гость", "text": "Цвет?"})[0], 409)


if __name__ == "__main__":
    unittest.main()
