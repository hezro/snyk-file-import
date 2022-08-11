#!/usr/bin/env python3

import sys
import httpx
import json
from loguru import logger

# Read configuration file: .conf
def parse_config() -> dict:
    conf = {}
    with open(CONFIG_FILE, "r") as file:
        for line in file:
            if "=" in line:
                key, value = line.strip().split("=")
                conf[key] = value
    return conf

# Import file
def import_file(dest_org_id: str, integrationId: str, repo_owner: str, repo_name: str, branch_name: str, file_path: str):
    try:
        logger.info(f"Importing file: {file_path} | Branch: {branch_name} | Repo: {repo_name} | Repo Owner: {repo_owner}")
        data = json.dumps( 
            {
                "target": {"owner": repo_owner, "name": repo_name, "branch": branch_name},
                "files": [{"path": file_path}],
            }
        )
        client_headers = { 
          "Content-Type": "application/json; charset=utf-8",
          "Authorization": f"token {SNYK_TOKEN}",
        }
        
        with httpx.Client(base_url=BASE_URL, headers=client_headers) as client:
            client.event_hooks={'request': [print_request], 'response': [print_response]}
            r = client.post(f"/org/{dest_org_id}/integrations/{integrationId}/import", data=data)
            r.raise_for_status()
            if r.status_code == 201: logger.success(f"{file_path} was imported successfully.")            
         
    except httpx.NetworkError as ex:
        logger.error(f"Network error occurred: {ex.request!r}.")
        logger.error(f"Exception: {ex}")
    except httpx.TransportError as ex:
        logger.error(f"Transport error occurred: {ex.request!r}.")
        logger.error(f"Exception: {ex}")
    except httpx.HTTPError as ex:
            logger.error(f"HTTPError: {ex.response.status_code} While requesting {ex.request.url!r} .")
            logger.error(f"Exception: {ex}")
    except Exception as ex:
            logger.error(f"Exception: {ex}")

def print_request(request):
    logger.info(f"Request: {request.method} {request.url} - Waiting for response")

def print_response(response):
    r = response.request
    logger.info(f"Response: {r.method} {r.url} - Status: {response.status_code}")

# Setup Logging
logger.remove(0)
logformat = (   
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{function}</cyan>:<red>{line}</red> - <level>{message}</level>"
)
logger.add(sys.stderr, format=logformat)
logger.level("INFO", color="<yellow>")

# Pull in key/value pairs from the config file
CONFIG_FILE = '.conf'
CONFIG = parse_config()
SNYK_TOKEN = CONFIG["SNYK_TOKEN"]
BASE_URL = CONFIG["BASE_API_URL"]

# Main function
@logger.catch
def main() -> None:
    dest_org_id = CONFIG["DEST_ORG_ID"]
    integration_id = CONFIG["INTEGRATION_ID"]
    repo_owner = CONFIG["REPO_OWNER"]
    repo_name = CONFIG["REPO_NAME"]
    branch_name = CONFIG["BRANCH_NAME"]
    file_path = CONFIG["FILE_PATH"]
   
    if CONFIG["LOGFILE"].lower().strip() == "true": logger.add('snyk_file_import_{time}.log')

    import_file(dest_org_id, integration_id, repo_owner, repo_name, branch_name, file_path)

if __name__ == "__main__":
    main()
