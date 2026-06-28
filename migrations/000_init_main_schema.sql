-- AB Management Main Schema - Idempotent Initialization
-- This file creates all core tables needed by the application.
-- Safe to run multiple times - uses CREATE TABLE IF NOT EXISTS
-- Run this FIRST before any other migrations

-- Create users table first (referenced by other tables)
CREATE TABLE IF NOT EXISTS users (
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

-- Create hospitals table (referenced by many tables)
CREATE TABLE IF NOT EXISTS hospitals (
  id bigserial primary key,
  name text unique not null,
  code text unique,
  address text,
  phone text,
  status text default 'ACTIVE',
  created_at text,
  updated_at text
);

-- Create roles table
CREATE TABLE IF NOT EXISTS roles (
  id bigserial primary key,
  name text unique not null,
  description text,
  is_system boolean default false,
  created_at text
);

-- Create permissions table
CREATE TABLE IF NOT EXISTS permissions (
  id bigserial primary key,
  permission_key text unique not null,
  label text not null,
  category text
);

-- Create role_permissions table
CREATE TABLE IF NOT EXISTS role_permissions (
  id bigserial primary key,
  role_id bigint references roles(id) on delete cascade,
  permission_key text not null,
  unique(role_id, permission_key)
);

-- Create user_permissions table
CREATE TABLE IF NOT EXISTS user_permissions (
  id bigserial primary key,
  user_id bigint references users(id) on delete cascade,
  permission_key text not null,
  allowed boolean default true,
  unique(user_id, permission_key)
);

-- Create user_hospitals table
CREATE TABLE IF NOT EXISTS user_hospitals (
  id bigserial primary key,
  user_id bigint references users(id) on delete cascade,
  hospital_id bigint references hospitals(id) on delete cascade,
  unique(user_id, hospital_id)
);

-- Create login_logs table
CREATE TABLE IF NOT EXISTS login_logs (
  id bigserial primary key,
  user_id bigint,
  username text,
  success boolean default false,
  ip_address text,
  created_at text
);

-- Create patients table
CREATE TABLE IF NOT EXISTS patients (
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
  paid_amount text,
  payment_status text default 'PENDING',
  booking_date text,
  created_by bigint,
  updated_by bigint,
  deleted_by bigint,
  deleted_at text
);

-- Create patient_tests table
CREATE TABLE IF NOT EXISTS patient_tests (
  id bigserial primary key,
  lab_no text,
  test_name text,
  status text default 'PENDING',
  result_entered_at text,
  created_by bigint,
  updated_by bigint
);

-- Create test_master table
CREATE TABLE IF NOT EXISTS test_master (
  id bigserial primary key,
  test_name text unique not null,
  department text,
  price numeric,
  status text,
  report_mode text default 'AUTO',
  report_heading text default '',
  report_group text default ''
);

-- Create test_parameters table
CREATE TABLE IF NOT EXISTS test_parameters (
  id bigserial primary key,
  test_name text,
  parameter text,
  unit text,
  reference_range text,
  sort_order integer
);

-- Create test_results table
CREATE TABLE IF NOT EXISTS test_results (
  id bigserial primary key,
  lab_no text,
  test_name text,
  result text,
  entered_by bigint,
  updated_by bigint,
  verified_by bigint,
  verified_at text,
  morphology text,
  remarks text
);

-- Create panel_names table
CREATE TABLE IF NOT EXISTS panel_names (
  id bigserial primary key,
  hospital_id bigint,
  name text not null,
  price numeric
);

-- Create panel_test_rates table
CREATE TABLE IF NOT EXISTS panel_test_rates (
  id bigserial primary key,
  hospital_id bigint,
  panel_name text,
  test_name text,
  price numeric
);

-- Create departments table
CREATE TABLE IF NOT EXISTS departments (
  id bigserial primary key,
  name text unique not null
);

-- Create report_logs table
CREATE TABLE IF NOT EXISTS report_logs (
  id bigserial primary key,
  lab_no text,
  report_type text,
  department text,
  user_id bigint,
  created_at text
);

-- Create expenses table
CREATE TABLE IF NOT EXISTS expenses (
  id bigserial primary key,
  hospital_id bigint,
  expense_date text,
  amount text,
  category text,
  description text
);

-- Create doctors table
CREATE TABLE IF NOT EXISTS doctors (
  id bigserial primary key,
  hospital_id bigint,
  name text unique not null,
  contact text,
  specialization text
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
  id bigserial primary key,
  user_id bigint,
  action text,
  entity_type text,
  entity_id text,
  old_value text,
  new_value text,
  created_at text
);

-- Create app_settings table
CREATE TABLE IF NOT EXISTS app_settings (
  id bigserial primary key,
  setting_key text unique not null,
  setting_value text
);

-- Create result_templates table
CREATE TABLE IF NOT EXISTS result_templates (
  id bigserial primary key,
  template_type text,
  shortcut text,
  text text unique
);

-- Create daily_patients table
CREATE TABLE IF NOT EXISTS daily_patients (
  id bigserial primary key,
  lab_no text,
  details text,
  created_at text
);

-- Ensure all tables have hospital_id column where applicable
ALTER TABLE patients ADD COLUMN IF NOT EXISTS hospital_id bigint;
ALTER TABLE patient_tests ADD COLUMN IF NOT EXISTS hospital_id bigint;
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS hospital_id bigint;
ALTER TABLE panel_names ADD COLUMN IF NOT EXISTS hospital_id bigint;
ALTER TABLE panel_test_rates ADD COLUMN IF NOT EXISTS hospital_id bigint;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS hospital_id bigint;
ALTER TABLE doctors ADD COLUMN IF NOT EXISTS hospital_id bigint;
ALTER TABLE daily_patients ADD COLUMN IF NOT EXISTS hospital_id bigint;
ALTER TABLE report_logs ADD COLUMN IF NOT EXISTS hospital_id bigint;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_patients_lab_no ON patients(lab_no);
CREATE INDEX IF NOT EXISTS idx_patients_hospital ON patients(hospital_id);
CREATE INDEX IF NOT EXISTS idx_patient_tests_lab_no ON patient_tests(lab_no);
CREATE INDEX IF NOT EXISTS idx_test_results_lab_no ON test_results(lab_no);
CREATE UNIQUE INDEX IF NOT EXISTS idx_panel_names_hospital_name ON panel_names(hospital_id, name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_panel_rates_hospital_panel_test ON panel_test_rates(hospital_id, panel_name, test_name);

-- Add role_id column if missing
ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id bigint;
