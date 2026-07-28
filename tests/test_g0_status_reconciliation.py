import unittest

from tools.reconcile_g0_status import derive


def raw(**kwargs):
    value = {
        "gates": {"G0": "FAIL"},
        "runtime": {"checked_out_commit_sha": "a", "peeled_commit_sha": "a", "tree_status": "clean"},
        "environment": {"architecture": "x86_64", "vllm": {"available": True}, "connector": {"available": True}},
        "model": {"available": True, "manifest_available": True},
        "inference": {"status": "pass"},
    }
    value.update(kwargs)
    return value


class G0StatusTests(unittest.TestCase):
    def test_complete_g0_g1_not_verified(self):
        result = derive(raw(), apc_executed=True)
        self.assertEqual(result["gates"]["G0"], "PASS")
        self.assertEqual(result["gates"]["G1"], "NOT_VERIFIED")
        self.assertEqual(result["formal_conclusion"], "VLLM_ENVIRONMENT_READY_EVENT_LINEAGE_NOT_VERIFIED")

    def test_missing_events_do_not_reprove_g0(self):
        result = derive(raw(), apc_executed=True)
        self.assertEqual(result["gates"]["G0"], "PASS")
        self.assertEqual(result["gates"]["G1"], "NOT_VERIFIED")

    def test_inference_failure(self):
        result = derive(raw(inference={"status": "fail"}), apc_executed=True)
        self.assertEqual(result["gates"]["G0"], "FAIL")
        self.assertEqual(result["formal_conclusion"], "G0_INFERENCE_FAILED")

    def test_g0_and_g1_pass_shape(self):
        result = derive(raw(), apc_executed=True)
        result["gates"]["G1"] = "PASS"
        result["formal_conclusion"] = "VLLM_EVENT_LINEAGE_VERIFIED"
        self.assertEqual(result["gates"], {"G0": "PASS", "G1": "PASS", "G1_authorized": True})

    def test_apc_is_a_g0_gate(self):
        result = derive(raw(), apc_executed=False)
        self.assertEqual(result["gates"]["G0"], "FAIL")
        self.assertEqual(result["formal_conclusion"], "G0_APC_FAILED")


if __name__ == "__main__":
    unittest.main()
