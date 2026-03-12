import os
import framework
import fastapi
import requests
import datetime
import pydantic
import typing

from payment_gateway_dashboard import router as pg_dashboard_router

router = fastapi.APIRouter(prefix='/reporting')
router.include_router(pg_dashboard_router)

# Superset dashboards have embedded_id and id; custom dashboards have "custom": True
dashboard_map = {
    # "PAYMENT GATEWAY CHARGES": {"custom": True},
    "PAYMENT GATEWAY CHARGES": {'embedded_id': "b72de33e-c001-4a35-94aa-d78c839a9295", "id": "13"},
    "LP Dashboard": {'embedded_id': "b4649e12-0125-43be-af53-ab00f7525edb", "id": "16"},
}

class Reporting_Get_Dashboard_params(pydantic.BaseModel):
    dashboard_name: typing.Optional[str] = pydantic.Field("", **{})


# Action get_dashboards
@router.get('/get_dashboards', tags=['Reporting'])
async def get_dashboards():
    return dashboard_map


# Action get_dashboard_uri
@router.post('/get_dashboard_uri', tags=['Reporting'])
async def get_dashboard_uri(data: Reporting_Get_Dashboard_params):
    dashboard_id = dashboard_map.get(data.dashboard_name)
    if not dashboard_id:
        return False, "Dashboard not found"
    base_url = os.environ.get("SUPERSET_DASHBOARD_BASE_URL", "https://recon-dashboards.kanilsoft.com").rstrip("/")
    login_url = f"{base_url}/api/v1/security/login"
    csrf_url = f"{base_url}/api/v1/security/csrf_token/"
    token_url = f"{base_url}/api/v1/security/guest_token/"
    login_data = {
        "username": os.environ.get("SUPERSET_USERNAME", "admin"),
        "password": os.environ.get("SUPERSET_PASSWORD", "Algo@123"),
        "provider": "db",
    }
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    try:
        response = session.post(login_url, json=login_data)
    except Exception as e:
        print(f"Exception while authenticating with dashboard component {e}")
        return False, "Service not available, Please contact the administrator"
    if response.status_code // 100 != 2:
        err_msg = response.text
        try:
            err_body = response.json()
            if isinstance(err_body, dict) and "message" in err_body:
                err_msg = err_body.get("message", err_msg)
        except Exception:
            pass
        print(f"Error logging to dashboard url with status code {response.status_code} and message {err_msg}")
        return False, f"Error while communicating with dashboard component {response.status_code}: {err_msg}"
    access_token = response.json().get("access_token")
    if not access_token:
        print("Login response missing access_token")
        return False, "Dashboard login did not return access token"
    session.headers["Authorization"] = f"Bearer {access_token}"
    session.headers["Referer"] = f"{base_url}/"
    try:
        csrf_response = session.get(csrf_url)
    except Exception as e:
        print(f"Exception fetching CSRF token: {e}")
        return False, "Error fetching dashboard CSRF token"
    if csrf_response.status_code // 100 != 2:
        print(f"Error getting CSRF token: {csrf_response.status_code} {csrf_response.text}")
        return False, "Error getting dashboard CSRF token"
    try:
        csrf_token = csrf_response.json().get("result")
    except Exception as e:
        print(f"Invalid CSRF response: {e}")
        return False, "Invalid CSRF token response"
    if not csrf_token:
        return False, "Dashboard did not return CSRF token"
    session.headers["X-CSRFToken"] = csrf_token
    session.headers["X-CSRF-Token"] = csrf_token
    session.headers["Referer"] = f"{base_url}/"
    session.headers["Origin"] = base_url
    payload = {
        "resources": [
            {
                "type": "dashboard",
                "id": str(dashboard_id['embedded_id']),
            }
        ],
        "rls": [],
        "user": {
            "username": os.environ.get("SUPERSET_USERNAME", "admin"),
            "first_name": "Dashboard",
            "last_name": "User",
        },
        "csrf_token": csrf_token,
    }
    try:
        response = session.post(token_url, json=payload)
    except Exception as e:
        print(f"Exception in getting dashboard access {e}")
        return False, "Error in getting dashboard access, Please contact the administrator"
    if response.status_code // 100 != 2:
        err_msg = response.text
        try:
            err_body = response.json()
            if isinstance(err_body, dict):
                err_msg = err_body.get("message", err_body.get("msg", err_msg))
        except Exception:
            pass
        print(f"Error getting dashboard guest token with status code {response.status_code} and message {err_msg}")
        return False, f"Error while communicating with dashboard component {response.status_code}: {err_msg}"
    try:
        auth_token = response.json().get("token")
    except Exception as e:
        print(f"Invalid guest_token response: {e}")
        return False, "Invalid guest token response from dashboard"
    if not auth_token:
        return False, "Dashboard did not return guest token"

    return True, {
        "id": f"{dashboard_id['embedded_id']}",
        "url": f"{base_url}/",
        "token": auth_token
    }




