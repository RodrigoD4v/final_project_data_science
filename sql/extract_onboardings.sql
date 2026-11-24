-- Phase 2 step 1: one row per onboarding with outcome, dates and event timestamps. READ-ONLY (Dev). No names, no amounts.
select o.id as onboarding_id, o.employment_id, e.uid as employment_uid, e.client_uid, e.employee_id, o.process_id,
       o.inserted_at as created_at, o.status::text as status, o.lost_reason::text as lost_reason, o.lost_date, o.finalized_date,
       o.ee_first_logged_in_at, o.ee_info_started_at, o.ee_info_completed_at, o.offer_finalized_at, o.updated_at as onboarding_updated_at,
       e.country_code, st.name as solution_type, e.effective_date as start_date, e.anticipated_start_date, e.inserted_at as employment_created_at,
       (e.dedup_employment_id is not null) as is_dedup, es.slug as engagement_status,
       (select max(updated_at)::date from employee_onboardings) as data_date
from employee_onboardings o
join employments e on e.id = o.employment_id
left join solution_types st on st.id = e.solution_type_id
left join engagement_statuses es on es.id = e.engagement_status_id
