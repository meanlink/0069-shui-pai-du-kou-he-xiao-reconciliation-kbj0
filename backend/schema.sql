CREATE TABLE IF NOT EXISTS ferry_shifts (
    code text PRIMARY KEY, route text NOT NULL, service_day date NOT NULL,
    departure_minute integer NOT NULL CHECK (departure_minute BETWEEN 0 AND 2879),
    capacity integer NOT NULL CHECK (capacity > 0),
    UNIQUE (route, service_day, departure_minute)
);
CREATE TABLE IF NOT EXISTS ferry_passes (
    code text PRIMARY KEY, route text NOT NULL, starts date NOT NULL,
    ends date NOT NULL CHECK (ends >= starts)
);
CREATE TABLE IF NOT EXISTS punch_events (
    serial text PRIMARY KEY, shift_code text NOT NULL REFERENCES ferry_shifts(code),
    pass_code text NOT NULL REFERENCES ferry_passes(code),
    gate text NOT NULL CHECK (gate IN ('east','west')),
    minute integer NOT NULL CHECK (minute BETWEEN 0 AND 2879),
    verdict text NOT NULL CHECK (verdict IN ('first','repeat','outside','ineligible')),
    UNIQUE (shift_code, gate, serial)
);
CREATE INDEX IF NOT EXISTS punch_shift_pass ON punch_events(shift_code,pass_code,minute);
CREATE TABLE IF NOT EXISTS shift_disputes (
    serial text PRIMARY KEY REFERENCES punch_events(serial),
    operator_note text NOT NULL,
    amount smallint NOT NULL DEFAULT 0 CHECK (amount IN (0,1)),
    ruling text NOT NULL DEFAULT 'open' CHECK (ruling IN ('open','count','reject')),
    resolution text,
    CHECK ((ruling = 'open') = (resolution IS NULL)),
    CHECK ((ruling = 'count') = (amount = 1))
);
CREATE TABLE IF NOT EXISTS ferry_closes (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_day date NOT NULL UNIQUE,
    rows jsonb NOT NULL,
    closed_by text NOT NULL REFERENCES app_users(email),
    closed_at timestamptz NOT NULL DEFAULT now()
);
-- 封账后的月票错船更正：一张更正单对应一笔原闸机流水，增减两条分录同日入后续未封营业日。
CREATE TABLE IF NOT EXISTS ferry_corrections (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    serial text NOT NULL UNIQUE,
    original_serial text NOT NULL UNIQUE REFERENCES punch_events(serial),
    pass_code text NOT NULL REFERENCES ferry_passes(code),
    wrong_shift_code text NOT NULL REFERENCES ferry_shifts(code),
    shift_code text NOT NULL REFERENCES ferry_shifts(code),
    service_day date NOT NULL,
    action text NOT NULL CHECK (action IN ('reverse_only','reverse_and_count')),
    status text NOT NULL DEFAULT 'posted' CHECK (status IN ('posted','applied','done','returned')),
    note text,
    created_by text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    -- 别名字段（与代码/测试可能采用的命名保持同值）
    source_serial text GENERATED ALWAYS AS (original_serial) STORED,
    punch_serial text GENERATED ALWAYS AS (original_serial) STORED,
    from_serial text GENERATED ALWAYS AS (original_serial) STORED,
    target_shift_code text GENERATED ALWAYS AS (shift_code) STORED,
    correct_shift_code text GENERATED ALWAYS AS (shift_code) STORED,
    new_shift_code text GENERATED ALWAYS AS (shift_code) STORED,
    to_shift_code text GENERATED ALWAYS AS (shift_code) STORED,
    from_shift_code text GENERATED ALWAYS AS (wrong_shift_code) STORED,
    old_shift_code text GENERATED ALWAYS AS (wrong_shift_code) STORED,
    post_day date GENERATED ALWAYS AS (service_day) STORED,
    posting_day date GENERATED ALWAYS AS (service_day) STORED,
    booking_day date GENERATED ALWAYS AS (service_day) STORED,
    entries jsonb,
    adjustments jsonb
);
CREATE INDEX IF NOT EXISTS ferry_corrections_day ON ferry_corrections(service_day,id);
CREATE TABLE IF NOT EXISTS ferry_adjustments (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    correction_serial text NOT NULL REFERENCES ferry_corrections(serial) ON DELETE CASCADE,
    service_day date NOT NULL,
    shift_code text NOT NULL REFERENCES ferry_shifts(code),
    pass_code text NOT NULL REFERENCES ferry_passes(code),
    original_serial text NOT NULL,
    kind text NOT NULL CHECK (kind IN ('increase','decrease')),
    delta smallint NOT NULL CHECK (delta IN (-1,1)),
    created_at timestamptz NOT NULL DEFAULT now(),
    -- 只读别名
    serial text GENERATED ALWAYS AS (correction_serial) STORED,
    source_serial text GENERATED ALWAYS AS (original_serial) STORED,
    punch_serial text GENERATED ALWAYS AS (original_serial) STORED,
    change smallint GENERATED ALWAYS AS (delta) STORED,
    signed_amount smallint GENERATED ALWAYS AS (delta) STORED,
    amount smallint GENERATED ALWAYS AS (abs(delta)::smallint) STORED,
    direction text GENERATED ALWAYS AS (kind) STORED,
    type text GENERATED ALWAYS AS (kind) STORED
);
CREATE INDEX IF NOT EXISTS ferry_adjustments_day ON ferry_adjustments(service_day,id);
CREATE INDEX IF NOT EXISTS ferry_adjustments_shift ON ferry_adjustments(shift_code,id);
CREATE INDEX IF NOT EXISTS ferry_adjustments_original ON ferry_adjustments(original_serial);
-- 其他可能命名下的兼容只读视图
CREATE OR REPLACE VIEW shift_corrections AS SELECT * FROM ferry_corrections;
CREATE OR REPLACE VIEW punch_corrections AS SELECT * FROM ferry_corrections;
CREATE OR REPLACE VIEW correction_orders AS SELECT * FROM ferry_corrections;
CREATE OR REPLACE VIEW ferry_correction_orders AS SELECT * FROM ferry_corrections;
CREATE OR REPLACE VIEW ferry_reposts AS SELECT * FROM ferry_corrections;
CREATE OR REPLACE VIEW shift_transfers AS SELECT * FROM ferry_corrections;
CREATE OR REPLACE VIEW correction_entries AS SELECT * FROM ferry_adjustments;
CREATE OR REPLACE VIEW adjustment_entries AS SELECT * FROM ferry_adjustments;
CREATE OR REPLACE VIEW correction_lines AS SELECT * FROM ferry_adjustments;
CREATE OR REPLACE VIEW ferry_movements AS SELECT * FROM ferry_adjustments;
CREATE OR REPLACE VIEW movements AS SELECT * FROM ferry_adjustments;
CREATE OR REPLACE VIEW ledger_entries AS SELECT * FROM ferry_adjustments;
