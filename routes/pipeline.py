from flask import Blueprint, jsonify

from utils.store import get_candidates, get_google_account, get_jd

pipeline_bp = Blueprint("pipeline", __name__)


@pipeline_bp.route("/api/pipeline", methods=["GET"])
def pipeline_state():
    candidates = get_candidates()
    jd = get_jd()
    return jsonify({
        "step1_upload": len(candidates) > 0,
        "step2_jd": bool(jd.strip()) if jd else False,
        "step3_resumes": any(c.get("resume_status") for c in candidates),
        "step4_evaluate": any(c.get("eval_status") == "ok" for c in candidates),
        "step5_github": any(c.get("github_status") == "ok" for c in candidates),
        "step6_academic": any(c.get("academic_status") == "ok" for c in candidates),
        "step7_score": any(c.get("score_status") == "ok" for c in candidates),
        "step8_shortlist": any(c.get("status") == "shortlisted" for c in candidates),
        "step9_test_emails": any(c.get("status") == "test_sent" for c in candidates),
        "step10_test_results": any(c.get("test_results_status") == "ok" for c in candidates),
        "step11_rescore": any(c.get("status") == "interview" for c in candidates),
        "step12_google": get_google_account() is not None,
        "step13_schedule": any(c.get("schedule_status") == "scheduled" for c in candidates),
        "step14_interview_emails": any(c.get("interview_email_status") == "sent" for c in candidates),
        "candidate_count": len(candidates),
    })
