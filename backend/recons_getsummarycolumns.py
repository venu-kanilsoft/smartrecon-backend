from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/getSummaryColumns', tags=['Recons'])
async def ReconsgetSummaryColumns(data: getSummaryColumnsParams):
    sc = [{'op': 'matched', 'key': 'Matched Count', 'displayname': 'Matched',
               'allowedop': [{'key': 'rollback_matched_records', 'displayname': 'Roll Back'}]},
              {'op': 'unmatched', 'key': 'UnMatched Count', 'displayname': 'UnMatched',
               'allowedop': [{'key': 'force_match_records', 'displayname': 'Force Match'}]},
              {'op': 'authwaiting', 'key': 'Auth Waiting', 'displayname': 'Auth Waiting',
               'allowedop': [{'key': 'authorize_force_match_records', 'displayname': 'Authorize'},
                             {'key': 'reject_force_match_records', 'displayname': 'Reject'}]},
              {'op': 'rollbackwaiting', 'key': 'Rollback Waiting', 'displayname': 'Rollback Waiting',
               'allowedop': [{'key': 'authorize_rollback_records', 'displayname': 'Authorize'},
                             {'key': 'reject_rollback_records', 'displayname': 'Reject'}]},
              {'op': 'reversal', 'key': 'Reversal Count', 'displayname': 'Reversal',
               'allowedop': [{'key': 'rollback_matched_records', 'displayname': 'Roll Back'}]},
              {'op': 'carry-forwardmatched', 'key': 'Carry-Forward Matched Count', 'displayname': 'Carry-Forward Matched',
               'allowedop': [{'key': 'rollback_matched_records', 'displayname': 'Roll Back'}]},
              {'op': 'carry-forwardunmatched', 'key': 'Carry-Forward UnMatched Count', 'displayname': 'Carry-Forward UnMatched',
               'allowedop': [{'key': 'force_match_records', 'displayname': 'Force Match'}]}]
        
    return {"status": True, "message": "Success", "data":sc}
