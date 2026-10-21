import csv
import gzip
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.count_archive import count_csv

class ArchiveCountTests(unittest.TestCase):
    def test_counts_actual_csv_rows_excluding_header(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bars.csv'
            p.write_text('timestamp,open,high,low,close,volume\n1,1,2,0.5,1.5,3\n2,1.5,3,1,2.5,4\n',encoding='utf-8')
            result=count_csv(p)[0]
            self.assertEqual(result['row_count_observed'],2)
            self.assertEqual(result['timestamp_column_candidate'],'timestamp')
            self.assertEqual(result['first_timestamp_value_in_file_order'],'1')
            self.assertEqual(len(result['sha256_on_disk']),64)
    def test_gzip_count(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bars.csv.gz'
            with gzip.open(p,'wt',encoding='utf-8',newline='') as f:
                f.write('time,open,close\n10,2,3\n20,3,4\n30,4,5\n')
            self.assertEqual(count_csv(p)[0]['row_count_observed'],3)
    def test_zip_counts_each_csv_member(self):
        import zipfile
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bundle.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('one.csv','timestamp,close\n1,2\n2,3\n')
                z.writestr('two.csv','time,close\n3,4\n')
                z.writestr('readme.txt','not data')
            got=count_csv(p)
            self.assertEqual(len(got),2)
            self.assertEqual([x['row_count_observed'] for x in got],[2,1])
class URLProbeSafetyTests(unittest.TestCase):
    def test_non_http_url_rejected_without_network(self):
        import sys
        sys.path.insert(0,str(ROOT))
        from scripts.audit_source_urls import probe
        result=probe('file:///etc/passwd')
        self.assertEqual(result['result'],'invalid_url')
        self.assertFalse(result['auth_sent'])
        self.assertFalse(result['api_key_sent'])


if __name__ == '__main__':
    unittest.main()
