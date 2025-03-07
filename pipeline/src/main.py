import httpx

from src.common.config import load_config, BASE_DIR
from src.parsing.constants import EGISTIC_DOMAIN
from src.parsing.services import EgisticService, Gov4cService
from src.parsing.tasks import run_egistic_tasks, run_gov4c_tasks


def main():
    config = load_config()
    
    with httpx.Client(timeout=None, verify=False) as client:
        egistic_service = EgisticService(
            domain=EGISTIC_DOMAIN,
            client=client,
            base_directory=BASE_DIR,
            credentials={
                "username": config.EGISTIC_CLIENT_USERNAME,
                "password": config.EGISTIC_CLIENT_PASSWORD
            }
        )
        # gov4c_service = Gov4cService(...)
        run_egistic_tasks(egistic_service)
        # run_gov4c_tasks(gov4c_service)
        
        
        
if __name__ == "__main__":
    main()
    