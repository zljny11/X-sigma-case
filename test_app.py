"""Integration tests use a temporary DB and real HTTP requests; never modify demo data."""
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from app import Handler, connect, initialize

class BookingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.path=str(Path(self.temp.name)/'test.db');initialize(self.path)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,db_path=self.path))
        self.thread=Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def request(self,path,payload=None):
        req=Request(self.base+path,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
        try:
            with urlopen(req) as response:return response.status,json.load(response)
        except HTTPError as error:return error.code,json.load(error)
    def book(self,time='10:00',**changes):
        data=dict(parent_id=1,dog_id=1,groomer_id=1,service_id=1,start_time='2026-11-01T'+time);data.update(changes)
        return self.request('/api/bookings',data)
    def test_reference_data_and_static_page(self):
        for path,count in [('/api/parents',3),('/api/parents/1/dogs',2),('/api/groomers',3),('/api/services',2)]:
            status,data=self.request(path);self.assertEqual(status,200);self.assertEqual(len(data),count)
        with urlopen(self.base) as response:self.assertIn('wagtopia',response.read().decode().lower())
    def test_success_schedule_and_persistence(self):
        status,booking=self.book();self.assertEqual(status,201);self.assertEqual(booking['end_time'],'2026-11-01T11:00')
        status,rows=self.request('/api/groomers/1/bookings');self.assertEqual(rows[0]['parent_name'],'Alice');self.assertEqual(rows[0]['dog_name'],'Coco');self.assertEqual(rows[0]['service_name'],'Wash')
        initialize(self.path)
        with connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM bookings').fetchone()[0],1)
    def test_overlap_exact_partial_enclosing_and_adjacent(self):
        self.assertEqual(self.book()[0],201)
        for time in ['10:00','10:30','09:30']:self.assertEqual(self.book(time)[0],409)
        self.assertEqual(self.book('11:00')[0],201);self.assertEqual(self.book('09:00')[0],201)
        self.assertEqual(self.book(groomer_id=2)[0],201)
    def test_validation(self):
        for changes in [dict(dog_id=3),dict(groomer_id=99),dict(service_id=99),dict(start_time='not-a-date'),dict(parent_id=True),dict(dog_id='1')]:
            self.assertEqual(self.book(**changes)[0],400)
        self.assertEqual(self.request('/api/bookings',[])[0],400)
        self.assertEqual(self.request('/api/bookings',{})[0],400)
    def test_cross_midnight(self):
        status,booking=self.book('23:30');self.assertEqual(status,201);self.assertEqual(booking['end_time'],'2026-11-02T00:30')
        self.assertEqual(self.book(start_time='2026-11-02T00:00')[0],409)
        self.assertEqual(self.book(start_time='2026-11-02T00:30')[0],201)
    def test_parallel_requests_only_one_succeeds(self):
        with ThreadPoolExecutor(max_workers=6) as pool:statuses=list(pool.map(lambda _:self.book()[0],range(6)))
        self.assertEqual(statuses.count(201),1);self.assertEqual(statuses.count(409),5)
    def test_database_trigger_protects_direct_writes(self):
        self.book()
        with self.assertRaisesRegex(sqlite3.IntegrityError,'groomer_overlap'):
            with connect(self.path) as db:db.execute("INSERT INTO bookings(parent_id,dog_id,groomer_id,service_id,start_time,end_time) VALUES(1,1,1,1,'2026-11-01T10:30','2026-11-01T11:30')")

if __name__=='__main__':unittest.main(verbosity=2)
