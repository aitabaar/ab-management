-- Multi-hospital / role-based permission migration for AB Management.
-- Safe to run multiple times. Do not put passwords in this file.

create table if not exists hospitals (
  id bigserial primary key,
  name text unique not null,
  code text unique,
  address text,
  phone text,
  status text default 'ACTIVE',
  created_at text,
  updated_at text
);

create table if not exists roles (
  id bigserial primary key,
  name text unique not null,
  description text,
  is_system boolean default false,
  created_at text
);

create table if not exists permissions (
  id bigserial primary key,
  permission_key text unique not null,
  label text not null,
  category text
);

create table if not exists role_permissions (
  id bigserial primary key,
  role_id bigint references roles(id) on delete cascade,
  permission_key text not null,
  unique(role_id, permission_key)
);

create table if not exists user_permissions (
  id bigserial primary key,
  user_id bigint references users(id) on delete cascade,
  permission_key text not null,
  allowed boolean default true,
  unique(user_id, permission_key)
);

create table if not exists user_hospitals (
  id bigserial primary key,
  user_id bigint references users(id) on delete cascade,
  hospital_id bigint references hospitals(id) on delete cascade,
  unique(user_id, hospital_id)
);

create table if not exists audit_logs (
  id bigserial primary key,
  hospital_id bigint,
  user_id bigint,
  username text,
  action text not null,
  entity_type text,
  entity_id text,
  lab_no text,
  details text,
  created_at text
);

create table if not exists login_logs (
  id bigserial primary key,
  user_id bigint,
  username text,
  success boolean default false,
  ip_address text,
  created_at text
);

alter table users add column if not exists password_hash text;
alter table users add column if not exists full_name text;
alter table users add column if not exists role_id bigint;
alter table users add column if not exists is_active boolean default true;
alter table users add column if not exists must_change_password boolean default false;
alter table users add column if not exists last_login_at text;
alter table users add column if not exists created_at text;
alter table users add column if not exists updated_at text;

alter table patients add column if not exists hospital_id bigint;
alter table patients add column if not exists created_by bigint;
alter table patients add column if not exists updated_by bigint;
alter table patients add column if not exists deleted_by bigint;
alter table patients add column if not exists deleted_at text;
alter table patient_tests add column if not exists hospital_id bigint;
alter table patient_tests add column if not exists created_by bigint;
alter table patient_tests add column if not exists updated_by bigint;
alter table test_results add column if not exists hospital_id bigint;
alter table test_results add column if not exists entered_by bigint;
alter table test_results add column if not exists updated_by bigint;
alter table test_results add column if not exists verified_by bigint;
alter table test_results add column if not exists verified_at text;
alter table panel_names add column if not exists hospital_id bigint;
alter table panel_test_rates add column if not exists hospital_id bigint;
alter table expenses add column if not exists hospital_id bigint;
alter table doctors add column if not exists hospital_id bigint;
alter table daily_patients add column if not exists hospital_id bigint;
alter table report_logs add column if not exists hospital_id bigint;

insert into hospitals(name, code, status, created_at)
values ('AB Management', 'ABM', 'ACTIVE', to_char(now(), 'DD-MM-YYYY HH12:MI AM'))
on conflict (name) do nothing;

update patients set hospital_id=(select id from hospitals where name='AB Management') where hospital_id is null;
update patient_tests set hospital_id=(select id from hospitals where name='AB Management') where hospital_id is null;
update test_results set hospital_id=(select id from hospitals where name='AB Management') where hospital_id is null;
update panel_names set hospital_id=(select id from hospitals where name='AB Management') where hospital_id is null;
update panel_test_rates set hospital_id=(select id from hospitals where name='AB Management') where hospital_id is null;
update expenses set hospital_id=(select id from hospitals where name='AB Management') where hospital_id is null;
update doctors set hospital_id=(select id from hospitals where name='AB Management') where hospital_id is null;
update daily_patients set hospital_id=(select id from hospitals where name='AB Management') where hospital_id is null;
update report_logs set hospital_id=(select id from hospitals where name='AB Management') where hospital_id is null;

alter table panel_names drop constraint if exists panel_names_name_key;
alter table panel_test_rates drop constraint if exists panel_test_rates_panel_name_test_name_key;

create index if not exists idx_patients_hospital_id on patients(hospital_id);
create index if not exists idx_patient_tests_hospital_id on patient_tests(hospital_id);
create index if not exists idx_test_results_hospital_id on test_results(hospital_id);
create index if not exists idx_report_logs_hospital_id on report_logs(hospital_id);
create index if not exists idx_audit_logs_hospital_id on audit_logs(hospital_id);
create unique index if not exists idx_panel_names_hospital_name on panel_names(hospital_id, name);
create unique index if not exists idx_panel_rates_hospital_panel_test on panel_test_rates(hospital_id, panel_name, test_name);
