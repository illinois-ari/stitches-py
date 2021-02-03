import json
import logging
import requests

from .fields import Field
from .repo import FTGPatch, FTGFieldAddition, FTGField, FTGPatchRequest

class FTGRepoClient:
    """
    Client for interacting with the FTGRepo via HTTP
    """
    def __init__(self, *, repo_url='http://localhost:4567'):
        self._logger = logging.getLogger()
        self._repo_url = repo_url


    def register_field(self, field: Field) -> bool:
        patch = FTGPatch()
        patch.field_additions.append(FTGFieldAddition(fieldType=FTGField.from_resource(field)))

        return self.apply_patch(patch)

    def apply_patch(self, patch: FTGPatch) -> bool:
        """
        Apply an FTG Patch to the repo.
        """
        req = FTGPatchRequest(patch=patch)
        req_body = req.json(by_alias=True)
        
        self._logger.error(req_body)

        response = requests.post(
            f'{self._repo_url}/applyPatch',
            data=req_body,
            headers={'content-type': 'application/json'}
        )
        if response.status_code != 200:
            self._logger.error(f'Received response {response.status} from FTGRepo')
            return False

        try:
            resp_obj = response.json()
            self._logger.error(resp_obj)
            return resp_obj.get('Success', False)
        except Exception as e:
            self._logger.error(f'Error loading json response {resp_txt}', exc_info=True)
            return False