-- Phase 2 step 2: creation-time attributes per onboarding (employment, contract, job, offer). READ-ONLY (Dev). No names, no free text.
select o.id as onboarding_id,
  e.employment_type::text employment_type, e.pay_frequency::text pay_frequency, c.type::text contract_type, cur.code payroll_currency, c.salary contract_salary,
  j.title job_title, length(j.description) job_description_len,
  of.id offer_id, of.inserted_at offer_created_at,
  of.monthly_salary_in_contract_currency offer_monthly_salary, of.is_offering_sign_on_bonus, of.is_potential_for_variable_compensation, of.working_hours_per_week,
  of.minimum_annual_leave, of.vacation_accrual_days, of.notice_period_length, of.notice_period_term::text notice_period_term, of.notice_period::text notice_period,
  of.probation_period_days, of.probationary_period_length, of.probationary_period_term::text probationary_period_term,
  of.is_monthly_allowance_offered, of.is_supplemental_medical_insurance_offered, of.is_supplemental_life_insurance_offered, of.retirement_match_percentage,
  of.is_non_compete_requested, of.is_non_solicitation_requested, of.is_ip_clause_requested, of.is_visa_work_permit_required::text is_visa_work_permit_required,
  of.job_industry, of.primary_work_location::text primary_work_location
from employee_onboardings o
join employments e on e.id = o.employment_id
left join contracts c on c.id = e.contract_id
left join currencies cur on cur.id = c.payroll_currency_id
left join jobs j on j.id = e.job_id
left join offers of on of.id = j.offer_id
