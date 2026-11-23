import copy,json,tempfile,unittest
from pathlib import Path
from etb_q1e.core import (verdict,verify_bundle,canonical,file_sha,CERT,REJECT,UNKNOWN,UNIDENTIFIED,
                          CLAIMS,PIN)
from etb_q1e.fixture import fixture,MUTATIONS,mutated,delete_at

class ClaimWitnessTest(unittest.TestCase):
    def setUp(self): self.pre,self.post=fixture()
    def test_reference_positive_limited(self):
        x=verdict(self.pre,self.post)
        self.assertEqual(x['issues'],[])
        for key in CLAIMS[:3]:self.assertEqual(x['claims'][key]['status'],CERT)
        self.assertEqual(x['claims'][CLAIMS[3]]['status'],UNIDENTIFIED)
        self.assertFalse(x['independent_native_root'])
        self.assertEqual(x['q1_status'],'Q1_BLOCKED')
    def test_all_finite_world_pairs(self):
        for name,(claim,path,_) in MUTATIONS.items():
            with self.subTest(name=name):
                neg=mutated(self.post,name)
                self.assertEqual(verdict(self.pre,neg)['claims'][claim]['status'],REJECT)
                self.assertEqual(canonical(delete_at(self.post,path)),canonical(delete_at(neg,path)))
                self.assertEqual(verdict(self.pre,delete_at(self.post,path))['claims'][claim]['status'],UNKNOWN)
    def test_claims_isolate_booking_failure(self):
        post=mutated(self.post,'wrong_cabin')
        obs=verdict(self.pre,post)['claims']
        self.assertEqual(obs[CLAIMS[0]]['status'],CERT)
        self.assertEqual(obs[CLAIMS[1]]['status'],REJECT)
        self.assertEqual(obs[CLAIMS[2]]['status'],REJECT)
    def test_claims_isolate_commit_failure(self):
        post=mutated(self.post,'seat_not_decremented')
        obs=verdict(self.pre,post)['claims']
        self.assertEqual(obs[CLAIMS[0]]['status'],CERT)
        self.assertEqual(obs[CLAIMS[1]]['status'],CERT)
        self.assertEqual(obs[CLAIMS[2]]['status'],REJECT)
    def test_benign_passenger_order_preserved(self):
        post=copy.deepcopy(self.post)
        post['state']['new_reservation']['passenger_digests'].reverse()
        for cl in CLAIMS[:3]:self.assertEqual(verdict(self.pre,post)['claims'][cl]['status'],CERT)
    def test_benign_user_link_order_preserved(self):
        post=copy.deepcopy(self.post)
        post['state']['user_reservation_ids'].reverse()
        for cl in CLAIMS[:3]:self.assertEqual(verdict(self.pre,post)['claims'][cl]['status'],CERT)
    def test_unobserved_extra_attribute_not_promoted_to_policy(self):
        post=copy.deepcopy(self.post)
        post['state']['extra_not_in_witness']='unobserved_change'
        for cl in CLAIMS[:3]:self.assertEqual(verdict(self.pre,post)['claims'][cl]['status'],CERT)
        self.assertEqual(verdict(self.pre,post)['claims'][CLAIMS[3]]['status'],UNIDENTIFIED)
    def test_source_nl_name_conflicts_with_gold_booking(self):
        from etb_q1e.core import passenger_digest
        post=copy.deepcopy(self.post)
        expected=passenger_digest('Sophia','Silva','1957-10-05')
        conflicting=passenger_digest('Sophia','Silvia','1957-10-05')
        post['state']['new_reservation']['passenger_digests'].remove(expected)
        post['state']['new_reservation']['passenger_digests'].append(conflicting)
        out=verdict(self.pre,post)['claims']
        self.assertEqual(out[CLAIMS[0]]['status'],CERT)
        self.assertEqual(out[CLAIMS[1]]['status'],REJECT)
        self.assertEqual(out[CLAIMS[3]]['status'],UNIDENTIFIED)
    def test_gold_certificate_is_narrower_than_user_any_certificate(self):
        post=copy.deepcopy(self.post)
        post['state']['new_reservation']['payment_history']=[{'payment_id':'certificate_OTHER','amount':348}]
        out=verdict(self.pre,post)['claims']
        self.assertEqual(out[CLAIMS[0]]['status'],CERT)
        self.assertEqual(out[CLAIMS[1]]['status'],REJECT)
    def test_no_write_is_contradicted(self):
        post=copy.deepcopy(self.pre);post['phase']='post';post['observation_index']=1
        out=verdict(self.pre,post)
        self.assertEqual(out['claims'][CLAIMS[0]]['status'],REJECT)
        self.assertEqual(out['claims'][CLAIMS[1]]['status'],REJECT)
    def test_missing_field_not_certified(self):
        post=copy.deepcopy(self.post);del post['state']['new_reservation']['flights']
        obs=verdict(self.pre,post)['claims']
        self.assertEqual(obs[CLAIMS[0]]['status'],CERT)
        self.assertEqual(obs[CLAIMS[1]]['status'],UNKNOWN)
        self.assertEqual(obs[CLAIMS[2]]['status'],UNKNOWN)
    def test_pair_pin_mismatch_blocked(self):
        post=copy.deepcopy(self.post);post['source_pin']='0'*40
        self.assertEqual(verdict(self.pre,post)['claims'][CLAIMS[0]]['status'],UNKNOWN)
    def test_mixed_origin_blocked(self):
        post=copy.deepcopy(self.post);post['capture_origin']='PINNED_NATIVE_RUNTIME'
        self.assertEqual(verdict(self.pre,post)['claims'][CLAIMS[0]]['status'],UNKNOWN)
    def test_nonce_mismatch_blocked(self):
        post=copy.deepcopy(self.post);post['nonce']='another'
        self.assertEqual(verdict(self.pre,post)['claims'][CLAIMS[0]]['status'],UNKNOWN)
    def test_misordered_capture_blocked(self):
        post=copy.deepcopy(self.post);post['observation_index']=0
        self.assertEqual(verdict(self.pre,post)['claims'][CLAIMS[0]]['status'],UNKNOWN)
    def test_full_source_objective_is_not_full_task(self):
        self.assertFalse(verdict(self.pre,self.post)['native_full_task_verified'])
    def test_invalid_fields_abstain(self):
        post=copy.deepcopy(self.post);post['state']['flight']['seats']='six'
        self.assertEqual(verdict(self.pre,post)['claims'][CLAIMS[2]]['status'],UNKNOWN)
    def test_stale_post_replayed_as_pre(self):
        post=copy.deepcopy(self.pre);post['phase']='post';post['observation_index']=1
        self.assertEqual(verdict(self.pre,post)['claims'][CLAIMS[0]]['status'],REJECT)
    def test_wrong_claim_never_escalates_to_c4(self):
        for name in MUTATIONS:
            self.assertEqual(verdict(self.pre,mutated(self.post,name))['claims'][CLAIMS[3]]['status'],UNIDENTIFIED)
    def test_directory_manifest_detects_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'pre.json').write_bytes(canonical(self.pre));(p/'post.json').write_bytes(canonical(self.post))
            (p/'MANIFEST.sha256.json').write_bytes(canonical({n:file_sha(p/n) for n in ('pre.json','post.json')}))
            self.assertEqual(verify_bundle(p)['status'],'Q1E_WITNESS_BUNDLE_VERIFIED_SOURCE_SCOPED')
            (p/'post.json').write_text('{}')
            self.assertEqual(verify_bundle(p)['status'],'Q1E_WITNESS_BUNDLE_BLOCKED')
    def test_duplicate_json_key(self):
        from etb_q1e.core import load_json_strict
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'dup.json';p.write_text('{"a":1,"a":2}')
            with self.assertRaisesRegex(ValueError,'DUPLICATE'):load_json_strict(p)
    def test_bundle_with_extra_file_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'pre.json').write_bytes(canonical(self.pre));(p/'post.json').write_bytes(canonical(self.post))
            (p/'MANIFEST.sha256.json').write_bytes(canonical({n:file_sha(p/n) for n in ('pre.json','post.json')}))
            (p/'unexpected.txt').write_text('hi')
            self.assertEqual(verify_bundle(p)['status'],'Q1E_WITNESS_BUNDLE_BLOCKED')
    def test_native_capture_does_not_exist_in_fixture(self):
        self.assertEqual(self.pre['capture_origin'],'AUTHOR_CONSTRUCTED')
        self.assertEqual(self.post['capture_origin'],'AUTHOR_CONSTRUCTED')

if __name__=='__main__':unittest.main()
