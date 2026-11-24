-- Phase 2 step 1: event counts known by day 3, 7 and 14 after the onboarding was created. READ-ONLY (Dev).
-- Task completion time is tasks.updated_at (to be audited); documents by employment_documents.inserted_at.
with t as (
  select o.id as onboarding_id,
    count(*) n_tasks_total,
    count(*) filter (where tk.inserted_at <= o.inserted_at + interval '3 days')  n_tasks_d3,
    count(*) filter (where tk.inserted_at <= o.inserted_at + interval '7 days')  n_tasks_d7,
    count(*) filter (where tk.inserted_at <= o.inserted_at + interval '14 days') n_tasks_d14,
    count(*) filter (where tk.status::text='completed' and tk.updated_at <= o.inserted_at + interval '3 days')  done_d3,
    count(*) filter (where tk.status::text='completed' and tk.updated_at <= o.inserted_at + interval '7 days')  done_d7,
    count(*) filter (where tk.status::text='completed' and tk.updated_at <= o.inserted_at + interval '14 days') done_d14,
    count(*) filter (where tk.status::text='failed' and tk.updated_at <= o.inserted_at + interval '3 days')  failed_d3,
    count(*) filter (where tk.status::text='failed' and tk.updated_at <= o.inserted_at + interval '7 days')  failed_d7,
    count(*) filter (where tk.status::text='failed' and tk.updated_at <= o.inserted_at + interval '14 days') failed_d14
  from employee_onboardings o join tasks tk on tk.process_id = o.process_id group by o.id),
d as (
  select o.id as onboarding_id,
    count(*) filter (where ed.inserted_at <= o.inserted_at + interval '3 days')  docs_d3,
    count(*) filter (where ed.inserted_at <= o.inserted_at + interval '7 days')  docs_d7,
    count(*) filter (where ed.inserted_at <= o.inserted_at + interval '14 days') docs_d14,
    count(*) docs_total
  from employee_onboardings o join employment_documents ed on ed.employment_id = o.employment_id group by o.id)
select o.id as onboarding_id, t.*, d.docs_d3, d.docs_d7, d.docs_d14, d.docs_total
from employee_onboardings o left join t on t.onboarding_id = o.id left join d on d.onboarding_id = o.id
