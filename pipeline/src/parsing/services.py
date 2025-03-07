import json
import io
from pathlib import Path
from enum import Enum
from typing import Any
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from tqdm import tqdm
from pydantic import AnyHttpUrl
import ee
import google.auth
import geemap

from src.parsing.constants import EgisticSubDomain


class BaseService:
    def __init__(self, domain: str) -> None:
        self._prefix = "https"
        self._subdomain = ""
        self._domain = domain
        self.base_url = self._build_base_url()
    
    def _build_base_url(self, subdomain: str | None = "") -> str:
        base_url = AnyHttpUrl.build(scheme=self._prefix, host=f"{subdomain}{self._domain}").unicode_string()
        return base_url

    def _set_subdomain(self, subdomain: Enum) -> None:
        self._subdomain = subdomain.value
        self.base_url = self._build_base_url(subdomain=f"{self._subdomain}.")


class EgisticService(BaseService):
    def __init__(
        self,
        domain: str,
        client: httpx.Client,
        base_directory: Path,
        credentials: dict[str, Any],
    ) -> None:
        super().__init__(domain=domain)
        self.client = client
        self.credentials = credentials
        self.base_directory = base_directory
    
    def _get_access_token(self, username: str, password: str) -> str:
        self._set_subdomain(subdomain=EgisticSubDomain.CABINET)
        response = self.client.post(
            url=self.base_url + "api/v1/signin/new/",
            data={"username": username, "password": password},
        )
        if response and response.is_success:
            response_data = response.json()
            token = response_data.get("token")
        else:
            token = None
        return token
    
    def get_map_layers(self):
        self._set_subdomain(subdomain=EgisticSubDomain.GEO)
        sub_directory = "data/parsing/egistic/layers"
        directory = self.base_directory / sub_directory
        directory.mkdir(parents=True, exist_ok=True)
        layers = [
            {
                "title": "15",
                "filter": "&bbox=7647267.869542876%2C6764043.948365914%2C7697978.538731981%2C6814664.154490127&width=768&height=766",
            },
            {
                "title": "agrogis_farminfo",
                "filter": "&bbox=5177527.5%2C4948971.0%2C9712419.0%2C7447898.5&width=768&height=423",
            },
            {
                "title": "agrogis_farminfo_new",
                "filter": "&bbox=5177527.5%2C4948989.0%2C9712323.0%2C7447898.5&width=768&height=423",
            },
            {
                "title": "cadastres_bingeometry",
                "filter": "&bbox=5180213.5%2C4966549.0%2C9650294.0%2C7447880.5&width=768&height=426",
            },
            {
                "title": "cadastres_farmgisinfo",
                "filter": "&bbox=5180213.5%2C4966549.0%2C9650294.0%2C7447880.5&width=768&height=426",
            },
        ]
        for layer in tqdm(layers, desc="fetching layers"):
            title = layer.get("title")
            filter = layer.get("filter")
            url = self.base_url + f"geoserver/main/wms?service=WMS&version=1.1.0&request=GetMap&layers=main%3A{title}{filter}&srs=EPSG%3A3857&styles=&format=geojson"
            file_path = directory / f"{title}.json"
            with self.client.stream("GET", url=url) as response:
                if response and response.is_success:
                    with file_path.open("wb") as file:
                        for chunk in tqdm(response.iter_bytes(chunk_size=1024 * 8), desc="saving chunks"):
                            file.write(chunk)
    
    def get_farms_metadata(self):
        self._set_subdomain(subdomain=EgisticSubDomain.CABINET)
        access_token = self._get_access_token(self.credentials["username"], self.credentials["password"])
        identifiers = []
        sub_directory = "data/parsing/egistic/farms"
        directory = self.base_directory / sub_directory
        directory.mkdir(parents=True, exist_ok=True)
        layers_directory = self.base_directory / "data/parsing/egistic/layers"
        layers = list(layers_directory.glob("agrogis_farminfo_new.json"))
        for layer in layers:
            with layer.open("r") as file:
                data = json.load(file)
                features = data.get("features")
                for feature in features:
                    id_hash = feature.get("id")
                    identifiers.append(id_hash)
        
        def get_by_identifier(self, identifier: str):
            identifier = identifier.replace("agrogis_farminfo_new.", "")
            response = self.client.get(
                url=self.base_url + f"api/v1/agrogis/farm/{identifier}/full-info/",
                headers={"authorization": f"Token {access_token}"}
            )
            if response and response.is_success:
                response_data = response.json()
                file_path = directory / f"{identifier}.json"
                with file_path.open("w") as file:
                    file.write(json.dumps(response_data, ensure_ascii=False, indent=4))
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(get_by_identifier, self, identifier)
                for identifier in identifiers
            ]
            for future in tqdm(as_completed(futures), total=len(identifiers), desc="fetching farms metadata"):
                try:
                    data = future.result()
                except Exception as exc:
                    print(exc)
    
    def filter_and_aggregate_metadata(self):
        farms_directory = self.base_directory / "data/parsing/egistic/farms"
        layers_directory = self.base_directory / "data/parsing/egistic/layers"  
        farms = list(farms_directory.glob("*.json"))
        layers = list(layers_directory.glob("*.json"))
        for farm in farms:
            with farm.open("r") as file:
                data = json.load(file)
            occupation = data.get("occupation")
            cultures = data.get("cultures")
            if occupation or cultures:
                # save only them by id
                # combine farm metadata to layer features
                # save as aggregated jsons -> later convert, compress, combine with others vectors
                ...
    
    
class Gov4cService(BaseService):
    def __init__(
        self,
        domain: str,
        client: httpx.Client,
        base_directory: Path,
        credentials: dict[str, Any],
    ) -> None:
        super().__init__(domain=domain)
        self.client = client
        self.credentials = credentials
        self.base_directory = base_directory

    def authenticate(self):
        ...
    
    def get_layers_metadata(self):
        # WFS capabilities lists layers - requests for vector data
        layers_metadata = []
        geoserver_metadata = self.client.get(
            self.base_url
            + "/geoserver/ows?service=WFS&version=1.0.0&request=GetCapabilities"
        ).text
        root = ET.fromstring(geoserver_metadata)
        feature_type_list = root.find("{http://www.opengis.net/wfs}FeatureTypeList")
        raw_layers_metadata = feature_type_list.findall(
            "{http://www.opengis.net/wfs}FeatureType"
        )
        for metadata in raw_layers_metadata:
            layers_metadata.append(
                {
                    "name": metadata[0].text,
                    "title": metadata[1].text,
                    "srs": metadata[4].text,
                    "bbox": metadata[5].attrib,
                }
            )
        return layers_metadata

    # the WMS capabilities lists layers that support requests for tiled images
    # the WCS capabilities lists layers that support raster queries
    def get_coverage(self):
        # https://map.gov4c.kz/geoserver/ows?service=WCS&version=2.0.1&request=GetCoverage&coverageId=egkn__maxar_raster_tiles&format=image/tiff
        ...


class EarthEngineService(BaseService):
    pass
