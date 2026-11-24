"""Phase 2 step 1: labels, exclusions, checkpoint populations and event-timing audit. Read-only on the extracts; counts and rates only.
Usage: python build_labels.py <project_dir>"""
import sys, os, numpy as np, pandas as pd
root = sys.argv[1]; base = os.path.join(root, "onboarding_early_warning"); ip = os.path.join(base, "data/interim")
B = pd.read_csv(os.path.join(ip, "onboardings_base.csv"), low_memory=False); E = pd.read_csv(os.path.join(ip, "onboardings_events.csv"), low_memory=False)
for c in ["created_at", "ee_first_logged_in_at", "ee_info_started_at", "ee_info_completed_at", "offer_finalized_at", "employment_created_at"]: B[c] = pd.to_datetime(B[c], utc=True, errors="coerce").dt.tz_localize(None)
for c in ["lost_date", "finalized_date", "start_date", "anticipated_start_date"]: B[c] = pd.to_datetime(B[c], errors="coerce")
D = pd.to_datetime(B.data_date.iloc[0]); cd = B.created_at.dt.normalize(); print("data date:", D.date(), "| onboardings:", len(B))
B["outcome_date"] = B.lost_date.where(B.status == "lost").fillna(B.finalized_date); B["days_to_outcome"] = (B.outcome_date - cd).dt.days
step = {"all onboardings": len(B)}
B = B[B.status.isin(["completed", "lost"])]; step["completed or lost (drop in_progress, pending_deposit, duplicate)"] = len(B)
B = B[~B.is_dedup]; step["not flagged as dedup employment"] = len(B)
bulk = B.created_at.dt.date.astype(str).isin(["2021-12-07", "2021-12-08", "2022-03-03"]); B = B[~bulk]; step["without bulk-load days (2021-12-07/08, 2022-03-03)"] = len(B)
B = B[cd.loc[B.index] <= D - pd.Timedelta(days=180)]; step["created at least 180 days before the data date (Q3 = A)"] = len(B)
bad_out = B.days_to_outcome < 0; step["_outcome dated before creation (dropped)"] = int(bad_out.sum()); B = B[~bad_out]
nod = B.outcome_date.isna(); step["_no outcome date (dropped)"] = int(nod.sum()); B = B[~nod]
print(pd.Series(step).to_string())
for c in ["ee_first_logged_in_at", "ee_info_started_at", "ee_info_completed_at", "offer_finalized_at"]:
    anom = B[c].notna() & (B[c] < B.created_at); print(f"   {c}: dated before creation {int(anom.sum())} rows -> set to blank (event unknown)"); B.loc[anom, c] = pd.NaT
B["y_lost"] = (B.status == "lost").astype(int); B["created_year"] = B.created_at.dt.year
B = B.merge(E, on="onboarding_id", how="left"); B.to_csv(os.path.join(ip, "onboarding_labels.csv"), index=False)
print("\nlabeled onboardings:", len(B), "| lost", int(B.y_lost.sum()), f"({B.y_lost.mean():.1%})")
print("\nby creation year:"); print(B.groupby("created_year").y_lost.agg(n="size", lost="sum", lost_pct=lambda s: round(100 * s.mean(), 1)).T.to_string())
print("\nlost reasons (labeled lost rows):"); print(B[B.y_lost == 1].lost_reason.fillna("(blank)").value_counts().head(12).to_string())
print("\ncheckpoint populations (still open at day d; day 0 = all). Day 3/7/14 models use onboardings created from 2022-04-01 (tasks and documents are complete from 2021-07); day 0 uses all years (Q4 = B)")
rows = []
for d in [0, 3, 7, 14]:
    m = (B.days_to_outcome > d) if d else pd.Series(True, index=B.index)
    if d: m &= B.created_at >= "2022-04-01"
    x = B[m]; rows.append(dict(day=d, n=len(x), lost=int(x.y_lost.sum()), lost_pct=round(100 * x.y_lost.mean(), 1), share_of_labeled_lost_still_open=round(100 * x.y_lost.sum() / B.y_lost.sum(), 1)))
print(pd.DataFrame(rows).to_string(index=False))
print("\ndays from creation to outcome (labeled): lost p10/p50/p90:", B[B.y_lost == 1].days_to_outcome.quantile([.1, .5, .9]).round(0).tolist(), "| completed:", B[B.y_lost == 0].days_to_outcome.quantile([.1, .5, .9]).round(0).tolist())
# --- timing audit: are the event fields written as they happen? fill rate by creation year and outcome
print("\n== event fill rate by creation year (labeled rows). A rate that jumps between years means the field was added or back-filled later")
for c in ["ee_first_logged_in_at", "ee_info_completed_at", "offer_finalized_at"]:
    t = B.groupby(["created_year", "status"])[c].apply(lambda s: round(100 * s.notna().mean())).unstack(); print(f"  {c}  (% filled: completed / lost)"); print("   ", {int(y): f"{int(r.get('completed', -1))}/{int(r.get('lost', -1))}" for y, r in t.iterrows()})
tk = B[B.created_at >= "2022-04-01"]; has = tk.n_tasks_total.notna()
print("\n== tasks: onboardings with tasks", f"{has.mean():.1%}", "| tasks existing by day 0..14 (mean): d3", round(tk.n_tasks_d3.mean(), 1), "d7", round(tk.n_tasks_d7.mean(), 1), "d14", round(tk.n_tasks_d14.mean(), 1), "total", round(tk.n_tasks_total.mean(), 1))
print("   monotonic done_d3 <= done_d7 <= done_d14:", bool(((tk.done_d3 <= tk.done_d7) & (tk.done_d7 <= tk.done_d14)).all()), "| done_d14 <= tasks by d14:", bool((tk.done_d14 <= tk.n_tasks_d14).all()))
print("   tasks done by day 14 vs an independent event: mean done_d14 when personal info completed by d14:", round(tk[tk.ee_info_completed_at <= tk.created_at + pd.Timedelta(days=14)].done_d14.mean(), 2), "| when not:", round(tk[~(tk.ee_info_completed_at <= tk.created_at + pd.Timedelta(days=14))].done_d14.mean(), 2))
print("   tasks done by day 14 by outcome among those open at day 14:", tk[tk.days_to_outcome > 14].groupby("status").done_d14.mean().round(2).to_dict(), "| failed_d14:", tk[tk.days_to_outcome > 14].groupby("status").failed_d14.mean().round(3).to_dict())
dc = B[B.created_at >= "2021-07-23"]; print("\n== documents by day 14 (mean) open at 14: ", dc[dc.days_to_outcome > 14].groupby("status").docs_d14.mean().round(2).to_dict(), "| rows with any document:", f"{dc.docs_total.notna().mean():.1%}")
