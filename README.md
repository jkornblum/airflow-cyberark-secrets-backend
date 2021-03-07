# airflow-cyberark-secrets-backend
This is a secrets backend for CyberArk CCP (central credential provider)
for the Apache Airflow platform. It will allow one to pull connections and 
variables from their CyberArk safes via the CCP.

This library has been tested with Airflow 1.10.14.

Documentation for CyberArk CCP can be found [here](https://docs.cyberark.com/Product-Doc/OnlineHelp/AAM-CP/11.2/en/Content/CCP/Calling-the-Web-Service-using-REST.htm?tocpath=Developer%7CCentral%20Credential%20Provider%7CCall%20the%20Central%20Credential%20Provider%20Web%20Service%20from%20Your%20Application%20Code%7C_____2) . 

Documentation for Airflow secrets backends can be found [here](https://airflow.apache.org/docs/apache-airflow/1.10.14/howto/use-alternative-secrets-backend.html?highlight=secrets)

## Usage
`pip install airflow-cyberark-secrets-backend`

Update your `airflow.cfg` with the following
```
[secrets]
backend = airflow_cyberark_secrets_backend.CyberArkSecretsBackend

backend_kwargs = {"app_id": "/files/var.json", "ccp_url": "/files/conn.json", "safe": "", "verify": "/path/to/ssl/cert.pem" }
```

The backend_kwargs:
- app_id : The application ID for CCP
- ccp_url : The host URL for CCP AIM, excluding query params
- safe : The secrets safe
- verify : The SSL cert path to for CCP SSL, can be False for disable, can be env var `CYBERARK_SSL`, default `False`

This library expects and requires your CyberArk response to have the
the following properties (will be mapped mapped to Airflow keys). This
map is a band-aid required from the little configuration CyberArk PAM (11.xx)
allows.

- AccountDescription : svc_account
- ApplicationName : schema
- Address : host
- Comment : extra
- Content : password
- LogonDomain : login
- Port : port

> AccountDescription : svc_account field is used to fetch password from
> rotating secret where the fetched secret is static, i.e. if you fetch `secret1`
> which is static, if you specify the CCP URL for `secret2` which rotates it will
> fetch metadata for `secret1` and fill in password from `secret2` in its response

## Development
PRs welcomed.

The following will install in editable mode with all required development tools.
```bash
git clone https://github.com/jkornblum/airflow-cyberark-secrets-backend.git
cd airflow-cyberark-secrets-backend
pip install -e '.[dev]'
```

Please format (`black`) and lint (`pylint`) before submitting PR.