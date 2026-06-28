-- AB Lab / AB Management Supabase schema
-- Run this in Supabase SQL Editor before importing data.

create table if not exists users (
  id bigserial primary key,
  username text unique not null,
  password text not null,
  password_hash text,
  full_name text,
  role text default 'Admin',
  role_id bigint,
  is_active boolean default true,
  must_change_password boolean default false,
  last_login_at text,
  created_at text,
  updated_at text
);

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

create table if not exists patients (
  id bigserial primary key,
  hospital_id bigint,
  lab_no text unique,
  title text,
  patient_name text,
  age text,
  age_type text,
  gender text,
  contact text,
  doctor text,
  ref_by text default '',
  panel_name text default 'Self',
  booking_date text,
  reporting_date text,
  total_amount numeric default 0,
  discount numeric default 0,
  paid_amount numeric default 0,
  balance numeric default 0,
  payment_status text default 'UNPAID',
  report_status text default 'PENDING',
  last_updated text,
  created_by bigint,
  updated_by bigint,
  deleted_by bigint,
  deleted_at text
);

create table if not exists patient_tests (
  id bigserial primary key,
  hospital_id bigint,
  lab_no text,
  test_name text,
  price numeric default 0,
  status text default 'PENDING',
  result_entered_at text,
  created_by bigint,
  updated_by bigint
);

create table if not exists test_results (
  id bigserial primary key,
  hospital_id bigint,
  lab_no text,
  test_name text,
  parameter text,
  result text,
  morphology text,
  remarks text,
  entered_by bigint,
  updated_by bigint,
  verified_by bigint,
  verified_at text
);

create table if not exists test_master (
  id bigserial primary key,
  test_name text unique,
  department text,
  price numeric default 0,
  status text default 'ACTIVE',
  report_mode text default 'AUTO',
  report_heading text default '',
  report_group text default ''
);

create table if not exists test_parameters (
  id bigserial primary key,
  test_name text,
  parameter text,
  unit text,
  reference_range text,
  sort_order integer default 0
);

create table if not exists panel_names (
  id bigserial primary key,
  hospital_id bigint,
  name text,
  status text default 'ACTIVE'
);

create table if not exists panel_test_rates (
  id bigserial primary key,
  hospital_id bigint,
  panel_name text,
  test_name text,
  price numeric default 0,
  unique(hospital_id, panel_name, test_name)
);

create table if not exists result_templates (
  id bigserial primary key,
  template_type text,
  shortcut text,
  text text unique
);

create table if not exists app_settings (
  setting_key text primary key,
  setting_value text
);

create table if not exists expenses (
  id bigserial primary key,
  hospital_id bigint,
  expense_date text,
  category text,
  description text,
  amount numeric,
  created_at text
);

create table if not exists doctors (
  id bigserial primary key,
  hospital_id bigint,
  name text unique,
  phone text,
  status text default 'ACTIVE'
);

create table if not exists daily_patients (
  id bigserial primary key,
  hospital_id bigint,
  date text,
  lab_no text,
  patient_name text,
  total_amount numeric,
  paid_amount numeric,
  balance numeric,
  payment_status text,
  report_status text
);

create table if not exists report_logs (
  id bigserial primary key,
  hospital_id bigint,
  lab_no text,
  department text,
  action text,
  "user" text,
  created_at text
);

create index if not exists idx_patients_lab_no on patients(lab_no);
create index if not exists idx_patients_hospital_id on patients(hospital_id);
create index if not exists idx_patient_tests_lab_no on patient_tests(lab_no);
create index if not exists idx_patient_tests_hospital_id on patient_tests(hospital_id);
create index if not exists idx_test_results_lab_no on test_results(lab_no);
create index if not exists idx_test_results_hospital_id on test_results(hospital_id);
create index if not exists idx_report_logs_lab_no on report_logs(lab_no);
create index if not exists idx_report_logs_hospital_id on report_logs(hospital_id);
create index if not exists idx_audit_logs_hospital_id on audit_logs(hospital_id);
create unique index if not exists idx_panel_names_hospital_name on panel_names(hospital_id, name);
