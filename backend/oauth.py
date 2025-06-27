# backend/oauth.py
import streamlit as st
import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Create login URL
def get_login_url():
    flow = Flow.from_client_secrets_file(
        'credentials/client_secret.json',
        scopes=SCOPES,
        redirect_uri=st.secrets["general"]["REDIRECT_URI"]
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
    # st.session_state["oauth_flow"] = flow
    return auth_url

# Exchange code for token
# backend/oauth.py
def fetch_token(code: str):
    # Recreate flow from file, not session
    flow = Flow.from_client_secrets_file(
        'credentials/client_secret.json',
        scopes=SCOPES,
        redirect_uri=st.secrets["general"]["REDIRECT_URI"]
    )
    flow.fetch_token(
        code=code,
        client_secret=st.secrets["google_oauth"]["client_secret"]
    )
    return flow.credentials


# Build Calendar API client from credentials
def get_calendar_service(creds: Credentials):
    return build("calendar", "v3", credentials=creds)



# GOOGLE_CALENDAR_CLIENT_EMAIL = "tailortalk-bot@zeta-crossbar-464011-m2.iam.gserviceaccount.com"
# GOOGLE_CALENDAR_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCLoeylezi8Zoqr\nx/vDzf3f+KvHTBIfAMt5hwIadhu933EPp0U8pcmb1sgk8FssOhWlzlasjrkMYi9g\n8LH+mQUybzxvK+6NQkkhIviK3GeyrULy0YSVp1ic2qlw/Y1t4EJSvLjMyxacSLJP\n2bD+MJIg1k2EX5mWSXxZ2zT7rGJODKvcpFH281jJNuzInb3rRDKSt+/L7uFyWadq\nMTS/HxxL8UO/OcTeGCB+0UD+LLBhpKSzXLdiKuMuB4sRHMb7CnLJhfwVvd6Myuu4\nz05U1u3RU4IyTjZ7EwqBHnCZ22FtVTn8iSHaksWhah253ojSN+7QkrF0XwRDA8L4\no1ly0Qa3AgMBAAECggEARLazmR/RZM1lcnGgkNP/GkfqaNIjnMQsXaq1u0XiEwcx\nQU3EgbroQttodN0fUN1op8ap2pMFt3Vd8WuhfDPbXd1ltSO+ah9zk239N4CNO12O\nM6Ytg+PtdIsalTMBdU/F86dRnd5XSyNvNGJhekV2s9giH4FYOKADJMj+AtfrLJLP\nptDqi+CjCctALdbJe5rVAiDW10TLZEZmKae0FshhySAKVWchNGuybN4cIB7fkDNP\n17NFnL2V3IVNLw9u4hWkemc7JLj1sqlKIBv6itiO6N+fV8hIRMqSPQLaRt4sXubm\nvEYTp6KQeFI1qKAiu22Z40dUEVHPuIiyVlWkMDMiCQKBgQDApZRkhbbRnO7jKRog\ncQ0IcKYW+VmaUpqkWxGBANNtoNl+UyMa4fDrSCDkw4MZ3bCIqiuJ/rUI5MI0D8hg\nAmrtrCL19midtYNKVGNHyuTTDOvPcgQir/+92G1UNpdj4boU8UPfS+JfAWxpg31m\nsxTt0AH9kzFH/T2xjISUXrdh8wKBgQC5jTbDlJDb9eG8ebsS1XEAhA3rA9j9S2fF\n0am5vYu2Jku+bPEvY+JhhonOhdc9im6GZMDEvL4SyUP+J7xKs2bhN0xDF7ArNq7/\nUwWJRljeU2pCqsPjsqsJei0MZ0M8A8X2t86FGgrRnl/QhxN7xh7LXixb5H9h+Fh/\nHRuti1y1LQKBgE+lZUd1/NKGlkE2YgXdl2zQ3eoLpx7lXefrer4h8EeXw7O1fYME\nvI0ZoffSWSZdgDnQWPXRZ1lI8n2BtO70sO6YR0/3UuM5AxG899rbqGUVJ3z5f3oz\n14DOtMynUUnLLhqwcMYl4m4y8XZiFXtbOKDlaZ1DuJExwsrf9IQ+8IQ/AoGAfQfj\n7BxzFFT2PGuGnGVJFQDm5AMet2eVUJ48ERXhS+c4SOPeDYHv7KmcuJZFeImMenDv\n2GIabkxCzcL2xRtoasA5WkhfBG9/sjq+U0cc4QsyYiPxhcBCMkuqiV4X1xvvzJUE\ny3nF6oQeqkQq48+XtpAJsg4hq+GNuHHj0ahD2y0CgYBgHZXfQi8lU3XCCX1ErbzX\nsSK4UrfxpKeUFyfQvkqPDsbv7ZbXo2Ofj4ZQVW5pPAt16rqBKb26QDKKfSPc2d76\nocU4JhxFBw9iM8OjZvCjtVo9oHsixh7EeFKpDM/AkxMQAVg6ewOcioYbGmgZQFLl\njETuzyEbR2D9GYsoS19mCw==\n-----END PRIVATE KEY-----\n"""