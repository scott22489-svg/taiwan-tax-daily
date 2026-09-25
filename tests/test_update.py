import unittest
from scripts.update import parse_feed, merge_articles, date_string, canonical

class FeedTests(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(date_string('Fri, 25 Sep 2026 00:30:00 GMT'), '2026-09-25')
        self.assertEqual(date_string('115/09/25'), '2026-09-25')
        self.assertIsNone(date_string('not-a-date'))
        self.assertIsNone(date_string(''))

    def test_feed_sanitizes_and_filters(self):
        raw = '''<rss><channel><item><title>營業稅公告</title><link>https://example.gov.tw/a?utm_source=rss&amp;id=2</link><description>&lt;b&gt;官方說明&lt;/b&gt;</description></item><item><title>人事消息</title><link>https://example.gov.tw/b</link></item></channel></rss>'''.encode()
        rows = parse_feed(raw, {'id':'test','name':'test','taxOnly':True}, 'now')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['url'],'https://example.gov.tw/a?id=2')
        self.assertEqual(rows[0]['summary'],'官方說明')
        self.assertIsNone(rows[0]['date'])

    def test_merge_preserves_history_and_first_seen(self):
        old = [{'url':'https://a','firstSeen':'old','date':'2026-01-01','title':'before'}, {'url':'https://b','firstSeen':'old','date':None}]
        incoming = [{'url':'https://a','firstSeen':'new','date':'2026-01-01','title':'after'}]
        merged = merge_articles(old,incoming)
        self.assertEqual(len(merged),2)
        self.assertEqual(merged[0]['title'],'after')
        self.assertEqual(merged[0]['firstSeen'],'old')
        self.assertEqual(merge_articles(merged,incoming),merged)

    def test_invalid_source_does_not_silently_succeed(self):
        for raw in [b'<html>maintenance</html>',b'<rss><channel/></rss>',b'<!DOCTYPE rss><rss/>']:
            with self.assertRaises(ValueError): parse_feed(raw,{},'now')
        with self.assertRaises(ValueError): canonical('javascript:alert(1)')

if __name__ == '__main__': unittest.main()
