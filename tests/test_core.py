import json,pathlib,tempfile,unittest
from unittest.mock import patch
from core import analyze
from local_ai import ask
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def text(self,s):
  with tempfile.TemporaryDirectory() as temp:
   p=pathlib.Path(temp)/'a.jsonl';p.write_text(s);return analyze(p)
 def sample(self):return (ROOT/'samples/can_example.jsonl').read_text()
 def test_can_recovery(self):
  d=analyze(ROOT/'samples/can_example.jsonl');e=d['episodes'][0]
  self.assertEqual(e['start_line'],3);self.assertEqual(e['end_line'],5)
  self.assertEqual(d['latest']['engine'],'OK')
 def test_firmware_recovery(self):
  e=analyze(ROOT/'samples/firmware_example.jsonl')['episodes'][0]
  self.assertEqual(e['finding'],'SENSOR_INVALID');self.assertEqual(e['end_line'],4)
 def test_bad_row(self):
  d=self.text('broken\n'+self.sample());self.assertEqual(d['skipped'],1)
  self.assertEqual(d['episodes'][0]['start_line'],4)
 def test_empty(self):
  with self.assertRaises(ValueError):self.text('{}\n')
 def test_backwards(self):
  rows=self.sample().splitlines()
  with self.assertRaisesRegex(ValueError,'backwards'):self.text(rows[2]+'\n'+rows[0])
 def test_mixed(self):
  with self.assertRaisesRegex(ValueError,'Mixed'):self.text(self.sample()+(ROOT/'samples/firmware_example.jsonl').read_text())
 def test_nan(self):
  r=json.loads(self.sample().splitlines()[0]);r['rpm']=float('nan')
  with self.assertRaises(ValueError):self.text(json.dumps(r))
 def test_unresolved(self):
  d=self.text('\n'.join(self.sample().splitlines()[:3]))
  self.assertIsNone(d['episodes'][0]['end_line'])
 def test_ai_loopback_no_tools(self):
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self):return b'{"message":{"content":"Test answer"}}'
  with patch('urllib.request.urlopen',return_value=Response()) as call:
   self.assertEqual(ask('line 3: TIMEOUT','Explain'),'Test answer')
   req=call.call_args.args[0];self.assertEqual(req.full_url,'http://127.0.0.1:11434/api/chat')
   body=json.loads(req.data);self.assertNotIn('tools',body);self.assertFalse(body['think'])
if __name__=='__main__':unittest.main()
