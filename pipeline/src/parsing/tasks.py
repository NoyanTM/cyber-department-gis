from src.parsing.services import EgisticService, Gov4cService


def run_egistic_tasks(egistic_service: EgisticService):
    egistic_service.get_map_layers()
    egistic_service.get_farms_metadata()
    egistic_service.filter_and_aggregate_metadata()
    
    
def run_gov4c_tasks(gov4c_service: EgisticService):
    pass
