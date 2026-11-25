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
