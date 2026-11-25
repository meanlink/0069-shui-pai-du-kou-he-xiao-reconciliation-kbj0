from ferry.punch_logic import register
from ferry.punch_models import Punch

def seed(cx):
    cx.execute("""
        INSERT INTO ferry_shifts VALUES
        ('F-102','西沙渡','2026-11-19',480,30),('F-201','西沙渡','2026-11-19',1445,28),
        ('F-211','北湾渡','2026-11-19',540,16)
        ON CONFLICT DO NOTHING;
        INSERT INTO ferry_passes VALUES
        ('M-071','西沙渡','2026-11-01','2026-11-30'),('M-072','西沙渡','2026-11-01','2026-11-30'),
        ('M-073','西沙渡','2026-11-01','2026-11-30'),('M-082','北湾渡','2026-11-01','2026-11-30'),
        ('M-091','北湾渡','2026-10-01','2026-10-31')
        ON CONFLICT DO NOTHING;
    """)
    for serial,shift,holder,gate,minute in (
        ("GF-01","F-102","M-071","east",461), ("GF-02","F-102","M-071","west",464),
        ("GF-03","F-102","M-072","east",455), ("GF-04","F-102","M-073","east",470),
        ("GF-05","F-201","M-071","west",1444),("GF-06","F-201","M-072","east",1438),
        ("GF-07","F-211","M-082","east",522), ("GF-08","F-211","M-091","east",525),
    ):
        if not cx.execute("SELECT 1 FROM punch_events WHERE serial=%s", (serial,)).fetchone():
            register(cx, Punch(serial=serial,shift_code=shift,pass_code=holder,gate=gate,minute=minute))
    cx.execute("""
        INSERT INTO shift_disputes(serial,operator_note)
        VALUES ('GF-03','东门设备提前放行，车票号和纸本乘船单一致。'),
               ('GF-08','运营方核对十月月票续费凭单。') ON CONFLICT DO NOTHING
    """)
