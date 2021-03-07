import os
from typing import Dict, Optional, Union

from airflow.models.connection import Connection
from airflow.secrets import BaseSecretsBackend
from airflow.utils.log.logging_mixin import LoggingMixin

import requests


__version__ = "0.1.0"


class CyberArkSecretsBackend(BaseSecretsBackend, LoggingMixin):
    """
    Class for Airflow Secrets Backend Connection to CyberArk
    """

    def __init__(
        self,
        app_id: str,
        ccp_url: str,
        safe: str,
        verify: Optional[Union[str, bool]] = None,
        **kwargs,
    ):
        """

        Args:
            app_id: The CyberArk Central Credential Provider AppId
            ccp__url: The Cyber CCP URL base (excluding query params)
            safe: The CyberArk safe
            verify: path to ssl certificate or False to disable verification
                if None will look for env var CYBERARK_SSL, if not found will disable (False)
        """
        super(CyberArkSecretsBackend, self).__init__(**kwargs)
        self.app_id = app_id
        self.ccp_url = ccp_url
        self.safe = safe
        self._verify = verify

        if self.ccp_url[-1] == "?":
            self.ccp_url = self.ccp_url[:-1]

        if self._verify is None:
            if "CYBERARK_SSL" in os.environ:
                self._verify = os.environ["CYBERARK_SSL"]
            else:
                self._verify = False

    def _fetch_cyberark(self, ca_obj: str) -> dict:
        """
        Fetch the secret from CyberArk

        Args:
            ca_obj: The CyberArk object name

        Returns:
            dict: The connection dictionary
        """
        ca_map = {
            "AccountDescription": "svc_account",
            "ApplicationName": "schema",
            "Address": "host",
            "Comment": "extra",
            "Content": "password",
            "LogonDomain": "login",
            "Port": "port",
        }

        url = f"{self.ccp_url}?AppID={self.app_id}&Safe={self.safe}&Object={ca_obj}"
        response = requests.get(url, verify=self._verify)
        response = response.json()
        ca_content: Dict[str, Union[int, str]] = {
            ca_map[ca_key]: str(response[ca_key])
            for ca_key in ca_map
            if ca_key in response
        }

        if "port" in ca_content:
            ca_content["port"] = int(ca_content["port"])

        # if the airflow connection is using a svc_account with auto-rotate
        # managed by CyberArk then fetch the fresh credential
        if "svc_account" in ca_content:
            ca_content["password"] = str(
                self._fetch_cyberark(str(ca_content["svc_account"]))["password"]
            )
            del ca_content["svc_account"]

        return ca_content

    def get_connections(self, conn_id: str) -> Optional[Connection]:
        """
        Get connections with a specific ID

        Args:
            conn_id: The Airflow connection id, the CyberArk object name

        Returns:
            airflow.models.connection.Connection
        """
        conn_dict = self._fetch_cyberark(ca_obj=conn_id)
        if conn_dict:
            conn = Connection(conn_id=conn_id, **conn_dict)

            return [conn]

        return None

    def get_variable(self, key: str) -> Optional[str]:
        """Return Variable value from CyberArk. This will be str of secret content.

        Arg:
            key: The variable key, the cyberark object name

        Returns:
            str of the CyberArk secret content
        """
        conn_dict = self._fetch_cyberark(ca_obj=key)
        if conn_dict:
            return conn_dict["password"]

        return None
