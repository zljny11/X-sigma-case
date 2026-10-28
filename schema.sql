PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS parents(parent_id INTEGER PRIMARY KEY, parent_name TEXT NOT NULL, phone TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS dogs(dog_id INTEGER PRIMARY KEY, parent_id INTEGER NOT NULL REFERENCES parents(parent_id), dog_name TEXT NOT NULL, breed TEXT NOT NULL, UNIQUE(dog_id,parent_id));
CREATE TABLE IF NOT EXISTS groomers(groomer_id INTEGER PRIMARY KEY, groomer_name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS services(service_id INTEGER PRIMARY KEY, service_name TEXT NOT NULL UNIQUE, duration_minutes INTEGER NOT NULL CHECK(duration_minutes=60));
CREATE TABLE IF NOT EXISTS bookings(
 booking_id INTEGER PRIMARY KEY, parent_id INTEGER NOT NULL REFERENCES parents(parent_id),
 dog_id INTEGER NOT NULL, groomer_id INTEGER NOT NULL REFERENCES groomers(groomer_id),
 service_id INTEGER NOT NULL REFERENCES services(service_id), start_time TEXT NOT NULL,
 end_time TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
 FOREIGN KEY(dog_id,parent_id) REFERENCES dogs(dog_id,parent_id),
 CHECK(julianday(end_time)>julianday(start_time)),
 CHECK(abs((julianday(end_time)-julianday(start_time))*1440-60)<0.0001)
);
CREATE INDEX IF NOT EXISTS idx_schedule ON bookings(groomer_id,start_time,end_time);
CREATE TRIGGER IF NOT EXISTS no_overlapping_insert BEFORE INSERT ON bookings
WHEN EXISTS(SELECT 1 FROM bookings WHERE groomer_id=NEW.groomer_id AND start_time<NEW.end_time AND end_time>NEW.start_time)
BEGIN SELECT RAISE(ABORT,'groomer_overlap'); END;
CREATE TRIGGER IF NOT EXISTS no_overlapping_update BEFORE UPDATE ON bookings
WHEN EXISTS(SELECT 1 FROM bookings WHERE booking_id<>NEW.booking_id AND groomer_id=NEW.groomer_id AND start_time<NEW.end_time AND end_time>NEW.start_time)
BEGIN SELECT RAISE(ABORT,'groomer_overlap'); END;
