import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent

@contextmanager
def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        with db:
            yield db
    finally:
        db.close()

def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.executescript((ROOT / 'schema.sql').read_text(encoding='utf-8'))
        db.executescript((ROOT / 'seed.sql').read_text(encoding='utf-8'))

def create_booking(path, payload):
    if not isinstance(payload, dict):
        return 400, {'error': '请求必须是 JSON 对象。'}
    try:
        ids = [payload[k] for k in ('parent_id','dog_id','groomer_id','service_id')]
        if any(type(i) is not int or i < 1 for i in ids):
            raise ValueError()
        raw = payload['start_time']
        if not isinstance(raw, str):
            raise ValueError()
        start = datetime.strptime(raw, '%Y-%m-%dT%H:%M')
        if start.strftime('%Y-%m-%dT%H:%M') != raw:
            raise ValueError()
        end = start + timedelta(hours=1)
    except (KeyError, ValueError, TypeError, OverflowError):
        return 400, {'error': '请填写有效的家长、狗狗、服务、美容师及预约时间（YYYY-MM-DDTHH:mm）。'}
    start_text, end_text = start.isoformat(timespec='minutes'), end.isoformat(timespec='minutes')
    try:
        with connect(path) as db:
            # Lock before checking and inserting to prevent concurrent overlaps.
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM dogs WHERE dog_id=? AND parent_id=?', (ids[1], ids[0])).fetchone():
                return 400, {'error': '所选狗狗不属于该家长。'}
            for table, key, value in [('groomers','groomer_id',ids[2]),('services','service_id',ids[3])]:
                if not db.execute(f'SELECT 1 FROM {table} WHERE {key}=?',(value,)).fetchone():
                    return 400, {'error': '美容师或服务不存在。'}
            cursor = db.execute('INSERT INTO bookings(parent_id,dog_id,groomer_id,service_id,start_time,end_time) VALUES(?,?,?,?,?,?)', (*ids,start_text,end_text))
            return 201, {'booking_id': cursor.lastrowid, 'start_time': start_text, 'end_time': end_text}
    except sqlite3.IntegrityError as error:
        if 'groomer_overlap' in str(error):
            return 409, {'error': '这位美容师在该时段已有预约，请调整时间或更换美容师。'}
        return 400, {'error': '预约数据无效。'}
    except sqlite3.OperationalError:
        return 503, {'error': '数据库暂时忙碌，请稍后重试。'}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, db_path, **kwargs):
        self.db_path = db_path
        super().__init__(*args, directory=str(ROOT / 'static'), **kwargs)

    def respond(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path.rstrip('/')
        if not path.startswith('/api'):
            return super().do_GET()
        segments = path.split('/')[2:]
        with connect(self.db_path) as db:
            if len(segments)==1 and segments[0] in ('parents','groomers','services'):
                return self.respond(200, [dict(r) for r in db.execute(f'SELECT * FROM {segments[0]}')])
            if len(segments)==3 and segments[0]=='parents' and segments[1].isdigit() and segments[2]=='dogs':
                return self.respond(200, [dict(r) for r in db.execute('SELECT * FROM dogs WHERE parent_id=?',(int(segments[1]),))])
            if len(segments)==3 and segments[0]=='groomers' and segments[1].isdigit() and segments[2]=='bookings':
                rows = db.execute('''SELECT b.*, p.parent_name, d.dog_name, d.breed, s.service_name, g.groomer_name
                    FROM bookings b JOIN parents p USING(parent_id) JOIN dogs d USING(dog_id)
                    JOIN services s USING(service_id) JOIN groomers g USING(groomer_id)
                    WHERE b.groomer_id=? ORDER BY b.start_time,b.booking_id''',(int(segments[1]),))
                return self.respond(200, [dict(r) for r in rows])
        self.respond(404, {'error':'API 不存在。'})

    def do_POST(self):
        if urlparse(self.path).path.rstrip('/') != '/api/bookings':
            return self.respond(404, {'error':'API 不存在。'})
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 16384:
                raise ValueError()
            payload = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            return self.respond(400, {'error':'无效的 JSON 请求。'})
        status, result = create_booking(self.db_path, payload)
        self.respond(status,result)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--db',default=str(ROOT / 'data' / 'wagtopia.db'))
    args = parser.parse_args()
    initialize(args.db)
    server = ThreadingHTTPServer((args.host,args.port),partial(Handler,db_path=args.db))
    print(f'Wagtopia is ready: http://{args.host}:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__=='__main__':
    main()
