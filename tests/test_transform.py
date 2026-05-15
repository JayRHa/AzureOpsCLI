import unittest
from datetime import datetime, timezone
from azure_ops_cli.transform import activity_log_filter, normalize_resource, parse_resource_id

class TransformTests(unittest.TestCase):
    def test_parse_resource_id(self):
        parsed = parse_resource_id("/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Web/sites/app1")
        self.assertEqual(parsed["subscription_id"], "sub1")
        self.assertEqual(parsed["resource_group"], "rg1")
        self.assertEqual(parsed["provider"], "Microsoft.Web")
        self.assertEqual(parsed["resource_type"], "sites")
        self.assertEqual(parsed["name"], "app1")
    def test_normalize_resource_uses_resource_group_from_id(self):
        resource = normalize_resource({"id": "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Web/sites/app1", "name": "app1"})
        self.assertEqual(resource["resource_group"], "rg1")
        self.assertEqual(resource["subscription_id"], "sub1")
    def test_activity_log_filter(self):
        value = activity_log_filter(2, "rg1", now=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))
        self.assertIn("eventTimestamp ge '2026-05-15T10:00:00Z'", value)
        self.assertIn("resourceGroupName eq 'rg1'", value)

if __name__ == "__main__":
    unittest.main()
