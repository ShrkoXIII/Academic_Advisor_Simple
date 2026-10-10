"""Regression tests for evidence authentication and truthful completion."""
import json
import pytest
from scripts.experiments.student_progress_20261010.safeguards import (
    sign_record, authenticate_record, publish_completion,
)


def test_tuning_record_rejects_changed_rounds_and_unsigned_cache():
    value=sign_record({'selected':{'rounds':114,'features':['a','b']}})
    assert authenticate_record(value)['selected']['rounds']==114
    changed=json.loads(json.dumps(value))
    changed['selected']['rounds']=115
    with pytest.raises(ValueError,match='integrity'):
        authenticate_record(changed)
    with pytest.raises(ValueError,match='unsigned'):
        authenticate_record({'selected':{'rounds':114}})


def test_failure_to_verify_cannot_leave_complete(tmp_path):
    path=tmp_path/'execution.json'
    path.write_text(json.dumps({'status':'COMPLETE'}))
    def fail():
        raise ValueError('Protected source changed')
    with pytest.raises(ValueError,match='Protected'):
        publish_completion(path,{'fits':108},fail)
    assert json.loads(path.read_text())['status']=='FAILED'


def test_complete_is_published_only_after_verification(tmp_path):
    path=tmp_path/'execution.json'
    seen=[]
    def verify():
        assert not path.exists()
        seen.append('verified')
        return {'changed':[]}
    publish_completion(path,{'fits':108},verify)
    assert seen==['verified']
    assert json.loads(path.read_text())=={'status':'COMPLETE','fits':108,'isolation':{'changed':[]}}


def test_tuning_selection_accepts_only_matching_context():
    from scripts.experiments.student_progress_20261010.safeguards import authenticate_selection
    context={'run':'run-a','year':2023,'spec':{'name':'47_grade'},
             'fit_rows':'fit-a','validation_rows':'validation-a'}
    selected={'parameters':{'num_leaves':31},'rounds':114}
    assert authenticate_selection(sign_record({'context':context,'selected':selected}),context)==selected


@pytest.mark.parametrize('key,replacement',[
    ('run','run-b'),('year',2024),('spec',{'name':'33_grade'}),
    ('fit_rows','fit-b'),('validation_rows','validation-b'),
])
def test_signed_tuning_selection_cannot_be_transplanted(key,replacement):
    from scripts.experiments.student_progress_20261010.safeguards import authenticate_selection
    original={'run':'run-a','year':2023,'spec':{'name':'47_grade'},
              'fit_rows':'fit-a','validation_rows':'validation-a'}
    record=sign_record({'context':original,'selected':{'rounds':114}})
    expected={**original,key:replacement}
    with pytest.raises(ValueError,match='context'):
        authenticate_selection(record,expected)
