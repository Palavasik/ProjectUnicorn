-- Project Unicorn: Supabase schema for users and feedback.
-- Run this script once in Supabase Dashboard → SQL Editor (New query → paste → Run).

-- Table: users (telegram users, first/last seen)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id BIGINT NOT NULL UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_user_id ON public.users (telegram_user_id);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- No policies for anon; backend uses service_role key which bypasses RLS in Supabase.


-- Table: feedback (after user selects a route)
CREATE TABLE IF NOT EXISTS public.feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id BIGINT NOT NULL,
    route_name TEXT NOT NULL,
    rating SMALLINT,
    comment TEXT,
    distance_km NUMERIC,
    start_lat NUMERIC,
    start_lon NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_telegram_user_id ON public.feedback (telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback (created_at);

ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

-- Backend uses service_role; no anon policies needed.
